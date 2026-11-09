"""HARN-03: the contract-test JSON Schema validator. Known valid and invalid instances for every supported keyword; error strings never hold instance values."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dmtest.schema import ContractStore, validate

CONTRACTS = Path(__file__).resolve().parents[3] / "contracts"

# (name, schema, instance, valid)
CASES = [
    ("type string ok", {"type": "string"}, "x", True),
    ("type string bad", {"type": "string"}, 1, False),
    ("type integer ok", {"type": "integer"}, 3, True),
    ("type integer rejects bool", {"type": "integer"}, True, False),
    ("type integer rejects float", {"type": "integer"}, 1.5, False),
    ("type number ok", {"type": "number"}, 1.5, True),
    ("type number rejects bool", {"type": "number"}, False, False),
    ("type boolean ok", {"type": "boolean"}, False, True),
    ("type object ok", {"type": "object"}, {}, True),
    ("type object bad", {"type": "object"}, [], False),
    ("type array ok", {"type": "array"}, [], True),
    ("type null ok", {"type": "null"}, None, True),
    ("type list ok", {"type": ["string", "null"]}, None, True),
    ("type list bad", {"type": ["string", "null"]}, 5, False),
    ("enum ok", {"enum": ["a", "b"]}, "a", True),
    ("enum bad", {"enum": ["a", "b"]}, "c", False),
    ("const ok", {"const": "stddoc/1"}, "stddoc/1", True),
    ("const bad", {"const": "stddoc/1"}, "stddoc/2", False),
    ("minLength ok", {"type": "string", "minLength": 2}, "ab", True),
    ("minLength bad", {"type": "string", "minLength": 2}, "a", False),
    ("maxLength ok", {"type": "string", "maxLength": 2}, "ab", True),
    ("maxLength bad", {"type": "string", "maxLength": 2}, "abc", False),
    ("maxLength counts characters", {"type": "string", "maxLength": 3}, "가나다", True),
    ("pattern ok", {"type": "string", "pattern": "^[a-z]+$"}, "abc", True),
    ("pattern bad", {"type": "string", "pattern": "^[a-z]+$"}, "ab1", False),
    ("minimum ok", {"type": "integer", "minimum": 1}, 1, True),
    ("minimum bad", {"type": "integer", "minimum": 1}, 0, False),
    ("maximum ok", {"type": "integer", "maximum": 3}, 3, True),
    ("maximum bad", {"type": "integer", "maximum": 3}, 4, False),
    ("minItems bad", {"type": "array", "minItems": 1}, [], False),
    ("maxItems bad", {"type": "array", "maxItems": 1}, [1, 2], False),
    ("maxItems ok", {"type": "array", "maxItems": 2}, [1, 2], True),
    ("uniqueItems ok", {"type": "array", "uniqueItems": True}, [1, 2], True),
    ("uniqueItems bad", {"type": "array", "uniqueItems": True}, [1, 1], False),
    ("uniqueItems compares objects", {"type": "array", "uniqueItems": True}, [{"a": 1}, {"a": 1}], False),
    ("items ok", {"type": "array", "items": {"type": "integer"}}, [1, 2], True),
    ("items bad", {"type": "array", "items": {"type": "integer"}}, [1, "x"], False),
    ("required ok", {"type": "object", "required": ["a"]}, {"a": 1}, True),
    ("required bad", {"type": "object", "required": ["a"]}, {}, False),
    ("properties ok", {"type": "object", "properties": {"a": {"type": "integer"}}}, {"a": 1}, True),
    ("properties bad", {"type": "object", "properties": {"a": {"type": "integer"}}}, {"a": "x"}, False),
    ("additionalProperties false rejects", {"type": "object", "properties": {"a": {}}, "additionalProperties": False}, {"a": 1, "b": 2}, False),
    ("additionalProperties false accepts", {"type": "object", "properties": {"a": {}}, "additionalProperties": False}, {"a": 1}, True),
    ("anyOf ok", {"anyOf": [{"type": "string"}, {"type": "null"}]}, None, True),
    ("anyOf bad", {"anyOf": [{"type": "string"}, {"type": "null"}]}, 1, False),
    ("oneOf exactly one", {"oneOf": [{"type": "string"}, {"type": "integer"}]}, "x", True),
    ("oneOf none", {"oneOf": [{"type": "string"}, {"type": "integer"}]}, None, False),
    ("oneOf two", {"oneOf": [{"type": "integer"}, {"minimum": 0}]}, 3, False),
    ("nested path", {"type": "object", "properties": {"a": {"type": "array", "items": {"type": "string"}}}}, {"a": ["x", 2]}, False),
]


class SchemaValidatorTests(unittest.TestCase):
    def test_known_instances(self):
        self.assertGreaterEqual(len(CASES), 40, "HARN-03 needs at least 40 known instances")
        for name, schema, instance, valid in CASES:
            with self.subTest(name):
                errors = validate(instance, schema)
                self.assertEqual(not errors, valid, f"{name}: {errors}")

    def test_every_supported_keyword_is_exercised(self):
        used = set()
        for _, schema, _, _ in CASES:
            stack = [schema]
            while stack:
                node = stack.pop()
                if isinstance(node, dict):
                    used.update(node)
                    stack += list(node.values())
                elif isinstance(node, list):
                    stack += node
        supported = {"type", "enum", "const", "properties", "required", "additionalProperties", "items", "minItems", "maxItems", "uniqueItems",
                     "minLength", "maxLength", "minimum", "maximum", "pattern", "anyOf", "oneOf"}
        self.assertEqual(supported - used, set(), "a supported keyword has no test")

    def test_errors_never_hold_instance_values(self):
        secret = "SENTINEL_VALUE_0123456789"
        schemas = [{"type": "integer"}, {"enum": ["a"]}, {"const": "x"}, {"type": "string", "maxLength": 3}, {"type": "string", "pattern": "^[0-9]+$"},
                   {"type": "object", "properties": {"k": {"type": "integer"}}}, {"type": "array", "items": {"type": "integer"}}]
        instances = [secret, secret, secret, secret, secret, {"k": secret}, [secret]]
        for schema, instance in zip(schemas, instances):
            errors = validate(instance, schema)
            self.assertTrue(errors, f"{schema} should reject the value")
            self.assertNotIn(secret, json.dumps(errors, ensure_ascii=False))

    def test_refs_within_and_across_files(self):
        store = ContractStore()
        ok = {"memory_id": "mem_1", "version": 1, "author_handle": None, "license": "CC0-1.0"}
        self.assertEqual(validate(ok, {"$ref": "memory.v1.json#/$defs/DerivedFrom"}, store), [])
        self.assertTrue(validate({**ok, "version": 0}, {"$ref": "memory.v1.json#/$defs/DerivedFrom"}, store))
        self.assertTrue(validate({**ok, "extra": 1}, {"$ref": "memory.v1.json#/$defs/DerivedFrom"}, store), "additionalProperties false must reject an unknown field")

    def test_contract_files_are_valid_json_schema_documents(self):
        for path in sorted(CONTRACTS.glob("*.json")):
            with self.subTest(path.name):
                document = json.loads(path.read_text(encoding="utf-8"))
                self.assertIsInstance(document, dict)
        store = ContractStore()
        for name, ref in (("StandardDoc", "memory.v1.json#/$defs/StandardDoc"), ("Form", "memory.v1.json#/$defs/Form")):
            self.assertIsInstance(store.schema(ref.split("#")[0], ref.split("#")[1]), dict, name)


if __name__ == "__main__":
    unittest.main()
