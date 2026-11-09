#!/usr/bin/env python3
"""HARN-02 / HARN-13: does the suite notice a deliberately broken implementation?

For every mutant (tests/README.md, "변이") the test double is started with DMEM_DOUBLE_MUTATION=<name> and the designated cases are run.
A mutant is KILLED when EVERY designated case fails. Before that, the clean double (no mutation) must pass all designated cases (positive control),
so "the case failed" can only mean "the case noticed the defect".

    python3 -B tests/env/mutation_check.py                       # all mutants
    python3 -B tests/env/mutation_check.py --only four_hints,no_untrusted
    python3 -B tests/env/mutation_check.py --repeat 2            # HARN-13: the clean control twice, verdicts must be identical

Exit 0 only when the control is clean and every designated case of every mutant failed. A designated case that is not implemented is reported as
MISSING and fails the check: a mutant nobody can detect is a hole in the suite.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tests" / "smoke" / "run_all.py"

# name -> (what is broken, designated cases that must fail)
MUTANTS = {
    "leak_query": ("normalisation keeps the query", ["CORE-04"]),
    "capability_leak": ("a Google document id is stored", ["CORE-19"]),
    "echo_input": ("errors echo the offending input", ["CORE-23"]),
    "four_hints": ("recall returns four hints", ["RCL-08", "MCP-09"]),
    "no_untrusted": ("recall drops `untrusted` and `framing`", ["RCL-11"]),
    "route_before_locale": ("the ranking puts route before locale", ["RCL-01", "RCL-04"]),
    "nondeterministic_rank": ("ties are ordered at random", ["RCL-09"]),
    "l2_in_recall": ("recall hints carry L2", ["MEM-04", "RCL-11"]),
    "partial_secret_save": ("a secret is masked and the rest stored", ["MEM-15", "LIB-08"]),
    "structure_keeps_prose": ("structure-only keeps the prose", ["MEM-14", "IMP-05"]),
    "license_ignored": ("an unverified licence still allows a full copy", ["SHR-12", "IMP-06"]),
    "copy_mutates_origin": ("a copy changes the origin's updated_at", ["SHR-11"]),
    "cross_tenant_leak": ("another user's private item is visible", ["SHR-16", "RCL-13"]),
    "no_consent_write": ("a publish without consent is recorded", ["SHR-02"]),
    "ssrf_no_guard": ("private addresses can be imported", ["IMP-09", "IMP-10"]),
    "overwrite_export": ("export overwrites an existing file", ["FMT-14"]),
    "stdout_noise": ("the MCP server prints a banner on stdout", ["MCP-06"]),
    "exit_code_wrong": ("not_found does not exit with 7", ["CLI-26"]),
}
LINE = re.compile(r"^\s*(ok|FAIL|skip)\s+(\S+)\s*(.*)$")


def run_cases(ids, mutation=None, timeout=420):
    env = dict(os.environ)
    env.pop("DMEM_DOUBLE_MUTATION", None)
    if mutation:
        env["DMEM_DOUBLE_MUTATION"] = mutation
    env["DMEM_TARGET"] = "double"
    try:
        proc = subprocess.run([sys.executable, "-B", str(RUNNER), "--suite", "contract", "--ids", ",".join(ids)], cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {i: ("TIMEOUT", "the run exceeded the check's own deadline") for i in ids}
    verdicts = {}
    for line in proc.stdout.splitlines():
        m = LINE.match(line)
        if m:
            verdicts[m.group(2)] = ({"ok": "PASS", "FAIL": "FAIL", "skip": "SKIP"}[m.group(1)], m.group(3).strip())
    return {i: verdicts.get(i, ("MISSING", "no such case was run")) for i in ids}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", default="", help="comma separated mutant names")
    ap.add_argument("--repeat", type=int, default=1, help="run the clean control this many times and require identical verdicts (HARN-13)")
    args = ap.parse_args()
    chosen = {k: v for k, v in MUTANTS.items() if not args.only or k in {x.strip() for x in args.only.split(",")}}
    unknown = set(x.strip() for x in args.only.split(",") if x.strip()) - set(MUTANTS)
    if unknown:
        print(f"unknown mutant(s): {sorted(unknown)}")
        return 2
    designated = sorted({case for _, ids in chosen.values() for case in ids})
    started = time.time()

    print(f"positive control: {len(designated)} designated cases on the clean double" + (f" x{args.repeat}" if args.repeat > 1 else ""))
    controls = [run_cases(designated) for _ in range(max(1, args.repeat))]
    control = controls[0]
    clean_bad = {c: v for c, v in control.items() if v[0] != "PASS"}
    unstable = sorted(c for c in designated if len({run[c][0] for run in controls}) > 1)
    for case, (verdict, reason) in sorted(clean_bad.items()):
        print(f"  CONTROL {verdict:<8} {case}  {reason[:140]}")
    if unstable:
        print(f"  UNSTABLE across repeats: {unstable}")

    rows, failures = [], 0
    for name, (what, ids) in chosen.items():
        result = run_cases(ids, mutation=name)
        killed = all(result[i][0] == "FAIL" for i in ids)
        detail = ", ".join(f"{i}:{result[i][0]}" for i in ids)
        rows.append((name, what, ids, result, killed))
        failures += 0 if killed else 1
        print(f"  {'KILLED  ' if killed else 'SURVIVED'} {name:<24} {detail}")

    out = ROOT / "target" / "e2e-logs" / "mutation" / time.strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps({"control": control, "unstable": unstable, "mutants": {n: {"what": w, "cases": {i: r[i] for i in ids}, "killed": k} for n, w, ids, r, k in rows}}, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Mutation check (HARN-02)", "", f"clean control: {len(designated) - len(clean_bad)}/{len(designated)} designated cases pass", "",
             "| mutant | what is broken | designated cases | verdict |", "|---|---|---|---|"]
    lines += [f"| `{n}` | {w} | {', '.join(f'{i}={r[i][0]}' for i in ids)} | {'killed' if k else '**SURVIVED**'} |" for n, w, ids, r, k in rows]
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    ok = not clean_bad and not unstable and failures == 0
    print(f"\n{sum(1 for r in rows if r[4])}/{len(rows)} mutants killed, control {'clean' if not clean_bad else 'DIRTY'}"
          f"{', unstable cases ' + str(unstable) if unstable else ''} in {time.time() - started:.0f}s — evidence: {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
