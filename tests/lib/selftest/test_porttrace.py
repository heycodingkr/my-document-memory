"""HARN-17: independent positive/negative controls for the WAM port inventory gate."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dmtest.porttrace import audit


class PortTraceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dmem-porttrace-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.upstream = self.root / "wam"
        self.destination = self.root / "dmem"
        for root in (self.upstream, self.destination):
            (root / "docs/spec").mkdir(parents=True)
            (root / "docs/test").mkdir()
        (self.upstream / "docs/spec/core.md").write_text("upstream contract")
        (self.upstream / "docs/test/pilot.md").write_text("unrelated pilot result")
        (self.destination / "docs/spec/core.md").write_text("document contract")
        self.manifest = self.root / "port.json"
        self.rows = [
            {"source": "docs/spec/core.md", "disposition": "adapt",
             "targets": ["docs/spec/core.md"], "reason": "URL plus form"},
            {"source": "docs/test/pilot.md", "disposition": "exclude",
             "targets": [], "reason": "WAM measurement is not a document-memory measurement"},
        ]

    def check(self, rows=None, **kwargs):
        self.manifest.write_text(json.dumps({"schema_version": 1, "entries": self.rows if rows is None else rows}))
        return audit(self.manifest, self.destination, kwargs.pop("upstream", self.upstream), **kwargs)

    def test_complete_inventory_and_explicit_exclusion(self):
        report = self.check(require_upstream=True)
        self.assertEqual(report["errors"], [])
        self.assertTrue(report["upstream_checked"])
        self.assertEqual((report["sources"], report["adapted"], report["excluded"]), (2, 1, 1))

    def test_new_upstream_and_deleted_upstream_are_detected(self):
        path = self.upstream / "docs/spec/new.md"
        path.write_text("new")
        self.assertTrue(any("unmapped" in e and "new.md" in e for e in self.check()["errors"]))
        path.unlink()
        (self.upstream / "docs/spec/core.md").unlink()
        self.assertTrue(any("missing_source" in e for e in self.check()["errors"]))

    def test_duplicate_source_and_missing_target(self):
        self.assertTrue(any("duplicate" in e for e in self.check(self.rows + self.rows[:1])["errors"]))
        (self.destination / "docs/spec/core.md").unlink()
        self.assertTrue(any("missing_target" in e for e in self.check()["errors"]))

    def test_invalid_rows_fail_without_crashing(self):
        for patch in ({"reason": " "}, {"disposition": "copy"}, {"targets": []},
                      {"targets": "docs/spec/core.md"}, {"source": None}, {"reason": 4}):
            with self.subTest(patch=patch):
                self.assertTrue(self.check([{**self.rows[0], **patch}, self.rows[1]])["errors"])
        for value in (None, "a row", 42):
            self.assertTrue(self.check([value])["errors"])
        self.assertTrue(self.check([{**self.rows[1], "targets": ["docs/spec/core.md"]}])["errors"])

    def test_paths_cannot_escape_either_root(self):
        for bad in ("../core.md", "/tmp/core.md", "docs/spec/../../../core.md", "docs\\spec\\core.md"):
            for field in ("source", "targets"):
                with self.subTest(path=bad, field=field):
                    patch = {field: [bad] if field == "targets" else bad}
                    self.assertTrue(self.check([{**self.rows[0], **patch}, self.rows[1]])["errors"])
        outside = self.root / "outside.md"
        outside.write_text("outside")
        target = self.destination / "docs/spec/core.md"
        target.unlink()
        target.symlink_to(outside)
        self.assertTrue(self.check()["errors"])

    def test_missing_upstream_is_explicit_and_strict_mode_fails(self):
        absent = self.root / "absent"
        report = self.check(upstream=absent)
        self.assertEqual(report["errors"], [])
        self.assertFalse(report["upstream_checked"])
        self.assertTrue(self.check(upstream=absent, require_upstream=True)["errors"])

    def test_empty_or_malformed_input_cannot_pass(self):
        self.assertTrue(self.check([])["errors"])
        for contents in ("{", "[]", '{"schema_version":true,"entries":[]}', '{"schema_version":1,"entries":{}}'):
            self.manifest.write_text(contents)
            self.assertTrue(audit(self.manifest, self.destination, self.upstream)["errors"])
        self.manifest.unlink()
        self.assertTrue(audit(self.manifest, self.destination, self.upstream)["errors"])


if __name__ == "__main__":
    unittest.main()
