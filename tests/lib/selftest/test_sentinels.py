"""HARN-04 / HARN-14: sentinel generation and scanning. Same seed, same corpus; variants are found; values are never reported; clean and contaminated sinks are told apart."""
import base64
import json
import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dmtest import sentinels

ROOT = Path(__file__).resolve().parents[3]


class SentinelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = sentinels.load()

    def test_generation_is_deterministic_and_matches_the_checked_in_corpus(self):
        first, second = sentinels.generate(), sentinels.generate()
        self.assertEqual(first, second)
        self.assertEqual(first, json.loads((ROOT / "tests" / "sentinels.json").read_text(encoding="utf-8")), "tests/sentinels.json is stale: run `python3 tests/lib/dmtest/sentinels.py --write`")

    def test_values_are_unique_and_cover_every_family(self):
        values = [i["value"] for i in self.corpus.items]
        self.assertEqual(len(values), len(set(values)))
        families = {i["family"] for i in self.corpus.items}
        for family in ("api_key", "jwt", "bearer", "private_key", "email", "phone", "national_id", "card", "account", "capability", "url_parts", "prose", "hidden", "injection"):
            self.assertIn(family, families)
        self.assertEqual(len(self.corpus.ids()), len(set(self.corpus.ids())))

    def test_every_variant_is_found_and_the_report_holds_no_value(self):
        for item in self.corpus.items[:20]:
            value = item["value"]
            raw = value.encode("utf-8")
            forms = {"literal": raw, "json": json.dumps(value)[1:-1].encode(), "percent": urllib.parse.quote(value, safe="").encode(),
                     "base64": base64.b64encode(raw).rstrip(b"="), "hex": raw.hex().encode()}
            for name, needle in forms.items():
                found = sentinels.scan(b"prefix " + needle + b" suffix", self.corpus)
                self.assertIn(item["id"], {f.sentinel_id for f in found}, f"{item['id']} not found as {name}")
        report = repr(sentinels.scan(b"x " + self.corpus.value("api_key", 1).encode(), self.corpus))
        self.assertNotIn(self.corpus.value("api_key", 1), report, "a finding must never print the value")

    def test_positive_and_negative_control_on_files(self):
        with tempfile.TemporaryDirectory() as d:
            clean, dirty = Path(d) / "clean", Path(d) / "dirty"
            for p in (clean, dirty):
                (p / "nested").mkdir(parents=True)
                (p / "nested" / "a.log").write_text("nothing to see here\n", encoding="utf-8")
            (dirty / "nested" / "b.json").write_text(json.dumps({"k": self.corpus.value("jwt", 2)}), encoding="utf-8")
            self.assertEqual(sentinels.scan([clean], self.corpus), [])
            hits = sentinels.scan([dirty], self.corpus)
            self.assertEqual([h.sentinel_id for h in hits], ["jwt-02"])
            self.assertTrue(hits[0].path.endswith("b.json"))

    def test_family_filter(self):
        blob = (self.corpus.value("email", 1) + " " + self.corpus.value("api_key", 1)).encode()
        self.assertEqual({f.sentinel_id for f in sentinels.scan(blob, self.corpus, families=("email",))}, {"email-01"})

    def test_symlinks_are_not_followed(self):
        with tempfile.TemporaryDirectory() as d:
            outside = Path(d) / "outside.txt"
            outside.write_text(self.corpus.value("bearer", 1), encoding="utf-8")
            sink = Path(d) / "sink"
            sink.mkdir()
            (sink / "link").symlink_to(outside)
            self.assertEqual(sentinels.scan([sink], self.corpus), [], "scanning must not leave the sink through a symlink (HARN-14)")


if __name__ == "__main__":
    unittest.main()
