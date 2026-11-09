"""URL canonicalization for the My Document Memory test double (stdlib only)."""
import base64
import hashlib
import hmac
import ipaddress
import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import unquote_to_bytes, urlsplit, urlunsplit

from . import mutation
from .errors import DmemError
from .vocab import provider_for_extension


@dataclass(frozen=True)
class Canonical:
    pattern: str
    provider: str
    host: str
    fetch_url: str | None = None


_GOOGLE_ROUTES = {
    "document": "google_docs",
    "presentation": "google_slides",
    "spreadsheets": "google_sheets",
}
_GOOGLE_TAILS = {"edit", "view", "preview", "copy", "export", "template"}
_ISOLATED_ALIASES = {
    "google-docs": ("docs.google.com", "google_docs"),
    "google-slides": ("docs.google.com", "google_slides"),
    "google-sheets": ("docs.google.com", "google_sheets"),
    "google-sheets-csv": ("docs.google.com", "google_sheets"),  # fixture variant whose export offers CSV only
    "notion": ("www.notion.so", "notion"),
}
_HEX32 = re.compile(r"^[0-9a-fA-F]{32}$")
_SLUG_HEX32 = re.compile(r"^.*-([0-9a-fA-F]{32})$")
_UUID = re.compile(r"^[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$")
_DNS_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def _reject(reason):
    raise DmemError("url_rejected", reason=reason)


def _ipv4_number(part):
    """Parse one WHATWG-style IPv4 number, including hex and legacy octal."""
    if not part:
        return None
    if part.lower().startswith("0x"):
        digits, base = part[2:], 16
        if not digits:
            return 0
    elif len(part) > 1 and part.startswith("0"):
        digits, base = part[1:], 8
        if not digits:
            return 0
    else:
        digits, base = part, 10
    try:
        return int(digits, base)
    except ValueError:
        return None


def _looks_like_ipv4(host):
    """Recognize IP literals accepted by browsers, not just dotted decimal."""
    pieces = host.split(".")
    # Invalid all-numeric authorities are rejected too: browsers treat these as
    # malformed IPv4 candidates rather than as ordinary DNS names.
    numericish = all(
        piece and (
            all("0" <= ch <= "9" for ch in piece)
            or (piece.lower().startswith("0x") and all(ch in "0123456789abcdefABCDEF" for ch in piece[2:]))
        )
        for piece in pieces
    )
    if not pieces or len(pieces) > 4:
        return numericish
    numbers = [_ipv4_number(piece) for piece in pieces]
    return numericish or all(number is not None for number in numbers)


def _is_ip_literal(host):
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return _looks_like_ipv4(host)


def _normalize_host(host):
    host = host[:-1] if host.endswith(".") else host
    try:
        normalized = host.encode("idna").decode("ascii").lower()
    except (UnicodeError, ValueError):
        _reject("host_not_allowed")
    if not normalized or _is_ip_literal(normalized):
        _reject("host_not_allowed")
    if ":" in normalized or any(not _DNS_LABEL.fullmatch(label) for label in normalized.split(".")):
        _reject("host_not_allowed")
    if "." not in normalized or normalized == "localhost":
        _reject("host_not_allowed")
    private_suffixes = (
        ".localhost", ".local", ".internal", ".lan", ".home", ".localdomain",
    )
    metadata_names = {
        "metadata.google.internal", "metadata.azure.com", "metadata.tencentyun.com",
        "metadata.oraclecloud.com", "instance-data.ec2.internal",
    }
    if normalized.endswith(private_suffixes) or normalized in metadata_names:
        _reject("host_not_allowed")
    return normalized


def _fixed_word(segment):
    return (
        len(segment) <= 40
        and all(ch.isalnum() or ch in "._~-" for ch in segment)
    )


def _generic_segment(segment):
    if segment in {":id", ":handle"}:
        return segment
    if "@" in segment and "." in segment:
        _reject("pii_in_url")
    if segment.startswith("@"):
        return ":handle"
    if segment and all("0" <= ch <= "9" for ch in segment):
        return ":id"
    if _UUID.fullmatch(segment) or (
        len(segment) >= 16 and all(ch in "0123456789abcdefABCDEF" for ch in segment)
    ):
        return ":id"
    if "-" in segment:
        slug, suffix = segment.rsplit("-", 1)
        if slug and (
            (len(suffix) >= 8 and all(ch in "0123456789abcdefABCDEF" for ch in suffix))
            or (len(suffix) >= 4 and all("0" <= ch <= "9" for ch in suffix))
        ):
            return ":id"
    if (
        len(segment) >= 20
        and all(ch.isascii() and (ch.isalnum() or ch in "_-") for ch in segment)
        and any(ch.isascii() and ch.isalpha() for ch in segment)
        and any("0" <= ch <= "9" for ch in segment)
    ):
        return ":id"
    if _fixed_word(segment):
        return segment.lower()
    return None


def _path_parts(path):
    try:
        decoded = unquote_to_bytes(path).decode("utf-8")
    except UnicodeDecodeError:
        _reject("unclassifiable")
    decoded = unicodedata.normalize("NFKC", decoded)
    return [part for part in decoded.split("/") if part]


def _classify(host, parts):
    """Return (provider id, provider-special output, leaked ID if mutated)."""
    if host == "docs.google.com" and parts:
        route = parts[0].lower()
        provider = _GOOGLE_ROUTES.get(route)
        if provider:
            parts = list(parts)
            if len(parts) >= 3 and parts[1].lower() == "u" and parts[2].isascii() and parts[2].isdigit():
                del parts[1:3]
            out = [route]
            leaked_id = None
            if len(parts) >= 3 and parts[1].lower() == "d":
                leaked_id = parts[2]
                out.extend(("d", ":id"))
                if len(parts) >= 4 and parts[3].lower() in _GOOGLE_TAILS:
                    out.append(parts[3].lower())
            return provider, out, leaked_id
        return "other", None, None

    notion_host = host in {"notion.so", "www.notion.so"} or host.endswith(".notion.site")
    if notion_host:
        if parts:
            last = parts[-1]
            match = _SLUG_HEX32.fullmatch(last)
            if _HEX32.fullmatch(last):
                return "notion", [":id"], last
            if match:
                return "notion", [":id"], match.group(1)
            if last == ":id":
                return "notion", [":id"], None
        return "notion", [], None

    provider = "other"
    if parts and "." in parts[-1]:
        extension = "." + parts[-1].rsplit(".", 1)[-1].lower()
        provider = provider_for_extension(extension) or "other"

    # Capability links have route-specific IDs that are not always long or
    # random-looking enough for the generic dynamic-segment rules.
    on_domain = lambda domain: host == domain or host.endswith("." + domain)
    leaked_id = None
    if host == "drive.google.com":
        if len(parts) >= 3 and parts[0].lower() == "file" and parts[1].lower() == "d":
            return provider, ["file", "d", ":id"], parts[2]
        if len(parts) >= 3 and parts[0].lower() == "drive" and parts[1].lower() == "folders":
            return provider, ["drive", "folders", ":id"], parts[2]
        return provider, [], None
    if on_domain("canva.com") or on_domain("figma.com"):
        allowed_routes = {"file", "design", "proto", "board"}
        if len(parts) >= 2 and parts[0].lower() in allowed_routes:
            return provider, [parts[0].lower(), ":id"], parts[1]
        return provider, [], None
    if on_domain("dropbox.com"):
        if len(parts) >= 2 and parts[0].lower() == "s":
            return provider, ["s", ":id"], parts[1]
        if len(parts) >= 3 and parts[0].lower() == "scl" and parts[1].lower() == "fi":
            return provider, ["scl", "fi", ":id"], parts[2]
        return provider, [], None
    if (
        host in {"onedrive.live.com", "1drv.ms"}
        or on_domain("sharepoint.com")
    ):
        return provider, [], None
    return provider, None, None


def _canonical_path(host, parts, provider, special):
    if special is not None:
        output = special
    else:
        output = []
        for part in parts:
            normalized = _generic_segment(part)
            if normalized is None:
                break
            output.append(normalized)
            if len(output) == 8:
                break
    return f"{host}/{'/'.join(output)}", output


def canonicalize(url, isolated=False):
    """Normalize a URL according to docs/spec/core.md sections 2, 3, 4, 8 and 9."""
    if not isinstance(url, str):
        _reject("unclassifiable")
    if len(url) > 2048:
        _reject("too_long")
    normalized = unicodedata.normalize("NFKC", url)
    try:
        parsed = urlsplit(normalized)
    except ValueError:
        _reject("unclassifiable")
    scheme = parsed.scheme.lower()
    if not scheme:
        _reject("unclassifiable")

    # Scheme policy precedes userinfo policy. HTTP is a scheme exception only
    # for the exact loopback authorities named by the isolated-mode contract.
    candidate_host = parsed.hostname
    candidate_host = candidate_host[:-1] if candidate_host and candidate_host.endswith(".") else candidate_host
    isolated_loopback = (
        isolated
        and scheme == "http"
        and candidate_host is not None
        and candidate_host.lower() in {"127.0.0.1", "::1", "localhost"}
    )
    if scheme != "https" and not isolated_loopback:
        _reject("scheme_not_allowed")
    if "@" in parsed.netloc:
        _reject("userinfo_not_allowed")
    if not parsed.netloc or parsed.hostname is None:
        if scheme != "https":
            _reject("scheme_not_allowed")
        _reject("host_not_allowed")

    raw_host = parsed.hostname
    try:
        port = parsed.port
    except ValueError:
        _reject("host_not_allowed")
    if parsed.netloc.endswith(":"):
        _reject("host_not_allowed")

    raw_host_normalized = raw_host[:-1] if raw_host.endswith(".") else raw_host

    if isolated_loopback:
        if port is None and ":" in parsed.netloc and not parsed.netloc.startswith("["):
            _reject("host_not_allowed")
        host = "fixture.test"
    else:
        if _is_ip_literal(raw_host_normalized.lower()):
            _reject("host_not_allowed")
        host = _normalize_host(raw_host)
        if port not in (None, 443):
            _reject("host_not_allowed")

    parts = _path_parts(parsed.path)
    if isolated_loopback and len(parts) >= 2 and parts[0].lower() == "p":
        alias = _ISOLATED_ALIASES.get(parts[1].lower())
        if alias:
            host, _ = alias
            parts = parts[2:]

    provider, special, leaked_id = _classify(host, parts)
    pattern, output = _canonical_path(host, parts, provider, special)

    active_mutation = mutation()
    if active_mutation == "capability_leak" and leaked_id is not None:
        pattern = pattern.replace(":id", leaked_id, 1)
    if active_mutation == "leak_query":
        try:
            original_query = urlsplit(url).query
        except ValueError:
            original_query = ""
        if original_query:
            pattern += "?" + original_query

    fetch_url = None
    if isolated_loopback:
        try:
            original = urlsplit(url)
            fetch_url = urlunsplit((original.scheme, original.netloc, original.path, "", ""))
        except ValueError:
            fetch_url = None
    return Canonical(pattern=pattern, provider=provider, host=host, fetch_url=fetch_url)


def is_canonical(text):
    """Check that a canonical pattern is already in its stable serialized form."""
    if not isinstance(text, str) or "://" in text or "\\" in text:
        return False
    if not text or not text.endswith("/") and "/" not in text:
        return False
    host, separator, path = text.partition("/")
    if not separator or not host or host != host.lower() or host.endswith("."):
        return False
    if not all(_DNS_LABEL.fullmatch(label) for label in host.split(".")):
        return False
    if path:
        segments = path[:-1].split("/") if path.endswith("/") else path.split("/")
        if any(not segment for segment in segments):
            return False
        if any(
            segment not in {":id", ":handle"}
            and (segment.lower() != segment or not _fixed_word(segment))
            for segment in segments
        ):
            return False
    try:
        return canonicalize("https://" + text).pattern == text
    except DmemError:
        return False


def source_ref(canonical_url_without_query, library_key):
    digest = hmac.new(library_key, canonical_url_without_query.encode("utf-8"), hashlib.sha256).digest()
    token = base64.b32encode(digest).decode("ascii").lower().rstrip("=")
    return "src_" + token[:26]


def is_capability_host(host):
    if not isinstance(host, str):
        return False
    normalized = host.rstrip(".").lower()
    exact = {
        "docs.google.com", "www.docs.google.com", "drive.google.com", "www.drive.google.com",
        "notion.so", "www.notion.so", "dropbox.com", "www.dropbox.com",
        "onedrive.live.com", "www.onedrive.live.com", "1drv.ms", "www.1drv.ms",
        "canva.com", "www.canva.com", "figma.com", "www.figma.com",
    }
    if normalized in exact:
        return True
    return (
        normalized.endswith(".notion.site")
        or normalized.endswith(".sharepoint.com")
        or normalized.endswith(".canva.com")
        or normalized.endswith(".figma.com")
    )
