import json
from html.parser import HTMLParser
from urllib.parse import urlparse
from . import vocab
from .errors import DmemError

_MODES = ("full", "quote_limited", "structure_only")


def copy_policy_for(license_id, origin, license_source, unverified):
    if origin == "user": return "full"
    item = vocab.license(license_id) or vocab.license("unknown")
    # license_id is the effective id after any asserted/detected conflict is resolved.
    return item["copy_policy_max"]


def republish_allowed(license_id, target_license):
    item = vocab.license(license_id)
    return bool(item and (item["republish"] == "allowed" or
        item["republish"] == "same_license" and target_license == license_id))


def apply_copy_mode(requested, max_policy):
    if max_policy not in _MODES: max_policy = "structure_only"
    allowed = list(_MODES[_MODES.index(max_policy):])
    mode = max_policy if requested is None else requested
    if mode not in allowed:
        raise DmemError("license_forbids", extra={"allowed_modes": allowed}, input_hint=mode)
    return mode


def _json_license(text):
    try: value = json.loads(text)
    except (ValueError, TypeError): return []
    found = []
    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.lower() == "license": found.extend(v if isinstance(v, list) else [v])
                else: walk(v)
        elif isinstance(obj, list):
            for v in obj: walk(v)
    walk(value)
    return [v for v in found if isinstance(v, str)]


class _HTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.metas, self.jsonld, self.parts = [], [], [], []
        self.in_json = False
    def handle_starttag(self, tag, attrs):
        a = {k.lower(): v for k, v in attrs if v is not None}
        if tag == "link" and "license" in a.get("rel", "").lower().split(): self.links.append(a.get("href", ""))
        if tag == "meta" and a.get("name", "").lower() == "license": self.metas.append(a.get("content", ""))
        if tag == "script" and "ld+json" in a.get("type", "").lower(): self.in_json, self.parts = True, []
    def handle_data(self, data):
        if self.in_json: self.parts.append(data)
    def handle_endtag(self, tag):
        if tag == "script" and self.in_json:
            self.jsonld.extend(_json_license("".join(self.parts)))
            self.in_json = False


def _map_license(value):
    value = value.strip()
    for item in vocab.licenses():
        if value == item["id"] or value.lower().rstrip("/") in {u.lower().rstrip("/") for u in item.get("urls", [])}:
            return item["id"]
    parsed = urlparse(value)
    host, path = (parsed.hostname or "").lower(), parsed.path.lower().strip("/")
    if host.endswith("creativecommons.org"):
        return {"publicdomain/zero/1.0": "CC0-1.0",
                "licenses/by/4.0": "CC-BY-4.0",
                "licenses/by-sa/4.0": "CC-BY-SA-4.0"}.get(path, "proprietary-structure-only")
    return "proprietary-structure-only"


def detect_license(html_text):
    parser = _HTML()
    parser.feed(html_text or "")
    signals = parser.links + parser.metas + parser.jsonld
    if not signals: return "unknown", "none"
    mapped = [_map_license(x) for x in signals]
    if "proprietary-structure-only" in mapped: return "proprietary-structure-only", "detected"
    allowed = {"CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0", "MIT", "Apache-2.0"}
    return next((x for x in mapped if x in allowed), "proprietary-structure-only"), "detected"
