"""HARN-04 / HARN-14: the eight-sink sentinel sweep (docs/test/security-scenarios.md). A sentinel planted in ANY sink is found, a clean world finds nothing, and a sink that collected nothing is reported."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "tests" / "lib")]
from dmtest import runner
from dmtest.schema import ContractStore
from dmtest.sentinels import load as load_sentinels
from dmtest.target import Target


class FakeFixtures:
    def __init__(self, entries=()):
        self.base_url, self._entries = "http://127.0.0.1:1", list(entries)

    def log(self):
        return list(self._entries)


class SweepTests(unittest.TestCase):
    def setUp(self):
        self.target = Target.from_env({})
        self.box = self.target.sandbox(server=True)
        self.corpus = load_sentinels()
        self.cli = self.box.cli("alice")
        saved = self.cli.json(["save", "--kind", "template", "--title", "seed", "--doc-type", "memo", "--locale", "ko-KR", "--provider", "markdown", "--stdin", "--format", "markdown"], stdin="# 메모\n\n본문입니다")
        assert saved.exit == 0, "the seed save must work: a transcript, an argv record and a server state file now exist"
        (self.box.home("alice")).mkdir(parents=True, exist_ok=True)
        (self.box.home("alice") / "seed.json").write_text("{}", encoding="utf-8")  # a local store file
        self.token = self.corpus.value("api_key", 1)

    def tearDown(self):
        self.box.close()

    def ctx(self, fixtures=None):
        return runner.Ctx(self.target, self.box, fixtures, ContractStore(), self.corpus)

    def sweep(self, fixtures=None, **kw):
        return self.ctx(fixtures).sweep(identities=("alice",), **kw)

    def test_a_clean_world_has_no_findings_and_every_sink_is_collected(self):
        report = self.sweep(FakeFixtures([{"path": "/x"}]))
        self.assertEqual(report["findings"], {})
        self.assertEqual(report["empty"], [], "every sink was collected (an existing but empty cache directory still counts as collected)")
        self.assertGreater(report["sizes"]["client_output"], 0)
        self.assertGreater(report["sizes"]["process_args_env"], 0)

    def test_empty_sinks_are_reported_unless_the_scenario_allows_them(self):
        self.assertEqual(self.sweep(None)["empty"], ["remote_requests"], "no fixture server was started: sink 6 has nothing to look at, and the sweep must say so")
        self.assertEqual(self.sweep(None, allow_empty=("remote_requests",))["empty"], [])

    def plant_and_expect(self, sink, plant, fixtures=None):
        plant()
        report = self.sweep(fixtures)
        self.assertEqual(list(report["findings"]), [sink], f"a sentinel planted in {sink} must be found there and nowhere else")
        self.assertEqual([f.sentinel_id for f in report["findings"][sink]], ["api_key-01"])

    def test_every_sink_detects_a_planted_sentinel(self):
        home = self.box.home("alice")
        root = self.box.tmp / "alice"
        token = self.token.encode()
        self.plant_and_expect("client_output", lambda: self.cli.transcript.append((b"result " + token, b"")))
        self.cli.transcript.pop()
        (home / "log").mkdir(parents=True, exist_ok=True)
        self.plant_and_expect("logs_diagnostics", lambda: (home / "log" / "x.log").write_bytes(b"line " + token))
        (home / "log" / "x.log").unlink()
        self.plant_and_expect("local_store", lambda: (home / "extra.json").write_text(json.dumps({"v": self.token})))
        (home / "extra.json").unlink()
        (root / "cache").mkdir(parents=True, exist_ok=True)
        self.plant_and_expect("cache", lambda: (root / "cache" / "entry").write_bytes(token))
        (root / "cache" / "entry").unlink()
        self.plant_and_expect("server_requests", lambda: self.box.request_log_path.write_text(json.dumps({"body": self.token}) + "\n"))
        self.box.request_log_path.unlink()
        self.plant_and_expect("remote_requests", lambda: None, FakeFixtures([{"path": "/" + self.token}]))
        self.plant_and_expect("process_args_env", lambda: self.cli.calls.append(([self.token], 0)))
        self.cli.calls.pop()
        self.plant_and_expect("exported_files", lambda: (root / "export.out").write_bytes(token))

    def test_variants_are_found_in_a_sink(self):
        import base64
        (self.box.tmp / "alice" / "export.out").write_bytes(base64.b64encode(self.token.encode()))
        self.assertEqual(list(self.sweep()["findings"]), ["exported_files"])

    def test_originals_hold_personal_data_legitimately_but_never_secrets_or_capability_ids(self):
        originals = self.box.home("alice") / "originals"
        originals.mkdir(parents=True, exist_ok=True)
        (originals / "a").write_text(self.corpus.value("email", 1))
        self.assertEqual(self.sweep()["findings"], {}, "a preserved upload may contain the user's own personal data")
        (originals / "b").write_text(self.corpus.value("capability", 1))
        report = self.sweep()
        self.assertEqual(list(report["findings"]), ["local_store_originals"])

    def test_a_capability_id_in_the_remote_request_log_is_expected(self):
        cap = self.corpus.value("capability", 1)
        report = self.sweep(FakeFixtures([{"path": f"/p/google-docs/document/d/{cap}/export"}]))
        self.assertNotIn("remote_requests", report["findings"], "fetching the document necessarily sends its id to that site")
        leak = self.sweep(FakeFixtures([{"path": "/x?" + self.corpus.value("url_parts", 1)}]))
        self.assertIn("remote_requests", leak["findings"], "but the query part must never be sent")


if __name__ == "__main__":
    unittest.main()
