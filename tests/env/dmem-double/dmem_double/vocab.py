"""Closed vocabularies loaded from /contracts/vocab (the single source of truth shared with the product)."""
import json
import unicodedata
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CONTRACTS = ROOT / "contracts"


def norm(text):
    """NFKC, lowercase, collapse whitespace (alias matching key)."""
    return " ".join(unicodedata.normalize("NFKC", str(text)).lower().split())


@lru_cache(maxsize=None)
def _load(name):
    return json.loads((CONTRACTS / "vocab" / name).read_text(encoding="utf-8"))


# ---- doc types ------------------------------------------------------------------------------
def doc_types():
    return _load("doc_types.json")["items"]


def doc_type_lookup(text):
    """Return (canonical_id, implied_variant_or_None) or None when the text is not in the vocabulary."""
    key = norm(text)
    for item in doc_types():
        if key == item["id"]:
            return item["id"], None
        for alias in item.get("aliases", []):
            if norm(alias["value"]) == key:
                return item["id"], alias.get("variant")
        for label in item.get("labels", {}).values():
            if norm(label) == key:
                return item["id"], None
    return None


def doc_type_known(doc_type_id):
    return doc_type_id is None or any(item["id"] == doc_type_id for item in doc_types())


def doc_type_family(doc_type_id):
    for item in doc_types():
        if item["id"] == doc_type_id:
            return item.get("family")  # None for "other"
    return None


# ---- locales / regions ----------------------------------------------------------------------
def locales():
    return list(_load("regions.json")["locales"])


def regions():
    return list(_load("regions.json")["regions"])


def region_profile(region):
    return _load("region_profiles.json")["profiles"].get(region)


# ---- licenses -------------------------------------------------------------------------------
def licenses():
    return _load("licenses.json")["items"]


def license_ids():
    return [i["id"] for i in licenses()]


def license(license_id):
    for item in licenses():
        if item["id"] == license_id:
            return item
    return None


# ---- keywords -------------------------------------------------------------------------------
def keywords():
    return _load("keywords.json")["items"]


def keyword_canonical(text):
    """Alias -> canonical keyword id, or None when the word is outside the public vocabulary."""
    key = norm(text)
    for item in keywords():
        if key == item["id"] or key in (norm(a) for a in item.get("aliases", [])):
            return item["id"]
    return None


# ---- providers ------------------------------------------------------------------------------
def providers():
    return _load("providers.json")["items"]


def provider_ids():
    return [p["id"] for p in providers()]


def provider_family(provider_id):
    for p in providers():
        if p["id"] == provider_id:
            return p["family"]
    return None


def provider_for_extension(ext):
    ext = ext.lower()
    for p in providers():
        if ext in p.get("extensions", []):
            return p["id"]
    return None


def vocab_versions():
    return {
        "doc_types": str(_load("doc_types.json")["version"]),
        "regions": str(_load("regions.json")["version"]),
        "licenses": str(_load("licenses.json")["version"]),
        "keywords": str(_load("keywords.json")["version"]),
    }
