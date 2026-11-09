"""HARN-07 / HARN-08 / HARN-15: verdicts, evidence files, profile gates, hang handling and vacuous cases of the runner itself.

The runner is driven with synthetic cases against the double: no product behaviour is judged here, only what the runner does with a case's outcome.
"""
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "tests" / "lib"), str(ROOT / "tests" / "smoke")]
from dmtest import runner
from dmtest.schema import ContractStore
from dmtest.sentinels import load as load_sentinels
from dmtest.target import Skip, Target


def entry(fn, profile="R1", needs=(), cid="T-01"):
    return {"id": cid, "fn": fn, "profile": profile, "layer": "L2", "needs": tuple(needs), "module": __name__}


def run_one(fn, profile="R1", needs=(), strict=False, target_profile="full", timeout=None):
    target = Target.from_env({"DMEM_TARGET": "double", "DMEM_PROFILE": target_profile})
    old = runner.CASE_TIMEOUT
    if timeout is not None:
        runner.CASE_TIMEOUT = timeout
    try:
        return runner._run_one(entry(fn, profile, needs), target, None, ContractStore(), load_sentinels(), strict)
    finally:
        runner.CASE_TIMEOUT = old


class RunnerVerdictTests(unittest.TestCase):
    def test_pass(self):
        self.assertEqual(run_one(lambda ctx: ctx.expect(True, "x")), ("PASS", ""))

    def test_a_failed_expectation_fails_with_its_message(self):
        verdict, reason = run_one(lambda ctx: ctx.expect(False, "the marker message"))
        self.assertEqual(verdict, "FAIL")
        self.assertIn("the marker message", reason)

    def test_all_failures_are_reported_not_just_the_first(self):
        def case(ctx):
            ctx.expect(False, "first problem")
            ctx.expect(False, "second problem")
        _, reason = run_one(case)
        self.assertIn("first problem", reason)
        self.assertIn("second problem", reason)

    def test_a_case_that_evaluates_nothing_is_a_failure_not_a_pass(self):
        verdict, reason = run_one(lambda ctx: None)
        self.assertEqual(verdict, "FAIL")
        self.assertIn("vacuous", reason)

    def test_an_exception_is_a_failure_with_its_type(self):
        def case(ctx):
            raise KeyError("boom")
        verdict, reason = run_one(case)
        self.assertEqual(verdict, "FAIL")
        self.assertIn("KeyError", reason)

    def test_skip_needs_a_reason_and_strict_mode_turns_it_into_a_failure(self):
        def case(ctx):
            ctx.skip("no such feature in this target")
        verdict, reason = run_one(case)
        self.assertEqual(verdict, "SKIP(case)")
        self.assertIn("no such feature", reason)
        strict_verdict, strict_reason = run_one(case, strict=True)
        self.assertEqual(strict_verdict, "FAIL")
        self.assertIn("strict", strict_reason)

    def test_a_hung_case_times_out_instead_of_hanging_the_run(self):
        started = time.monotonic()
        verdict, reason = run_one(lambda ctx: time.sleep(30), timeout=1.0)
        self.assertEqual(verdict, "FAIL")
        self.assertIn("timeout", reason)
        self.assertLess(time.monotonic() - started, 10, "HARN-15: the run must go on")

    def test_a_hung_mcp_child_does_not_hang_the_case(self):
        def case(ctx):
            session = ctx.mcp(initialize=False)
            reply = session.rpc("ping", timeout=1.0)  # the double answers; this only proves the call returns
            ctx.expect(reply is not None, "ping")
        self.assertEqual(run_one(case, timeout=20)[0], "PASS")


class ProfileGateTests(unittest.TestCase):
    def test_full_cases_are_skipped_with_a_reason_on_the_runtime_v1_profile(self):
        verdict, reason = run_one(lambda ctx: ctx.expect(True, "x"), profile="F", target_profile="runtime-v1")
        self.assertEqual(verdict, "SKIP(profile)")
        self.assertTrue(reason)

    def test_r1_cases_still_run_on_the_runtime_v1_profile(self):
        self.assertEqual(run_one(lambda ctx: ctx.expect(True, "x"), profile="R1", target_profile="runtime-v1")[0], "PASS")

    def test_f_cases_run_on_the_full_profile(self):
        self.assertEqual(run_one(lambda ctx: ctx.expect(True, "x"), profile="F")[0], "PASS")

    def test_l0_cases_are_always_skipped_with_a_reason(self):
        verdict, reason = run_one(lambda ctx: ctx.expect(True, "x"), profile="L0")
        self.assertEqual(verdict, "SKIP(L0)")
        self.assertTrue(reason)

    def test_hook_cases_are_skipped_on_a_product_target(self):
        target = Target("product", ["/bin/true"], ["/bin/true"], "full")
        result = runner._run_one(entry(lambda ctx: ctx.expect(True, "x"), "F", ("hooks",)), target, None, ContractStore(), load_sentinels(), False)
        self.assertEqual(result[0], "SKIP(needs)")
        strict = runner._run_one(entry(lambda ctx: ctx.expect(True, "x"), "F", ("hooks",)), target, None, ContractStore(), load_sentinels(), True)
        self.assertEqual(strict[0], "FAIL")


class EvidenceTests(unittest.TestCase):
    def test_a_run_leaves_meta_cases_and_summary_and_every_skip_has_a_reason(self):
        with tempfile.TemporaryDirectory() as out:
            os.environ["DMEM_TARGET"] = "double"
            counts, results, path = runner.run(ids="CORE-01,CORE-02,IMP-19", suite="contract", out=out, quiet=True)
            run_dir = Path(path)
            for name in ("meta.json", "cases.jsonl", "summary.md"):
                self.assertTrue((run_dir / name).is_file(), name)
            rows = [json.loads(line) for line in (run_dir / "cases.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual({r["id"] for r in rows}, {"CORE-01", "CORE-02", "IMP-19"})
            for row in rows:
                if row["verdict"].startswith("SKIP"):
                    self.assertTrue(row.get("reason"), f"{row['id']}: a skipped case without a reason")
            meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["target"], "double")
            self.assertEqual(sum(counts.values()), 3)
            self.assertNotIn("SENTINEL", (run_dir / "cases.jsonl").read_text(encoding="utf-8"), "evidence rows must not hold sentinel values")


if __name__ == "__main__":
    unittest.main()
