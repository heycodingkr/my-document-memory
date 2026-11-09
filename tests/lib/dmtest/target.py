"""The system under test: the double (default) or a real product, reached only through its CLI and stdio MCP binaries.

Environment (tests/README.md): DMEM_TARGET=double|product, DMEM_BIN, DMEM_MCP_BIN, DMEM_SERVER_CMD, DMEM_PROFILE=full|runtime-v1.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from .cli import Cli
from .mcpclient import McpSession
from .procs import Owned, free_port, isolated_env, short_tmp

ROOT = Path(__file__).resolve().parents[3]
DOUBLE_DIR = ROOT / "tests" / "env" / "dmem-double"


class TargetError(RuntimeError):
    pass


class Skip(Exception):
    """Raised to skip a case explicitly; the reason is mandatory and ends up in the evidence."""


class Target:
    def __init__(self, kind, cli_cmd, mcp_cmd, profile, server_cmd=None):
        self.kind, self.cli_cmd, self.mcp_cmd, self.profile, self.server_cmd = kind, cli_cmd, mcp_cmd, profile, server_cmd

    @property
    def is_double(self):
        return self.kind == "double"

    @classmethod
    def from_env(cls, env=None):
        env = os.environ if env is None else env
        kind = env.get("DMEM_TARGET", "double")
        profile = env.get("DMEM_PROFILE", "full")
        if profile not in ("full", "runtime-v1"):
            raise TargetError("DMEM_PROFILE must be full or runtime-v1")
        if kind == "double":
            return cls("double", [sys.executable, "-B", str(DOUBLE_DIR / "dmem")], [sys.executable, "-B", str(DOUBLE_DIR / "dmem-mcp")], profile)
        if kind == "product":
            cli, mcp = env.get("DMEM_BIN"), env.get("DMEM_MCP_BIN")
            if not cli or not mcp:
                raise TargetError("DMEM_TARGET=product needs DMEM_BIN and DMEM_MCP_BIN (absolute paths)")
            for path in (cli, mcp):
                if not os.path.isabs(path) or not os.access(path, os.X_OK):
                    raise TargetError("DMEM_BIN and DMEM_MCP_BIN must be absolute paths of executables")
            return cls("product", [cli], [mcp], profile, env.get("DMEM_SERVER_CMD"))
        raise TargetError("DMEM_TARGET must be double or product")

    def sandbox(self, server=False):
        return Sandbox(self, short_tmp(), server)


class Sandbox:
    """One disposable world per case: per-identity HOME/DMEM_HOME, one shared server state, one request log."""

    def __init__(self, target, tmp, server=False):
        self.target, self.tmp, self.server = target, Path(tmp), server
        self.server_state = self.tmp / "server.json" if (server and target.is_double) else None
        self.request_log_path = self.tmp / "requests.jsonl"
        self.extra_env = {}
        self._sessions, self._cli, self._server_proc = [], {}, None
        self.endpoint = self.token = None

    # -- environment
    def home(self, identity="local"):
        return self.tmp / identity / "dmem"

    def env_for(self, identity="local", extra=None):
        base = self.tmp / identity
        env = isolated_env(base, DMEM_HOME=str(self.home(identity)), DMEM_ISOLATED="1")
        if self.target.is_double:
            env.update({"DMEM_DOUBLE_TEST_HOOKS": "1", "DMEM_TEST_IDENTITY": identity, "DMEM_TEST_REQUEST_LOG": str(self.request_log_path)})
            if self.server_state:
                env["DMEM_TEST_SERVER_STATE"] = str(self.server_state)
            for key in ("DMEM_DOUBLE_MUTATION", "DMEM_TEST_RESOLVE", "DMEM_TEST_CLOCK_OFFSET", "DMEM_TEST_SERVER_DOWN"):
                if key in os.environ:
                    env[key] = os.environ[key]
        elif self.endpoint:
            env.update({"DMEM_ENDPOINT": self.endpoint, "DMEM_TOKEN": self.token})
        env.update(self.extra_env)
        env.update(extra or {})
        return env

    def cli(self, identity="local", extra_env=None):
        key = (identity, tuple(sorted((extra_env or {}).items())))
        if key not in self._cli:
            self._cli[key] = Cli(self.target.cli_cmd, self.env_for(identity, extra_env), cwd=str(self.tmp / identity / "home"))
        return self._cli[key]

    def mcp(self, identity="local", extra_env=None):
        session = McpSession(self.target.mcp_cmd, self.env_for(identity, extra_env))
        self._sessions.append(session)
        return session

    def request_log(self):
        if not self.request_log_path.exists():
            return []
        return [json.loads(line) for line in self.request_log_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    # -- fixtures
    def load_library(self, path, identity="local", owner_map=None):
        """Load a fixture file into the double's store (test hook). Products have no such hook: the case is skipped with a reason."""
        if not self.target.is_double:
            raise Skip("fixture loading needs the double's test hook (no public CLI equivalent yet)")
        args = ["__test", "load-fixture", str(path)] + [f"{k}={v}" for k, v in (owner_map or {}).items()]
        result = self.cli(identity).run(args)
        if result.exit != 0:
            raise TargetError("fixture load failed")
        return result.json

    def start_server(self):
        """Product only: start DMEM_SERVER_CMD on a free loopback port with a disposable data dir."""
        if self.target.is_double:
            return None
        if not self.target.server_cmd:
            raise Skip("no DMEM_SERVER_CMD configured for this product")
        port, token = free_port(), "dmem-test-" + os.urandom(6).hex()
        data = self.tmp / "server-data"
        data.mkdir(parents=True, exist_ok=True)
        cmd = self.target.server_cmd.format(port=port, data_dir=data, token=token).split()
        self._server_proc = Owned(cmd, isolated_env(self.tmp / "server", DMEM_TOKEN=token)).start()
        self.endpoint, self.token = f"http://127.0.0.1:{port}", token
        for _ in range(80):
            try:
                urllib.request.urlopen(self.endpoint + "/healthz", timeout=0.5).read()
                return self.endpoint
            except Exception:
                time.sleep(0.25)
        raise TargetError("server did not become healthy")

    # -- the eight sinks of the sentinel sweep (docs/test/security-scenarios.md, HARN-14)
    SINKS = ("client_output", "logs_diagnostics", "local_store", "cache", "server_requests", "remote_requests", "process_args_env", "exported_files")

    def sweep_sources(self, identities, fixture_log=None):
        """{sink: [sources]} where a source is a Path or bytes. `local_store_originals` is separate: preserved uploads legitimately hold the user's own personal data."""
        sinks = {name: [] for name in self.SINKS}
        sinks["local_store_originals"] = []
        sinks["client_output"] += [out + b"\n" + err for cli in self._cli.values() for out, err in cli.transcript]
        sinks["client_output"] += [bytes(s.raw_out) + b"\n" + bytes(s.raw_err) for s in self._sessions]
        for who in identities:
            root = self.tmp / who
            home = self.home(who)
            log_dirs = [home / n for n in ("log", "logs", "diagnostics", "telemetry", "spool")] + [root / "tmp", root / "data", root / "config"]
            sinks["logs_diagnostics"] += [p for p in log_dirs if p.exists()] + [p for p in home.glob("*.log")] + [p for p in home.glob("*.jsonl")]
            sinks["logs_diagnostics"].append(("listing of " + who + ":\n" + "\n".join(sorted(str(f.relative_to(root)) for f in root.rglob("*") if f.is_file()))).encode())
            if home.exists():
                own = ("originals", "cache", "log", "logs", "diagnostics", "telemetry", "spool")  # the other sinks' directories: keep the eight sinks disjoint
                sinks["local_store"] += [c for c in home.iterdir() if c.name not in own and not c.name.endswith((".log", ".jsonl"))]
                if (home / "originals").exists():
                    sinks["local_store_originals"].append(home / "originals")
            sinks["cache"] += [p for p in (root / "cache", home / "cache") if p.exists()]
            sinks["exported_files"] += [c for c in root.iterdir() if c.is_file()] + ([root / "home"] if (root / "home").exists() else [])
        if self.request_log_path.exists():
            sinks["server_requests"].append(self.request_log_path)
        if self.server_state and self.server_state.exists():
            sinks["server_requests"].append(self.server_state)
        if fixture_log is not None:  # None: no fixture server was started, so there is no log to look at (reported as an empty sink)
            sinks["remote_requests"].append(json.dumps(fixture_log, ensure_ascii=False).encode())
        calls = [{"args": a, "exit": e} for cli in self._cli.values() for a, e in cli.calls]
        envs = [dict(cli.env) for cli in self._cli.values()] + [dict(s.env) for s in self._sessions]
        sinks["process_args_env"].append(json.dumps({"calls": calls, "env": envs}, ensure_ascii=False).encode())
        return sinks

    def close(self):
        for s in self._sessions:
            try:
                s.close()
            except Exception:
                pass
        if self._server_proc:
            self._server_proc.stop()
        subprocess.run(["rm", "-rf", str(self.tmp)], check=False)
