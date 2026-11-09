"""Code to docs traceability (HARN-10): every case the harness implements is defined in docs/test, and every R1/F case defined there is implemented or explained.

    PYTHONPATH=tests/lib python3 -B -m dmtest.codetrace            # exit 1 on any problem
    PYTHONPATH=tests/lib python3 -B -m dmtest.codetrace --list     # also list the accounted-for IDs by status

Rules (docs/test/harness-verification.md HARN-10):
  1. A case ID used by code must be defined in docs/test (doc-first).
  2. A functional-tests.md row whose stage is R1 or F must be implemented as a case, or appear in tests/coverage.json with a status and a reason:
       skip          not automatable by this harness (the reason says why and where it IS verified)
       product-only  needs the product (its own unit/integration tests)
       L0            product unit test
       external      verified by another harness in this repository (for example tests/smoke/arise_smoke.py)
       covered       a scenario row that is the same check as feature cases that ARE implemented (the reason names them)
  3. coverage.json may only name defined IDs, must give every entry a reason, and must not list an implemented case as `skip` (a stale excuse).
Silent omissions are failures: an ID that is neither implemented nor explained is reported.
"""
import json
import re
import sys
from pathlib import Path

from .doctrace import defined_ids

REPO = Path(__file__).resolve().parents[3]
COVERAGE = REPO / "tests" / "coverage.json"
STATUSES = ("skip", "product-only", "L0", "external", "covered")
ROW = re.compile(r"^\|\s*([A-Z]{2,6}-[A-J]?\d{2,3})\s*\|\s*([A-Za-z0-9]+)\s*\|", re.M)


def implemented_ids():
    import pkgutil
    from importlib import import_module
    sys.path[:0] = [str(REPO / "tests" / "lib"), str(REPO / "tests" / "smoke")]
    pkg = import_module("cases")
    for info in sorted(pkgutil.iter_modules(pkg.__path__), key=lambda i: i.name):
        if info.name != "util":
            import_module(f"cases.{info.name}")
    from dmtest import runner
    return dict(runner.REGISTRY)


def required_ids():
    """{id: stage} for functional-tests.md rows staged R1 or F."""
    text = (REPO / "docs" / "test" / "functional-tests.md").read_text(encoding="utf-8")
    return {i: stage for i, stage in ROW.findall(text) if stage in ("R1", "F")}


def check():
    registry = implemented_ids()
    defined = defined_ids()
    coverage = json.loads(COVERAGE.read_text(encoding="utf-8")) if COVERAGE.exists() else {}
    required = required_ids()
    problems = []
    for case_id in sorted(registry):
        if case_id not in defined:
            problems.append(f"code uses {case_id}, which no docs/test document defines")
    for case_id, entry in sorted(coverage.items()):
        if case_id not in defined:
            problems.append(f"coverage.json names {case_id}, which no docs/test document defines")
        if entry.get("status") not in STATUSES:
            problems.append(f"coverage.json {case_id}: status must be one of {STATUSES}")
        if not str(entry.get("reason", "")).strip():
            problems.append(f"coverage.json {case_id}: a reason is required")
        if case_id in registry and entry.get("status") == "skip":
            problems.append(f"coverage.json {case_id}: listed as skip but the case is implemented")
    for case_id in sorted(required):
        if case_id not in registry and case_id not in coverage:
            problems.append(f"{case_id} (stage {required[case_id]}) is neither implemented nor explained in coverage.json")
    return {"problems": problems, "implemented": sorted(registry), "coverage": coverage, "required": required}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    report = check()
    if "--list" in argv:
        print(f"implemented cases: {len(report['implemented'])}")
        by_status = {}
        for case_id, entry in report["coverage"].items():
            by_status.setdefault(entry.get("status"), []).append(case_id)
        for status, ids in sorted(by_status.items(), key=lambda kv: str(kv[0])):
            print(f"{status}: {len(ids)}  {', '.join(sorted(ids))}")
    for line in report["problems"]:
        print("PROBLEM", line)
    required = report["required"]
    accounted = sum(1 for i in required if i in report["implemented"] or i in report["coverage"])
    print(f"{'OK' if not report['problems'] else 'FAIL'}: {len(report['implemented'])} cases implemented, "
          f"{accounted}/{len(required)} R1/F rows accounted for, {len(report['problems'])} problem(s)")
    return 1 if report["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
