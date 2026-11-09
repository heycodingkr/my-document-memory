"""A small JSON Schema subset validator used by the double to validate tool inputs against contracts/mcp-tools.v1.json.

Supported keywords: type (name or list), enum, const, properties, required, additionalProperties (bool), items, minItems,
maxItems, uniqueItems, minLength, maxLength, minimum, maximum, pattern, anyOf, oneOf, $ref (local '#/...' and
'file.json#/...' relative to the contracts directory). Error strings never contain instance values.
"""
import json
import re

from .vocab import CONTRACTS

_TYPES = {"string": str, "boolean": bool, "object": dict, "array": list, "null": type(None)}


def _is(value, name):
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name == "string":
        return isinstance(value, str)
    return isinstance(value, _TYPES[name]) and not (name != "boolean" and isinstance(value, bool) and name in ("object", "array"))


class Contracts:
    def __init__(self, base=CONTRACTS):
        self.base = base
        self._files = {}

    def file(self, name):
        if name not in self._files:
            self._files[name] = json.loads((self.base / name).read_text(encoding="utf-8"))
        return self._files[name]

    def resolve(self, ref, current):
        name, _, pointer = ref.partition("#")
        doc = self.file(name) if name else current
        node = doc
        for part in [p for p in pointer.split("/") if p]:
            node = node[part]
        return node, doc


def validate(instance, schema, contracts=None, current=None, path="$"):
    contracts = contracts or Contracts()
    current = current if current is not None else contracts.file("mcp-tools.v1.json")
    errors = []
    if "$ref" in schema:
        node, doc = contracts.resolve(schema["$ref"], current)
        return validate(instance, node, contracts, doc, path)
    if "anyOf" in schema:
        if not any(not validate(instance, s, contracts, current, path) for s in schema["anyOf"]):
            errors.append(f"{path}: no anyOf branch matches")
    if "oneOf" in schema:
        matches = sum(1 for s in schema["oneOf"] if not validate(instance, s, contracts, current, path))
        if matches != 1:
            errors.append(f"{path}: {matches} oneOf branches match")
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
                errors += validate(item, schema["items"], contracts, current, f"{path}[{i}]")
    if isinstance(instance, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: missing required key")
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in props:
                    errors.append(f"{path}: unknown property")
        for key, sub in props.items():
            if key in instance:
                errors += validate(instance[key], sub, contracts, current, f"{path}.{key}")
    return errors


def inline(schema, contracts=None, current=None):
    """Resolve every $ref so the schema is self-contained (what a tools/list outputSchema must be)."""
    contracts = contracts or Contracts()
    current = current if current is not None else contracts.file("mcp-tools.v1.json")
    if isinstance(schema, dict):
        if "$ref" in schema:
            node, doc = contracts.resolve(schema["$ref"], current)
            return inline(node, contracts, doc)
        return {k: inline(v, contracts, current) for k, v in schema.items()}
    if isinstance(schema, list):
        return [inline(v, contracts, current) for v in schema]
    return schema
