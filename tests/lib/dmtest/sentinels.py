"""Deterministic synthetic sentinels and a scanner that never prints the values it finds (HARN-04, docs/test/fixtures.md section 6).

    python3 -B -m dmtest.sentinels --write      regenerate tests/sentinels.json (seed dmem-sentinels-v1)

Every sentinel is invalid by construction (reserved domains, zero-filled national ids, test card numbers). The scanner searches
literal, JSON-escaped, percent-encoded, base64, base64url and hex variants and reports (sentinel id, path, variant) only.
"""
import base64
import hashlib
import json
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SEED = "dmem-sentinels-v1"
PATH = ROOT / "tests" / "sentinels.json"
PER_FAMILY = 6


def _digest(*parts):
    return hashlib.sha256((SEED + "|" + "|".join(map(str, parts))).encode()).hexdigest()


def _alnum(n, *parts):
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"
    raw = int(_digest(*parts), 16)
    out = ""
    while len(out) < n:
        raw, r = divmod(raw, len(alphabet))
        out += alphabet[r]
        if raw == 0:
            raw = int(_digest(*parts, len(out)), 16)
    return out


def _gen(family, i):
    d = _digest(family, i)
    if family == "api_key":
        return ["sk-test-" + _alnum(32, family, i), "AKIA" + _alnum(16, family, i).upper(), "ghp_" + _alnum(36, family, i)][i % 3]
    if family == "jwt":
        b = lambda s: base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")
        return f"eyJ{b('hdr' + d[:8])[:10]}.eyJ{b('pay' + d[8:16])[:14]}.{_alnum(22, family, i)}"
    if family == "bearer":
        return "Bearer " + _alnum(28, family, i)
    if family == "private_key":
        return f"-----BEGIN PRIVATE KEY-----\n{_alnum(40, family, i)}\n-----END PRIVATE KEY-----"
    if family == "email":
        return f"user{d[:6]}@example.test"
    if family == "phone":
        return ["010-0000-%04d" % (int(d[:4], 16) % 10000), "+1 (555) 010-%04d" % (int(d[:4], 16) % 100 + 100), "090-0000-%04d" % (int(d[:4], 16) % 10000)][i % 3]
    if family == "national_id":
        return ["000000-0000000", "000-00-0000"][i % 2]
    if family == "card":
        return "4111 1111 1111 1111"
    if family == "account":
        return "DE00 0000 0000 0000 0000 00"
    if family == "capability":
        return "GDOC_ID_SENTINEL_" + _alnum(24, family, i) if i % 2 == 0 else "RK_SENTINEL_" + _alnum(12, family, i)
    if family == "url_parts":
        return ["Q_SENTINEL_", "F_SENTINEL_", "USERINFO_SENTINEL_"][i % 3] + _alnum(10, family, i)
    if family == "prose":
        return f"PROSE_SENTINEL_{i + 1}" if i < 5 else "L2_ONLY_SENTINEL"
    if family == "hidden":
        return f"HIDDEN_SENTINEL_{i % 3 + 1}"
    raise KeyError(family)


FAMILIES = ["api_key", "jwt", "bearer", "private_key", "email", "phone", "national_id", "card", "account", "capability", "url_parts", "prose", "hidden"]
# Families whose values are deliberately the same well-known invalid constants are listed once; the rest have PER_FAMILY values.


def generate():
    items = []
    for family in FAMILIES:
        seen = set()
        for i in range(PER_FAMILY):
            value = _gen(family, i)
            if value in seen:
                continue
            seen.add(value)
            items.append({"id": f"{family}-{len(seen):02d}", "family": family, "value": value})
    return {"seed": SEED, "families": FAMILIES, "items": items}


def write():
    PATH.write_text(json.dumps(generate(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


class Sentinels:
    def __init__(self, data):
        self.items = data["items"]

    def value(self, family, n=1):
        return [i["value"] for i in self.items if i["family"] == family][n - 1]

    def ids(self):
        return [i["id"] for i in self.items]

    def of(self, family):
        return [i["value"] for i in self.items if i["family"] == family]


def load(path=PATH):
    return Sentinels(json.loads(Path(path).read_text(encoding="utf-8")))


def variants(value):
    raw = value.encode("utf-8")
    out = {"literal": [raw], "json": [json.dumps(value, ensure_ascii=True)[1:-1].encode(), json.dumps(value, ensure_ascii=False)[1:-1].encode()],
           "percent": [urllib.parse.quote(value, safe="").encode(), urllib.parse.quote_plus(value).encode()],
           "base64": [base64.b64encode(raw).rstrip(b"=")], "base64url": [base64.urlsafe_b64encode(raw).rstrip(b"=")], "hex": [raw.hex().encode()]}
    return out


class Finding:
    def __init__(self, sentinel_id, path, variant):
        self.sentinel_id, self.path, self.variant = sentinel_id, str(path), variant

    def __repr__(self):  # never the value
        return f"Finding({self.sentinel_id}, {self.path}, {self.variant})"


def _chunks(source):
    """Yield (label, bytes) for files, directories (recursively, symlinks skipped) and raw byte strings."""
    if isinstance(source, (bytes, bytearray)):
        yield "<bytes>", bytes(source)
    elif isinstance(source, str) and not Path(source).exists():
        yield "<text>", source.encode("utf-8")
    else:
        p = Path(source)
        if p.is_symlink():
            return
        if p.is_dir():
            for child in sorted(p.rglob("*")):
                if child.is_file() and not child.is_symlink():
                    yield from _chunks(child)
        elif p.is_file():
            yield str(p), p.read_bytes()


def scan(sources, sentinels, families=None, use_variants=True):
    """Return [Finding]. `sources` is an iterable of paths, bytes or text. The values are never returned or printed."""
    sources = [sources] if isinstance(sources, (str, bytes, Path)) else list(sources)
    findings = []
    wanted = [i for i in sentinels.items if not families or i["family"] in families]
    for source in sources:
        for label, blob in _chunks(source):
            for item in wanted:
                forms = variants(item["value"]) if use_variants else {"literal": [item["value"].encode()]}
                for kind, needles in forms.items():
                    if any(n and n in blob for n in needles):
                        findings.append(Finding(item["id"], label, kind))
                        break
    return findings


if __name__ == "__main__":
    if "--write" in sys.argv:
        write()
        print(f"wrote {PATH.relative_to(ROOT)} ({len(generate()['items'])} sentinels)")
