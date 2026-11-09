"""Owned processes, isolated environments and leak checks (HARN-05, HARN-15). Only processes this run started are ever signalled."""
import os
import shutil
import signal
import socket
import subprocess
import tempfile
import time
from pathlib import Path


def short_tmp(prefix="dmem-"):
    """A short temp directory (macOS unix-socket paths are length limited)."""
    return Path(tempfile.mkdtemp(prefix=prefix, dir="/tmp"))


def isolated_env(tmp, **extra):
    """Environment for a child: disposable HOME/XDG/TMPDIR. Nothing from the user's real profile is inherited except PATH/LANG."""
    tmp = Path(tmp)
    env = {k: os.environ[k] for k in ("PATH", "LANG", "LC_ALL", "PYTHONUTF8") if k in os.environ}
    for d in ("home", "config", "cache", "data", "tmp"):
        (tmp / d).mkdir(parents=True, exist_ok=True)
    env.update({"HOME": str(tmp / "home"), "XDG_CONFIG_HOME": str(tmp / "config"), "XDG_CACHE_HOME": str(tmp / "cache"),
                "XDG_DATA_HOME": str(tmp / "data"), "TMPDIR": str(tmp / "tmp"), "TMP": str(tmp / "tmp"), "TEMP": str(tmp / "tmp"),
                "DMEM_TELEMETRY": "off", "PYTHONDONTWRITEBYTECODE": "1", "NO_COLOR": "1"})
    env.update({k: str(v) for k, v in extra.items() if v is not None})
    return env


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Owned:
    """A child in its own process group. stop() terminates only that group."""

    def __init__(self, cmd, env, cwd=None, stdin=subprocess.PIPE):
        self.cmd, self.env, self.cwd, self.stdin_mode = cmd, env, cwd, stdin
        self.p = None

    def start(self):
        self.p = subprocess.Popen(self.cmd, env=self.env, cwd=self.cwd, stdin=self.stdin_mode, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  start_new_session=True)
        return self

    def alive(self):
        return self.p is not None and self.p.poll() is None

    def stop(self, timeout=3.0):
        if self.p is None:
            return
        if self.p.poll() is None:
            for sig, wait in ((signal.SIGTERM, timeout), (signal.SIGKILL, 2.0)):
                try:
                    os.killpg(self.p.pid, sig)
                except ProcessLookupError:
                    break
                try:
                    self.p.wait(timeout=wait)
                    break
                except subprocess.TimeoutExpired:
                    continue
        for stream in (self.p.stdin, self.p.stdout, self.p.stderr):
            try:
                stream and stream.close()
            except Exception:
                pass


def run_with_timeout(cmd, env, stdin=None, timeout=30.0, cwd=None):
    """Run to completion in its own group; on timeout kill the group and report exit=None (HARN-15)."""
    p = subprocess.Popen(cmd, env=env, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    started = time.monotonic()
    try:
        out, err = p.communicate(input=stdin, timeout=timeout)
        return p.returncode, out, err, time.monotonic() - started
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        out, err = p.communicate()
        return None, out or b"", err or b"", time.monotonic() - started


def leftover_check(before, after):
    """Return the pids that appeared and are still alive (the harness must leave none behind)."""
    return sorted(set(after) - set(before))


def cleanup(path):
    shutil.rmtree(path, ignore_errors=True)
