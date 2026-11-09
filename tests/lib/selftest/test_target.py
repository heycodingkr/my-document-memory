"""HARN-16: the target adapter. The same cases must give the same verdicts when the double is reached the way a product would be (absolute DMEM_BIN / DMEM_MCP_BIN)."""
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "tests" / "lib"), str(ROOT / "tests" / "smoke")]
from dmtest import runner
from dmtest.schema import ContractStore
from dmtest.sentinels import load as load_sentinels
from dmtest.target import Target, TargetError


class TargetEnvTests(unittest.TestCase):
    def test_product_without_binaries_is_a_clear_error(self):
        with self.assertRaises(TargetError) as ctx:
            Target.from_env({"DMEM_TARGET": "product"})
        self.assertIn("DMEM_BIN", str(ctx.exception))

    def test_relative_or_missing_binaries_are_refused(self):
        with self.assertRaises(TargetError):
            Target.from_env({"DMEM_TARGET": "product", "DMEM_BIN": "dmem", "DMEM_MCP_BIN": "dmem-mcp"})
        with self.assertRaises(TargetError):
            Target.from_env({"DMEM_TARGET": "product", "DMEM_BIN": "/nonexistent/dmem", "DMEM_MCP_BIN": "/nonexistent/dmem-mcp"})

    def test_unknown_target_or_profile_is_refused(self):
        with self.assertRaises(TargetError):
            Target.from_env({"DMEM_TARGET": "something"})
        with self.assertRaises(TargetError):
            Target.from_env({"DMEM_PROFILE": "nope"})

    def test_defaults_are_the_double_on_the_full_profile(self):
        t = Target.from_env({})
        self.assertTrue(t.is_double)
        self.assertEqual(t.profile, "full")


class ProductPathTests(unittest.TestCase):
    """Run real cases through wrapper scripts that exec the double, as a product binary would be run."""

    def test_the_same_cases_give_the_same_verdicts_through_the_product_adapter(self):
        double = ROOT / "tests" / "env" / "dmem-double"
        with tempfile.TemporaryDirectory() as d:
            wrappers = {}
            for name in ("dmem", "dmem-mcp"):
                path = Path(d) / name
                path.write_text(f"#!/bin/sh\nexec {sys.executable} -B {double / name} \"$@\"\n", encoding="utf-8")
                path.chmod(path.stat().st_mode | stat.S_IXUSR)
                wrappers[name] = str(path)
            product = Target.from_env({"DMEM_TARGET": "product", "DMEM_BIN": wrappers["dmem"], "DMEM_MCP_BIN": wrappers["dmem-mcp"], "DMEM_PROFILE": "runtime-v1"})
            reference = Target.from_env({"DMEM_TARGET": "double", "DMEM_PROFILE": "runtime-v1"})
            import cases.core  # noqa: F401  (registers CORE-*)
            import cases.form  # noqa: F401
            ids = ["CORE-01", "CORE-02", "CORE-12", "FORM-05", "FORM-10"]
            verdicts = {}
            for label, target in (("product", product), ("double", reference)):
                verdicts[label] = [runner._run_one(runner.REGISTRY[i], target, None, ContractStore(), load_sentinels(), False)[0] for i in ids]
            self.assertEqual(verdicts["product"], verdicts["double"])
            self.assertEqual(set(verdicts["product"]), {"PASS"}, "the cases must really run through the wrapper, not be skipped")


if __name__ == "__main__":
    unittest.main()
