"""Case registry and runner. Cases are black-box functions over `Ctx`; ids come from docs/test only (HARN-10).

    @case("CORE-02", profile="R1", needs=())
    def core_02(ctx):
        r = ctx.cli().json(["recall", "http://example.com/a"])
        ctx.expect(r.exit == 2 and r.code == "url_rejected", "http is rejected")

`profile`: R1 | F | L0 (docs/test/README.md section 2). `needs`: server (shared server state or DMEM_SERVER_CMD), hooks (double test hooks),
fixtures (loopback fixture web server). A case that cannot run is SKIPped with a reason; a skip is never silent.
"""
import fnmatch
import json
import os
import sys
import threading
import time
import traceback

from . import sentinels as sentinel_lib
from .evidence import RunDir
from .fixture_http import FixtureServer
from .schema import ContractStore, validate
from .target import Skip, Target

REGISTRY = {}
PROFILES = ("R1", "F", "L0")
CASE_TIMEOUT = float(os.environ.get("DMEM_CASE_TIMEOUT", "90"))


def case(case_id, profile="R1", layer="L2", needs=()):
    def wrap(fn):
        if case_id in REGISTRY:
            raise ValueError(f"duplicate case id {case_id}")
        if profile not in PROFILES:
            raise ValueError("bad profile")
        REGISTRY[case_id] = {"id": case_id, "fn": fn, "profile": profile, "layer": layer, "needs": tuple(needs), "module": fn.__module__}
        return fn
    return wrap


class Ctx:
    def __init__(self, target, sandbox, fixtures, store, sentinels):
        self.target, self.sandbox, self._fixtures, self.store, self.sentinels = target, sandbox, fixtures, store, sentinels
        self.failures = []
        self.cli_used = []
        self.checks = 0

    # -- verdicts
    def expect(self, condition, message):
        self.checks += 1
        if not condition:
            self.failures.append(message)
        return bool(condition)

    def skip(self, reason):
        raise Skip(reason)

    # -- target access
    @property
    def profile(self):
        return self.target.profile

    @property
    def is_double(self):
        return self.target.is_double

    def cli(self, identity="local", extra_env=None):
        return self.sandbox.cli(identity, extra_env)

    def mcp(self, identity="local", extra_env=None, initialize=True):
        session = self.sandbox.mcp(identity, extra_env)
        if initialize:
            session.initialize()
        return session

    def home(self, identity="local"):
        return self.sandbox.home(identity)

    def request_log(self):
        return self.sandbox.request_log()

    # -- fixtures
    @property
    def fx_url(self):
        return self._fixtures.base_url

    def fx_log(self):
        return self._fixtures.log()

    def search_provider(self, spec):
        """spec 'none' | 'fixture' (loopback fixture /search) | raw provider string."""
        self.sandbox.extra_env["DMEM_SEARCH_PROVIDER"] = f"fixture:{self.fx_url}/search" if spec == "fixture" else spec

    def load_library(self, name, identity="local", owner_map=None):
        path = self.store.base.parent / "tests" / "fixtures" / f"{name}.json"
        return self.sandbox.load_library(path, identity, owner_map or {"local": identity})

    # -- checks
    def schema_ok(self, instance, tool_or_ref, label=""):
        schema = self.store.result_schema(tool_or_ref) if isinstance(tool_or_ref, str) and tool_or_ref.startswith("doc_memory_") else tool_or_ref
        errors = validate(instance, schema, self.store)
        self.expect(not errors, f"schema {label or tool_or_ref}: {errors[:3]}")
        return not errors

    def scan_sinks(self, identities=("local",), extra=(), families=None, server=True):
        """Scan every client-side sink for sentinels; returns findings (ids only). Never prints values.

        `server=False` leaves the shared server state out: it legitimately holds its owners' private data, so only cases about what the server must not
        have received (or must not store at all) scan it."""
        paths = [self.sandbox.request_log_path] if self.sandbox.request_log_path.exists() else []
        for who in identities:
            paths.append(self.sandbox.tmp / who)
        if server and self.sandbox.server_state and self.sandbox.server_state.exists():
            paths.append(self.sandbox.server_state)
        paths += list(extra)
        return sentinel_lib.scan(paths, self.sentinels, families)


    def scan_values(self, values, identities=("local",), extra=()):
        """Like scan_sinks for ad-hoc literals (e.g. a capability id). Returns findings (ids only)."""
        data = sentinel_lib.Sentinels({"items": [{"id": f"adhoc-{i}", "family": "adhoc", "value": v} for i, v in enumerate(values, 1)]})
        paths = [self.sandbox.request_log_path] if self.sandbox.request_log_path.exists() else []
        paths += [self.sandbox.tmp / who for who in identities]
        if self.sandbox.server_state and self.sandbox.server_state.exists():
            paths.append(self.sandbox.server_state)
        return sentinel_lib.scan(paths + list(extra), data)


def select(ids, suite):
    chosen = []
    patterns = [p.strip() for p in ids.split(",")] if ids else []
    for cid in sorted(REGISTRY):
        if patterns and not any(fnmatch.fnmatch(cid, p) for p in patterns):
            continue
        is_smoke = cid.startswith("SMK-")
        if suite == "smoke" and not (is_smoke or cid.startswith(("CLI-04", "SNIP"))):
            continue
        if suite == "contract" and is_smoke:
            continue
        chosen.append(REGISTRY[cid])
    return chosen


def run(ids="", profile=None, suite="all", strict=False, out=None, quiet=False):
    import pkgutil
    from importlib import import_module
    cases_pkg = import_module("cases")
    for info in sorted(pkgutil.iter_modules(cases_pkg.__path__), key=lambda i: i.name):
        if info.name != "util":
            import_module(f"cases.{info.name}")
    target = Target.from_env()
    if profile:
        target.profile = profile
    run_dir = RunDir("smoke" if suite == "smoke" else "contract", base=out)
    run_dir.write_meta({"target": target.kind, "profile": target.profile, "suite": suite, "python": sys.version.split()[0], "platform": sys.platform,
                        "mutation": __import__("os").environ.get("DMEM_DOUBLE_MUTATION", ""), "started": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
    store = ContractStore()
    sentinels = sentinel_lib.load()
    chosen = select(ids, suite)
    fixtures = None
    results = []
    try:
        if any("fixtures" in c["needs"] or c["id"].startswith(("IMP", "DISC", "SMK")) for c in chosen):
            fixtures = FixtureServer(str(run_dir.path / "fixture"))
            fixtures.start()
        for entry in chosen:
            started = time.monotonic()
            verdict, reason = _run_one(entry, target, fixtures, store, sentinels, strict)
            run_dir.case(entry["id"], verdict, reason=reason, profile=entry["profile"], seconds=round(time.monotonic() - started, 2))
            results.append((entry["id"], verdict, reason))
            if not quiet:
                mark = {"PASS": "  ok ", "FAIL": " FAIL", "SKIP": " skip"}[verdict.split("(")[0]]
                print(f"{mark} {entry['id']:<8} {reason if verdict != 'PASS' else ''}")
    finally:
        if fixtures:
            fixtures.stop()
    counts = run_dir.write_summary(f"Contract run ({target.kind}, profile {target.profile})")
    if not quiet:
        print(f"\n{counts['PASS']} passed, {counts['FAIL']} failed, {counts['SKIP']} skipped  — evidence: {run_dir.path}")
    return counts, results, run_dir.path


def _run_one(entry, target, fixtures, store, sentinels, strict):
    skip = None
    if entry["profile"] == "L0":
        skip = ("SKIP(L0)", "product unit test (docs/test/README.md section 2)")
    elif entry["profile"] == "F" and target.profile == "runtime-v1":
        skip = ("SKIP(profile)", "full-contract case; target profile is runtime-v1")
    elif "hooks" in entry["needs"] and not target.is_double:
        skip = ("SKIP(needs)", "needs the double's test hooks")
    if skip:
        return (("FAIL", f"{skip[1]} (strict)") if strict and skip[0] == "SKIP(needs)" else skip)
    sandbox = target.sandbox(server="server" in entry["needs"])
    if fixtures:
        fixtures.reset()  # one fixture server serves the whole run: every case starts with an empty request log
    ctx = Ctx(target, sandbox, fixtures, store, sentinels)
    outcome = {}

    def work():
        try:
            if "server" in entry["needs"] and not target.is_double:
                sandbox.start_server()
            entry["fn"](ctx)
        except BaseException as exc:  # reported below; a worker thread must never die silently
            outcome["exc"] = exc

    worker = threading.Thread(target=work, daemon=True)
    worker.start()
    worker.join(CASE_TIMEOUT)
    try:
        if worker.is_alive():  # HARN-15: a hung child must not hang the run; closing the sandbox kills its process groups
            sandbox.close()
            worker.join(5)
            return "FAIL", f"timeout: the case ran longer than {CASE_TIMEOUT:g}s (DMEM_CASE_TIMEOUT)"
    finally:
        sandbox.close()
    exc = outcome.get("exc")
    if isinstance(exc, Skip):
        return ("FAIL", f"skipped in strict mode: {exc}") if strict else ("SKIP(case)", str(exc))
    if exc is not None:
        return "FAIL", f"{type(exc).__name__}: {str(exc)[:160]}"
    if ctx.failures:
        return "FAIL", "; ".join(ctx.failures)[:300]
    if ctx.checks == 0:
        return "FAIL", "vacuous: no expectation was evaluated (HARN-07)"
    return "PASS", ""
