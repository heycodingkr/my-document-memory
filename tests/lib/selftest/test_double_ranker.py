"""Ranking of the test double against the expected orders in docs/test/functional-tests.md (RCL-01..09, RCL-13, RCL-18)."""
import copy
import json
import os
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests" / "env" / "dmem-double"))
from dmem_double import ranker  # noqa: E402

LIB = {m["fx_id"]: m for m in json.loads((ROOT / "tests" / "fixtures" / "rcl-lib.json").read_text(encoding="utf-8"))}
CAT = {m["fx_id"]: m for m in json.loads((ROOT / "tests" / "fixtures" / "shr-cat.json").read_text(encoding="utf-8"))}
DOCS = "docs.google.com/document/d/:id/edit"
LOCAL = {"id": "local", "workspaces": ["acme"]}  # the caller owns the 'local' fixtures and belongs to workspace acme


def order(query, caller=LOCAL, candidates=None, shuffle=None):
    items = list((candidates or LIB).values())
    if shuffle is not None:
        random.Random(shuffle).shuffle(items)
    base = {"url": DOCS, "provider": "google_docs", "limit": 3}
    base.update(query)
    return [r["candidate"]["fx_id"][3:] for r in ranker.rank(items, base, caller)]  # "fx_m1" -> "m1"


class Ranking(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("DMEM_DOUBLE_MUTATION", None)

    def test_rcl01_exact_route_then_host_wide_then_other_host(self):
        self.assertEqual(order({"doc_type": "resume", "locale": "ko-KR"}), ["m1", "m4", "m5"])

    def test_rcl02_doc_type_matches_across_hosts(self):
        self.assertEqual(order({"url": "www.example.org/templates/resume/modern", "provider": "other", "doc_type": "resume", "locale": "ko-KR"}),
                         ["m5", "m1", "m4"])

    def test_rcl03_url_only_uses_host_and_family(self):
        self.assertEqual(order({}), ["m1", "m3", "m2"])
        ids = order({"limit": 3})
        self.assertNotIn("m5", ids)  # other host
        self.assertNotIn("m8", ids)  # deck family

    def test_rcl04_locale_exact_language_none(self):
        self.assertEqual(order({"doc_type": "resume", "locale": "ja-JP"}), ["m3", "m1", "m2"])
        self.assertEqual(order({"doc_type": "resume", "locale": "en-GB"}), ["m2", "m1", "m3"])

    def test_rcl05_provider_tie_break_then_id(self):
        q = {"url": "example.com/x", "doc_type": "memo", "locale": "ko-KR"}
        self.assertEqual(order(dict(q, provider="markdown")), ["m11", "m10"])
        self.assertEqual(order(dict(q, provider="docx")), ["m10", "m11"])
        self.assertEqual(order(dict(q, provider="other")), ["m10", "m11"])  # same updated_at -> memory_id ascending

    def test_rcl06_tier_mine_team_public(self):
        self.assertEqual(order({"doc_type": "lesson_plan"}), ["m15", "m16", "m17"])

    def test_rcl07_keyword_aliases(self):
        q = {"doc_type": "report"}
        self.assertEqual(order(dict(q, keywords=["초안"]))[0], "m13")
        self.assertEqual(order(dict(q, keywords=["draft"]))[0], "m13")
        self.assertEqual(order(dict(q, keywords=["weekly"]))[0], "m12")
        hit = ranker.rank(list(LIB.values()), dict(q, url=DOCS, provider="google_docs", keywords=["초안"]), LOCAL)[0]
        self.assertIn("keywords", hit["matched_on"])

    def test_rcl08_limit(self):
        self.assertEqual(len(order({})), 3)
        self.assertEqual(len(order({"limit": 1})), 1)

    def test_rcl09_order_does_not_depend_on_input_order(self):
        reference = order({"doc_type": "resume", "locale": "ko-KR"})
        for seed in range(20):
            self.assertEqual(order({"doc_type": "resume", "locale": "ko-KR"}, shuffle=seed), reference)
            self.assertEqual(order({"url": "example.com/x", "doc_type": "memo", "provider": "other"}, shuffle=seed), ["m10", "m11"])

    def test_rcl13_scope_and_visibility(self):
        pool = dict(LIB)
        pool.update(CAT)
        anon = {"id": None, "workspaces": []}
        bob = {"id": "bob", "workspaces": []}
        carol = {"id": "carol", "workspaces": ["acme"]}
        alice = {"id": "alice", "workspaces": ["acme"]}
        vis = lambda caller, scope: {k for k, c in pool.items() if ranker.visible(c, caller, scope)}
        self.assertEqual({k for k in vis(anon, "all")}, {k for k, c in pool.items() if c["visibility"] == "public"})
        self.assertNotIn("fx_s5", vis(bob, "all"))
        self.assertIn("fx_s6", vis(bob, "all"))
        self.assertNotIn("fx_s6", vis(alice, "all"))
        self.assertIn("fx_s4", vis(carol, "team"))
        self.assertNotIn("fx_s4", vis(bob, "team"))
        self.assertNotIn("fx_s4", vis(anon, "all"))
        self.assertTrue(vis(alice, "mine") and all(pool[k]["owner"] == "alice" for k in vis(alice, "mine")))
        self.assertEqual(vis(anon, "mine"), set())

    def test_rcl18_status_filters_and_needs_reverify(self):
        pool = copy.deepcopy(LIB)
        pool["fx_m2"]["status"] = "superseded"
        pool["fx_m3"]["status"] = "retired"
        self.assertNotIn("m2", order({"doc_type": "resume"}, candidates=pool))
        self.assertNotIn("m3", order({"doc_type": "resume"}, candidates=pool))
        # needs_reverify only loses to fresh items that tie on every EARLIER tuple element (locale, route, provider, tier, keywords).
        pool = copy.deepcopy(LIB)
        clone = copy.deepcopy(pool["fx_m10"])
        clone.update({"fx_id": "fx_m00", "status": "needs_reverify"})  # smaller id than the fresh twins: only freshness can push it back
        pool["fx_m00"] = clone
        q = {"url": "example.com/x", "provider": "other", "doc_type": "memo", "locale": "ko-KR", "limit": 3}
        self.assertEqual(order(q, candidates=pool), ["m10", "m11", "m00"])
        # a needs_reverify item that is better on an earlier element still wins (exact route beats freshness)
        pool = copy.deepcopy(LIB)
        pool["fx_m1"]["status"] = "needs_reverify"
        self.assertEqual(order({"doc_type": "resume", "locale": "ko-KR"}, candidates=pool)[0], "m1")

    def test_mutations_change_the_result(self):
        clean = order({"doc_type": "resume", "locale": "ja-JP"})
        os.environ["DMEM_DOUBLE_MUTATION"] = "route_before_locale"
        self.assertNotEqual(order({"doc_type": "resume", "locale": "ja-JP"}), clean)
        os.environ["DMEM_DOUBLE_MUTATION"] = "four_hints"
        self.assertEqual(len(order({})), 4)
        os.environ["DMEM_DOUBLE_MUTATION"] = "nondeterministic_rank"
        seen = {tuple(order({"url": "example.com/x", "doc_type": "memo", "provider": "other"}, shuffle=0)) for _ in range(40)}
        self.assertGreater(len(seen), 1)


if __name__ == "__main__":
    unittest.main()
