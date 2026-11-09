"""HARN-12: static checks of contracts/*.json. Tool set, annotations, dangling $refs (a dangling ref once hung the double's MCP server), the served catalogue size, vocabulary tables."""
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests" / "lib"))
from dmtest.mcpclient import McpSession
from dmtest.procs import isolated_env, short_tmp
from dmtest.schema import ContractStore, validate

CONTRACTS = ROOT / "contracts"
TOOLS = ["doc_memory_status", "doc_memory_recall", "doc_memory_search", "doc_memory_expand", "doc_memory_web_search", "doc_memory_web_preview",
         "doc_memory_save", "doc_memory_import", "doc_memory_copy", "doc_memory_publish", "doc_memory_delete", "doc_memory_outcome"]
READ_ONLY = {"doc_memory_status", "doc_memory_recall", "doc_memory_search", "doc_memory_expand", "doc_memory_web_search", "doc_memory_web_preview"}
CATALOG_BUDGET = 12000


def walk(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield (path, key, value)
            yield from walk(value, f"{path}/{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from walk(value, f"{path}/{i}")


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in CONTRACTS.glob("*.json")}
        cls.tools = cls.files["mcp-tools.v1.json"]["tools"]

    def test_twelve_unique_tools(self):
        names = [t["name"] for t in self.tools]
        self.assertEqual(names, TOOLS)
        self.assertEqual(len(set(names)), 12)

    def test_annotations_follow_the_rule(self):
        for t in self.tools:
            with self.subTest(t["name"]):
                a = t["annotations"]
                self.assertEqual(a.get("readOnlyHint"), t["name"] in READ_ONLY)
                self.assertEqual(a.get("destructiveHint", False), t["name"] == "doc_memory_delete")

    def test_every_tool_has_description_input_and_result(self):
        for t in self.tools:
            with self.subTest(t["name"]):
                self.assertLessEqual(len(t["description"]), 4096)
                self.assertEqual(t["inputSchema"]["type"], "object")
                self.assertIs(t["inputSchema"].get("additionalProperties"), False, "an unknown field must be rejected")
                self.assertTrue(t["result"].startswith(("#/", "memory.v1.json#/")))

    def test_every_ref_resolves(self):
        store = ContractStore()
        refs = 0
        for name, document in self.files.items():
            for path, key, value in walk(document):
                if key == "$ref" and isinstance(value, str):
                    refs += 1
                    try:
                        store.resolve(value, name)
                    except (KeyError, TypeError) as exc:
                        self.fail(f"{name}{path}: dangling $ref {value!r} ({exc!r})")
        self.assertGreater(refs, 50, "the walk must actually find the refs")

    def test_result_schemas_accept_a_minimal_valid_error_and_reject_junk(self):
        store = ContractStore()
        for t in self.tools:
            with self.subTest(t["name"]):
                self.assertTrue(validate("not an object", store.result_schema(t["name"]), store), "a string must never be a valid result")

    def test_served_catalogue_fits_the_byte_budget(self):
        tmp = short_tmp()
        try:
            env = isolated_env(tmp, DMEM_HOME=str(tmp / "dmem"), DMEM_ISOLATED="1")
            session = McpSession([sys.executable, "-B", str(ROOT / "tests" / "env" / "dmem-double" / "dmem-mcp")], env)
            try:
                init = session.initialize()
                served = {"tools": session.list_tools(), "instructions": init["result"]["instructions"]}
            finally:
                session.close()
        finally:
            subprocess.run(["rm", "-rf", str(tmp)], check=False)
        size = len(json.dumps(served, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        print(f"\n  served tools/list + instructions: {size} bytes (budget {CATALOG_BUDGET})")
        self.assertEqual(len(served["tools"]), 12)
        self.assertLessEqual(size, CATALOG_BUDGET)
        self.assertLessEqual(len(served["instructions"]), 4096)
        self.assertTrue(re.search(r"recall", served["instructions"][:512], re.I) and re.search(r"untrusted", served["instructions"][:512], re.I), "the first 512 characters must carry the recall and untrusted rules")

    def test_license_vocabulary_matches_the_sharing_table(self):
        vocab = json.loads((CONTRACTS / "vocab" / "licenses.json").read_text(encoding="utf-8"))
        ids = {item["id"] for item in vocab["items"]} if "items" in vocab else {item["id"] for item in vocab["licenses"]}
        text = (ROOT / "docs" / "spec" / "sharing.md").read_text(encoding="utf-8")
        for license_id in ids:
            self.assertIn(license_id, text, f"{license_id} is in the vocabulary but not in sharing.md")
        publish = next(t for t in self.tools if t["name"] == "doc_memory_publish")
        enum = publish["inputSchema"]["properties"]["license"]
        listed = enum.get("enum") or self.files["memory.v1.json"]["$defs"]["LicenseId"]["enum"]
        self.assertTrue(set(listed) <= ids | {"unknown"}, "the tool schema offers a licence the vocabulary does not know")

    def test_doc_type_aliases_in_form_md_exist_in_the_vocabulary(self):
        vocab = json.loads((CONTRACTS / "vocab" / "doc_types.json").read_text(encoding="utf-8"))
        types = {item["id"]: item for item in vocab["items"]} if "items" in vocab else {item["id"]: item for item in vocab["doc_types"]}
        aliases = {a["value"]: (item["id"], a.get("implies", {})) for item in types.values() for a in item.get("aliases", [])}
        for alias, doc_type, variant in (("이력서", "resume", None), ("cv", "resume", "cv"), ("履歴書", "resume", "jp_rirekisho"), ("세금계산서", "invoice", "kr_tax_invoice"),
                                         ("適格請求書", "invoice", "jp_qualified"), ("견적서", "quote", None), ("見積書", "quote", None), ("angebot", "quote", None),
                                         ("회의록", "meeting_minutes", None), ("議事録", "meeting_minutes", None), ("교안", "lesson_plan", None)):
            with self.subTest(alias):
                found = aliases.get(alias) or ((alias, {}) if alias in types else None)
                self.assertIsNotNone(found, f"alias {alias} missing")
                if alias in aliases:
                    self.assertEqual(aliases[alias][0], doc_type)
                    self.assertEqual(aliases[alias][1].get("variant"), variant)


if __name__ == "__main__":
    unittest.main()
