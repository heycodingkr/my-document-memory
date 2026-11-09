#!/usr/bin/env python3
"""Run the black-box contract + smoke cases against the double (default) or a product.

    python3 -B tests/smoke/run_all.py [--target double|product] [--profile full|runtime-v1]
                                      [--suite smoke|contract|all] [--ids 'CORE-*,SMK-*'] [--strict] [--out DIR]

Exit code 0 only when no case FAILed (and, with --strict, nothing in scope was skipped). See tests/README.md.
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tests" / "lib"), str(ROOT / "tests" / "smoke")]
sys.dont_write_bytecode = True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", choices=["double", "product"])
    ap.add_argument("--profile", choices=["full", "runtime-v1"])
    ap.add_argument("--suite", choices=["smoke", "contract", "all"], default="all")
    ap.add_argument("--ids", default="")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    if args.target:
        os.environ["DMEM_TARGET"] = args.target
    from dmtest import runner
    counts, _, _ = runner.run(ids=args.ids, profile=args.profile, suite=args.suite, strict=args.strict, out=args.out, quiet=args.quiet)
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
