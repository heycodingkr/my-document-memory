"""JSON Schema subset validator for contract tests (independent of the double's own validator).

Supported: type (name or list), enum, const, properties, required, additionalProperties (bool), items, minItems, maxItems,
uniqueItems, minLength, maxLength, minimum, maximum, pattern, anyOf, oneOf, $ref ('#/...' and 'file.json#/...'). Error strings
never contain instance values (HARN-03).
"""
import json
import re
from pathlib import Path

CONTRACTS = Path(__file__).resolve().parents[3] / "contracts"


class ContractStore:
    def __init__(self, base=CONTRACTS):
        self.base = Path(base)
        self._files = {}

    def file(self, name):
        if name not in self._files:
            self._files[name] = json.loads((self.base / name).read_text(encoding="utf-8"))
        return self._files[name]

    def schema(self, file, pointer=""):
        node = self.file(file)
        for part in [p for p in pointer.lstrip("#").split("/") if p]:
            node = node[part]
        return node

    def tool(self, name):
        for t in self.file("mcp-tools.v1.json")["tools"] + self.file("mcp-tools.v1.json").get("wrapper_tools", []):
            if t["name"] == name:
                return t
        raise KeyError(name)

    def result_schema(self, tool_name):
        t = self.tool(tool_name)
        return {"$ref": t["result"], "__file": "mcp-tools.v1.json"}

    def resolve(self, ref, current_file):
        name, _, pointer = ref.partition("#")
        file = name or current_file
        return self.schema(file, pointer), file


def _is(value, name):
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name == "string":
        return isinstance(value, str)
    if name == "boolean":
        return isinstance(value, bool)
    if name == "object":
        return isinstance(value, dict)
    if name == "array":
        return isinstance(value, list)
    if name == "null":
        return value is None
    return False


def validate(instance, schema, store=None, current_file="mcp-tools.v1.json", path="$"):
    """Return a list of error strings (empty = valid)."""
    store = store or ContractStore()
    if "__file" in schema:
        current_file = schema["__file"]
    errors = []
    if "$ref" in schema:
        node, file = store.resolve(schema["$ref"], current_file)
        return validate(instance, node, store, file, path)
    if "anyOf" in schema and not any(not validate(instance, s, store, current_file, path) for s in schema["anyOf"]):
        errors.append(f"{path}: no anyOf branch matches")
    if "oneOf" in schema:
        n = sum(1 for s in schema["oneOf"] if not validate(instance, s, store, current_file, path))
        if n != 1:
            errors.append(f"{path}: {n} oneOf branches match")
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: const mismatch")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: not in enum")
    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_is(instance, n) for n in names):
            errors.append(f"{path}: wrong type")
            return errors
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: too short")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{path}: too long")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: pattern mismatch")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: below minimum")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: above maximum")
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: too few items")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: too many items")
        if schema.get("uniqueItems") and len({json.dumps(i, sort_keys=True) for i in instance}) != len(instance):
            errors.append(f"{path}: duplicate items")
        if "items" in schema:
            for i, item in enumerate(instance):
                errors += validate(item, schema["items"], store, current_file, f"{path}[{i}]")
    if isinstance(instance, dict):
        props = schema.get("properties", {})
        errors += [f"{path}: missing required key" for k in schema.get("required", []) if k not in instance]
        if schema.get("additionalProperties") is False:
            errors += [f"{path}: unknown property" for k in instance if k not in props]
        for key, sub in props.items():
            if key in instance:
                errors += validate(instance[key], sub, store, current_file, f"{path}.{key}")
    return errors
