"""Web fetch guard, preview store and search-provider client of the test double (docs/spec/web-import.md sections 2, 3, 5, 7).

The guard validates EVERY resolved address before connecting, connects to the validated IP directly (no second resolution),
re-validates each redirect hop, streams the body under a size cap (compressed bodies are decoded incrementally) and enforces
one wall-clock deadline. It sends no Cookie, Authorization or Referer header.
"""
import contextlib
import fcntl
import http.client
import ipaddress
import json
import os
import re
import socket
import ssl
import time
import zlib
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlsplit

from . import mutation, scrub, urls, vocab
from .errors import DmemError
from .state import iso, new_id, now  # noqa: F401  (now is re-exported: fetch.now())

USER_AGENT = "dmem/0.0.0-double"
ALLOWED_TYPES = {"text/html", "text/markdown", "text/plain", "application/pdf",
                 "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                 "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "text/csv"}
ZIP_TYPES = {t for t in ALLOWED_TYPES if t.startswith("application/vnd.openxmlformats")}
V4_BLOCKED = [ipaddress.ip_network(n) for n in ("0.0.0.0/8", "10.0.0.0/8", "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16", "172.16.0.0/12",
                                                  "192.168.0.0/16", "224.0.0.0/4", "240.0.0.0/4")]
V6_BLOCKED = [ipaddress.ip_network(n) for n in ("::1/128", "::/128", "fc00::/7", "fe80::/10", "ff00::/8")]
NAT64 = ipaddress.ip_network("64:ff9b::/96")


def ip_blocked(ip):
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    if isinstance(addr, ipaddress.IPv6Address):
        if addr.ipv4_mapped is not None:
            return ip_blocked(str(addr.ipv4_mapped))
        if addr in NAT64:
            return ip_blocked(str(ipaddress.IPv4Address(int(addr) & 0xFFFFFFFF)))
        return any(addr in net for net in V6_BLOCKED)
    return any(addr in net for net in V4_BLOCKED)


def resolve(host, isolated=False):
    """Every A/AAAA address of host. DMEM_TEST_RESOLVE ("host=ip1,ip2;host2=ip3") overrides the real resolver."""
    for entry in filter(None, os.environ.get("DMEM_TEST_RESOLVE", "").split(";")):
        name, _, ips = entry.partition("=")
        if name.strip().lower() == host.lower():
            return [i.strip() for i in ips.split(",") if i.strip()]
    try:
        return sorted({info[4][0] for info in socket.getaddrinfo(host, None)})
    except (socket.gaierror, UnicodeError):
        raise DmemError("fetch_failed", reason="dns")


def is_downgrade(current, target):
    """https -> http redirect (web-import.md section 2). Not testable through the http-only loopback fixture, so it is a unit-tested pure function."""
    return urlsplit(current).scheme == "https" and urlsplit(target).scheme == "http"


class FetchResult:
    def __init__(self, status, headers, body, final_url, content_type):
        self.status, self.headers, self.body, self.final_url, self.content_type = status, headers, body, final_url, content_type


def _blocked(reason, hint=None):
    return DmemError("fetch_blocked", reason=reason, input_hint=hint)


def _validate_target(url, isolated):
    """Returns (scheme, host, port, path_with_query, ip). Raises fetch_blocked."""
    parts = urlsplit(url)
    scheme, host = parts.scheme.lower(), (parts.hostname or "")
    if scheme not in ("http", "https") or not host or parts.username or parts.password:
        raise _blocked("scheme", url)
    loopback = host in ("127.0.0.1", "::1", "localhost")
    plain_ok = isolated and loopback
    try:  # a private IP literal is reported as private_address whatever the scheme or port is
        literal = str(ipaddress.ip_address(host))
    except ValueError:
        literal = None
    if literal and not plain_ok and ip_blocked(literal) and mutation() != "ssrf_no_guard":
        raise _blocked("private_address", url)
    if scheme == "http" and not plain_ok and mutation() != "ssrf_no_guard":
        raise _blocked("scheme", url)
    port = parts.port or (443 if scheme == "https" else 80)
    if not plain_ok and port != 443 and mutation() != "ssrf_no_guard":
        raise _blocked("port", url)
    path = (parts.path or "/") + (("?" + parts.query) if parts.query else "")
    if plain_ok:
        return scheme, host, port, path, "127.0.0.1" if host == "localhost" else host
    try:
        ips = [str(ipaddress.ip_address(host))]
    except ValueError:
        ips = resolve(host, isolated)
    if mutation() != "ssrf_no_guard" and any(ip_blocked(ip) for ip in ips):
        raise _blocked("private_address", url)
    if not ips:
        raise DmemError("fetch_failed", reason="dns")
    return scheme, host, port, path, ips[0]


def _connect(scheme, host, port, ip, timeout):
    sock = socket.create_connection((ip, port), timeout=timeout)
    if scheme == "https":
        sock = ssl.create_default_context().wrap_socket(sock, server_hostname=host)
        conn = http.client.HTTPSConnection(host, port, timeout=timeout)
    else:
        conn = http.client.HTTPConnection(host, port, timeout=timeout)
    conn.sock = sock  # we connect to the VALIDATED ip and never resolve again
    return conn


def fetch(url, *, isolated=False, max_bytes=5 * 1024 * 1024, timeout=10.0, max_redirects=3):
    deadline = time.monotonic() + timeout
    current = url
    for hop in range(max_redirects + 1):
        scheme, host, port, path, ip = _validate_target(current, isolated)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise _blocked("timeout")
        conn = None
        try:
            conn = _connect(scheme, host, port, ip, remaining)
            headers = {"Host": host if port in (80, 443) else f"{host}:{port}", "User-Agent": USER_AGENT,
                       "Accept": "text/html,text/markdown,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.*;q=0.9",
                       "Accept-Encoding": "gzip, deflate"}
            conn.request("GET", path, headers=headers)
            resp = conn.getresponse()
            status = resp.status
            rheaders = {k.lower(): v for k, v in resp.getheaders()}
            if 300 <= status < 400 and rheaders.get("location"):
                target = urljoin(current, rheaders["location"])
                if "login" in urlsplit(target).path.lower():
                    raise _blocked("login_required")
                if is_downgrade(current, target):
                    raise _blocked("scheme")
                current = target
                continue
            if status in (401, 403):
                raise _blocked("login_required")
            if status >= 500:
                raise DmemError("fetch_failed", reason="status_5xx")
            if status >= 400:
                raise DmemError("fetch_failed", reason="status_4xx")
            if "noai" in rheaders.get("x-robots-tag", "").lower():
                raise _blocked("signal_noai")
            ctype = rheaders.get("content-type", "").split(";")[0].strip().lower()
            if ctype not in ALLOWED_TYPES:
                raise _blocked("content_type")
            encoding = rheaders.get("content-encoding", "").lower()
            decoder = zlib.decompressobj(16 + zlib.MAX_WBITS) if encoding == "gzip" else zlib.decompressobj() if encoding == "deflate" else None
            body, size = [], 0
            while True:
                if time.monotonic() > deadline:
                    raise _blocked("timeout")
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                try:
                    data = decoder.decompress(chunk, max_bytes + 1 - size) if decoder else chunk
                except zlib.error:
                    raise DmemError("fetch_failed", reason="reset")
                size += len(data)
                if size > max_bytes:
                    raise _blocked("size")
                body.append(data)
                if decoder and decoder.unconsumed_tail:  # more output pending: keep decoding under the cap
                    while decoder.unconsumed_tail:
                        data = decoder.decompress(decoder.unconsumed_tail, max_bytes + 1 - size)
                        size += len(data)
                        if size > max_bytes:
                            raise _blocked("size")
                        body.append(data)
            raw = b"".join(body)
            if ctype in ZIP_TYPES and not raw.startswith(b"PK"):
                raise _blocked("content_type")
            if ctype == "application/pdf" and not raw.startswith(b"%PDF"):
                raise _blocked("content_type")
            if ctype in ("text/html", "text/plain", "text/markdown") and (raw.startswith(b"PK") or raw.startswith(b"%PDF")):
                raise _blocked("content_type")
            if ctype == "text/html" and re.search(rb"<input[^>]+type=[\"']?password", raw, re.I):
                raise _blocked("login_required")
            return FetchResult(status, rheaders, raw, current, ctype)
        except DmemError:
            raise
        except (socket.timeout, TimeoutError):
            raise _blocked("timeout")
        except ssl.SSLError:
            raise DmemError("fetch_failed", reason="tls")
        except socket.gaierror:
            raise DmemError("fetch_failed", reason="dns")
        except (ConnectionError, http.client.HTTPException, OSError):
            raise DmemError("fetch_failed", reason="reset")
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
    raise _blocked("redirect_limit")


class PreviewStore:
    """Short-lived (15 min) preview records under home/previews/<id>.json, mode 0600."""

    TTL = 900

    def __init__(self, home):
        self.dir = Path(home) / "previews"

    def put(self, record):
        self.dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        pid = "pv_" + os.urandom(6).hex()
        path = self.dir / f"{pid}.json"
        fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({"expires_at": now() + self.TTL, "record": record}, handle, ensure_ascii=False)
        return pid

    def get(self, preview_id):
        if not re.fullmatch(r"pv_[0-9a-f]{12}", preview_id or ""):
            raise DmemError("not_found")
        path = self.dir / f"{preview_id}.json"
        if not path.exists() or path.is_symlink():
            raise DmemError("not_found")
        data = json.loads(path.read_text(encoding="utf-8"))
        if now() > data["expires_at"]:
            path.unlink(missing_ok=True)
            raise DmemError("not_found")
        return data["record"]

    def purge(self):
        count = 0
        if self.dir.exists():
            for path in self.dir.glob("pv_*.json"):
                try:
                    if now() > json.loads(path.read_text(encoding="utf-8"))["expires_at"]:
                        path.unlink()
                        count += 1
                except (ValueError, OSError):
                    continue
        return count


def _clean(text, limit):
    text = re.sub(r"<[^>]*>", "", str(text))
    text = "".join(ch for ch in scrub.strip_hidden(text)[0] if ch >= " " and ch != "\x7f")
    return text[:limit]


def web_search(query, provider_spec, limit, locale=None, doc_type=None, provider=None):
    if len(query) > 200:
        raise DmemError("payload_too_large")
    if scrub.has_secret(query):
        raise DmemError("secret_detected")
    kind, _, target = (provider_spec or "none").partition(":")
    if kind not in ("fixture", "http") or not target:
        raise DmemError("search_unavailable")
    params = {"q": query}
    for key, value in (("locale", locale), ("doc_type", doc_type), ("provider", provider)):
        if value:
            params[key] = value
    parts = urlsplit(target)
    try:
        conn = http.client.HTTPConnection(parts.hostname, parts.port or 80, timeout=5) if parts.scheme == "http" else http.client.HTTPSConnection(parts.hostname, parts.port or 443, timeout=5)
        conn.request("GET", (parts.path or "/") + "?" + urlencode(params), headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        resp = conn.getresponse()
        raw = resp.read(1024 * 1024)
        status = resp.status
        retry = resp.getheader("Retry-After")
        conn.close()
    except (OSError, http.client.HTTPException):
        raise DmemError("search_unavailable")
    if status == 429:
        raise DmemError("rate_limited", retry_after_seconds=int(retry) if retry and retry.isdigit() else 60)
    if status >= 400:
        raise DmemError("search_unavailable")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise DmemError("search_unavailable")
    items = data.get("candidates", data.get("results", [])) if isinstance(data, dict) else data
    out, filtered = [], 0
    for item in items if isinstance(items, list) else []:
        try:
            canon = urls.canonicalize(str(item.get("url", "")), isolated=True)
        except DmemError:
            filtered += 1
            continue
        parts = urlsplit(str(item["url"]))
        clean_url = f"{parts.scheme}://{parts.netloc}{parts.path or '/'}"
        lic = item.get("license")
        hint = item.get("locale")
        out.append({"url": clean_url[:2048], "title": _clean(item.get("title", ""), 200), "snippet": _clean(item.get("snippet", ""), 400),
                    "detected": {"provider": canon.provider, "doc_type": None, "locale": hint if hint in vocab.locales() else None},
                    "license_hint": lic if lic in vocab.license_ids() else None})

    def fit(candidate):  # matches come first; the provider's own order breaks ties (sorted() is stable)
        detected = candidate["detected"]
        return (0 if provider and detected["provider"] == provider else 1, 0 if locale and detected["locale"] == locale else 1)
    if provider or locale:
        out.sort(key=fit)
    out = out[:limit]
    for number, candidate in enumerate(out, 1):
        candidate["rank"] = number
    return {"provider": "fixture" if kind == "fixture" else "http", "candidates": out, "filtered": filtered}


class FetchGate:
    """Per-library limits for page fetches (core.md section 8, proposed): 30 per rolling minute and 4 in flight. A refused call changes nothing."""
    PER_MINUTE, IN_FLIGHT = 30, 4

    def __init__(self, home):
        self.path = Path(home) / "fetch-gate.json"

    @contextlib.contextmanager
    def _locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with open(str(self.path) + ".lock", "a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                data = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
            except (ValueError, OSError):
                data = {}
            yield data
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data), encoding="utf-8")
            os.replace(tmp, self.path)

    @staticmethod
    def _alive(pid):
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    @contextlib.contextmanager
    def slot(self):
        stamp = now()
        with self._locked() as data:
            recent = [x for x in data.get("stamps", []) if x > stamp - 60]
            flying = [p for p in data.get("flight", []) if self._alive(p[0]) and p[1] > stamp - 30]
            data["stamps"], data["flight"] = recent, flying
            if len(recent) >= self.PER_MINUTE or len(flying) >= self.IN_FLIGHT:
                refused = True
            else:
                refused = False
                recent.append(stamp)
                flying.append([os.getpid(), stamp])
        if refused:
            raise DmemError("rate_limited", retry_after_seconds=60)
        try:
            yield
        finally:
            with self._locked() as data:
                data["flight"] = [p for p in data.get("flight", []) if p[0] != os.getpid()]
