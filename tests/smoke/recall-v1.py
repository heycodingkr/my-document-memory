#!/usr/bin/env python3
"""Black-box smoke for recall v1 (docs/spec/recall-v1.md, cases RV-* in docs/test/recall-v1.md).

Starts the real `dmem-server` in an EMPTY temporary working directory (so it can never read a real credentials/ folder) on a free
loopback port with a temporary database, then drives it over HTTP, the real `dmem` CLI and the real `dmem-mcp` stdio server.
Prints only case ids, counts and fixed codes; sentinel values are never printed.

    cargo build --workspace && python3 -I tests/smoke/recall-v1.py        # uses target/debug (override: DMEM_BIN_DIR=...)

Exit code 0 only when every check passes.
"""
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
BIN = Path(os.environ.get("DMEM_BIN_DIR") or ROOT / "target/debug")
for name in ["dmem-server", "dmem", "dmem-mcp"]:
    if not (BIN / name).is_file():
        raise SystemExit("Run cargo build --workspace first.")
sys.path[:0] = [str(ROOT / "tests" / "lib"), str(ROOT / "tests" / "env" / "dmem-double")]
from dmtest import sentinels as S  # noqa: E402
from dmem_double import jsonschema_lite as J  # noqa: E402

RESULTS = []
BODIES = []  # every byte string the product produced; scanned for sentinel leaks at the end


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + ((" :: " + detail) if (detail and not ok) else ""), flush=True)


with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    PORT = sock.getsockname()[1]
TMP = tempfile.mkdtemp(prefix="dmem-recall-smoke-")
TOKEN = "smoke-" + secrets.token_hex(12)
BASE = f"http://127.0.0.1:{PORT}"
ENV = {"PATH": os.environ.get("PATH", ""), "HOME": TMP, "DMEM_URL": BASE, "DMEM_TOKEN": TOKEN}
LOG = open(os.path.join(TMP, "server.log"), "wb")
SERVER = subprocess.Popen([str(BIN / "dmem-server")], cwd=TMP, stdout=LOG, stderr=LOG,
                          env={**ENV, "DMEM_ADDR": f"127.0.0.1:{PORT}", "DMEM_DATABASE": os.path.join(TMP, "db.sqlite3")})


def api(method, path, body=None, token=TOKEN, scan=True):
    data = None if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
    req = urllib.request.Request(BASE + path, method=method, data=data)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw, status = r.read(), r.status
    except urllib.error.HTTPError as e:
        raw, status = e.read(), e.code
    if scan:  # template CRUD legitimately echoes what the user stored, so only recall/status bodies are leak-scanned
        BODIES.append(raw)
    try:
        return status, json.loads(raw), raw
    except ValueError:
        return status, None, raw


def cli(*a, env=None, stdin=None):
    p = subprocess.run([str(BIN / "dmem"), *a], env=env or ENV, input=stdin, capture_output=True, timeout=40, cwd=TMP)
    BODIES.extend([p.stdout, p.stderr])
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


class Mcp:
    def __init__(self, env=None):
        self.p = subprocess.Popen([str(BIN / "dmem-mcp")], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, env=env or ENV, cwd=TMP)
        self.n = 0

    def rpc(self, method, params=None):
        self.n += 1
        msg = {"jsonrpc": "2.0", "id": self.n, "method": method}
        if params is not None:
            msg["params"] = params
        self.p.stdin.write((json.dumps(msg) + "\n").encode())
        self.p.stdin.flush()
        line = self.p.stdout.readline()
        BODIES.append(line)
        return json.loads(line)

    def call(self, name, arguments):
        res = self.rpc("tools/call", {"name": name, "arguments": arguments})["result"]
        return res["isError"], json.loads(res["content"][0]["text"])

    def close(self):
        try:
            self.p.stdin.close()
            self.p.wait(timeout=5)
        except Exception:  # noqa: BLE001
            self.p.kill()
        BODIES.append(self.p.stderr.read())


def wait_ready():
    for _ in range(100):
        if SERVER.poll() is not None:
            return False
        try:
            if api("GET", "/v1/status")[0] == 200:
                return True
        except OSError:
            pass
        time.sleep(0.2)
    return False


def tpl(title, doc_type="meeting_minutes", locale="ko-KR", provider="docx", sections=None, tags=None, summary="요약"):
    return {"title": title, "summary": summary, "form": {"provider": provider, "doc_type": doc_type, "locale": locale},
            "sections": sections or ["개요", "본문", "결론"], "tags": tags or []}


def make(**kw):
    st, js, _ = api("POST", "/v1/templates", tpl(**kw), scan=False)
    assert st in (200, 201), (st, js)
    return js


def q(path, **params):
    parts = []
    for k, v in params.items():
        if v is not None:
            parts.append(f"{k}={urllib.parse.quote(','.join(v) if isinstance(v, list) else str(v), safe='')}")
    return path + ("?" + "&".join(parts) if parts else "")


SENT = S.load(str(ROOT / "tests" / "sentinels.json"))
N = "https://www.example.org/templates/minutes"
CONTRACTS = J.Contracts(ROOT / "contracts")
RECALL_SCHEMA = CONTRACTS.file("mcp-tools.v1.json")["$defs"]["RecallResult"]
try:
    if not wait_ready():
        check("harness: server starts", False, "server did not become ready")
        raise SystemExit(1)
    check("harness: server starts on a temp port with an empty working directory", True)
    st, js, _ = api("GET", "/v1/templates")
    check("precondition: GET /v1/templates works and lists seeds", st == 200 and len(js["items"]) >= 1)
    check("precondition: authentication is still required", api("GET", "/v1/recall?url=" + urllib.parse.quote(N), token=None)[0] == 401)

    cap = SENT.of("capability")[0:2] + SENT.of("url_parts")[0:3]
    sent_url = f"https://docs.google.com/document/d/{cap[0]}/edit?resourcekey={cap[1]}&q={cap[2]}#{cap[3]}"
    queries = [
        dict(url=N, doc_type="meeting_minutes", locale="ko-KR"),
        dict(url="https://docs.google.com/document/d/ABC123/edit?usp=sharing", doc_type="meeting_minutes"),
        dict(url=N, keywords=["초안"]),
        dict(url=N, doc_type="report", scope="public"),
    ]
    m = Mcp()
    tools = {t["name"]: t for t in m.rpc("tools/list")["result"]["tools"]}
    init = m.rpc("initialize", {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "smoke", "version": "1"}})
    has = "document_memory_recall" in tools
    check("RV-30: tools/list has document_memory_recall and keeps the earlier tools",
          has and all(n in tools for n in ("document_memory_status", "document_template_search", "document_memory_create")), str(sorted(tools)))
    if has:
        t = tools["document_memory_recall"]
        sch = t["inputSchema"]
        ref = next(x for x in CONTRACTS.file("mcp-tools.v1.json")["tools"] if x["name"] == "doc_memory_recall")
        props, rp = sch.get("properties", {}), ref["inputSchema"]["properties"]
        sem = (set(props) == set(rp) and sch.get("required") == ["url"] and sch.get("additionalProperties") is False
               and props.get("keywords", {}).get("maxItems") == 8 and props.get("keywords", {}).get("items", {}).get("maxLength") == 32
               and props.get("limit", {}).get("minimum") == 1 and props.get("limit", {}).get("maximum") == 3
               and all(props.get(k, {}).get("enum") == rp[k].get("enum") for k in ("scope", "kind", "provider")))
        check("RV-30: input schema is semantically the contract's doc_memory_recall schema", sem, "properties/limits/enums differ from the contract")
        check("RV-30: annotations equal the contract (read-only, idempotent)", t.get("annotations") == ref.get("annotations"), str(t.get("annotations")))
    ins = init["result"].get("instructions", "")
    check("RV-31: instructions stay <= 512 chars and name the tool early", len(ins) <= 512 and "document_memory_recall" in ins[:200], f"len={len(ins)}")
    for i, qy in enumerate(queries, 1):
        st, http_js, _ = api("GET", q("/v1/recall", **qy))
        errors = J.validate(http_js, RECALL_SCHEMA, CONTRACTS) if st == 200 else ["status"]
        check(f"RV-41: query {i} HTTP 200 and validates against the contract's RecallResult", st == 200 and not errors, f"status={st} errors={errors[:3]}")
        if st != 200:
            continue
        argv = ["recall", qy["url"], *(qy.get("keywords") or [])]
        for flag, key in (("--doc-type", "doc_type"), ("--locale", "locale"), ("--scope", "scope"), ("--provider", "provider")):
            if qy.get(key):
                argv += [flag, qy[key]]
        rc, out, err = cli(*argv)
        check(f"RV-40: query {i} CLI output == HTTP response", rc == 0 and json.loads(out) == http_js, f"rc={rc} err={err[:80]}")
        if has:
            is_err, mcp_js = m.call("document_memory_recall", dict(qy))
            check(f"RV-40: query {i} MCP result == HTTP response", (not is_err) and mcp_js == http_js, f"is_err={is_err}")
    st, js, _ = api("GET", q("/v1/recall", url=N, doc_type="meeting_minutes", locale="ko-KR"))
    check("RV-20: seeds are ranked, Korean seed first, at most 3 hints",
          st == 200 and js["hints"] and js["hints"][0]["memory_id"] == "meeting.minutes.ko" and len(js["hints"]) <= 3, str(js and [h["memory_id"] for h in js["hints"]]))
    for label, p in (("empty result", dict(url=N, doc_type="invoice")), ("team scope", dict(url=N, scope="team")),
                     ("kind reference", dict(url=N, doc_type="report", kind="reference"))):
        st, js, _ = api("GET", q("/v1/recall", **p))
        check(f"RV-41: {label} validates", st == 200 and not J.validate(js, RECALL_SCHEMA, CONTRACTS) and js["hints"] == []
              and js["reason"] in ("no_match", "scope_unavailable_local"), f"status={st} reason={js and js.get('reason')}")
    mine = make(title="SENTINEL_RECALL_PRIVATE", tags=["draft"])
    st, js, _ = api("GET", q("/v1/recall", url=N, doc_type="meeting_minutes", locale="ko-KR"))
    check("RV-21: a private template outranks seeds of the same form",
          st == 200 and js["hints"][0]["memory_id"] == mine["id"] and js["hints"][0]["source"]["tier"] == "mine")
    st, cp, _ = api("POST", "/v1/templates/meeting.minutes.ko/copy", {})
    st, js, _ = api("GET", q("/v1/recall", url=N, doc_type="meeting_minutes", locale="ko-KR", scope="all", limit=3))
    cph = next((h for h in js["hints"] if h["memory_id"] == cp["id"]), None)
    check("RV-28: a copy of a seed keeps origin and license in its hint",
          cph is not None and cph["source"]["origin"] == "copied" and cph["source"]["license"] == "CC0-1.0" and cph["source"]["tier"] == "mine")
    for i in range(24):
        make(title=f"T{i:02d}", doc_type="report", tags=[])
    needle = make(title="T24", doc_type="report", tags=["zz-needle"])
    st, js, _ = api("GET", q("/v1/recall", url=N, doc_type="report", locale="ko-KR", keywords=["zz-needle"], scope="mine", limit=3))
    check("RV-22: the best match is found among 25 private templates (no 20-row cap)",
          st == 200 and len(js["hints"]) == 3 and js["hints"][0]["memory_id"] == needle["id"], str(js and [h["memory_id"] for h in js["hints"]]))
    big = make(title="가" * 120, summary="나" * 600, sections=["다" * 60] * 12, doc_type="proposal", locale="ko-KR")
    st, js, _ = api("GET", q("/v1/recall", url=N, doc_type="proposal", scope="mine"))
    h = next((x for x in js["hints"] if x["memory_id"] == big["id"]), None)
    size = len(json.dumps(h, ensure_ascii=False, separators=(",", ":")).encode()) if h else -1
    check("RV-11: an oversized hint is trimmed to <= 1600 bytes with title and form intact", h is not None and size <= 1600 and h["title"] == big["title"], f"size={size}")
    for label, qs, code in (("limit=4", dict(url=N, limit=4), "invalid_input"), ("limit=0", dict(url=N, limit=0), "invalid_input"),
                            ("unknown param", dict(url=N, foo="bar1"), "invalid_input"), ("no url", dict(doc_type="report"), "invalid_input"),
                            ("bad scope", dict(url=N, scope="bogus9"), "invalid_input"), ("bad kind", dict(url=N, kind="bogus9"), "invalid_input"),
                            ("9 keywords", dict(url=N, keywords=[f"k{i}" for i in range(9)]), "invalid_input"),
                            ("empty keyword", dict(url=N, keywords=["a", "", "b"]), "invalid_input"),
                            ("unknown doc_type", dict(url=N, doc_type="unknown_thing9"), "invalid_form")):
        st, js, raw = api("GET", q("/v1/recall", **qs))
        leaked = any(w.encode() in raw for w in ("bogus9", "unknown_thing9", "bar1", "foo"))
        check(f"RV-24: {label} -> 400 {code} without echoing the input", st == 400 and js and js.get("code") == code and not leaked, f"status={st} body={raw[:90]}")
    st, js, raw = api("GET", q("/v1/recall", url="http://example.com/secret-path-9"))
    check("RV-26: an http URL -> 400 url_rejected without echo",
          st == 400 and js.get("code") == "url_rejected" and b"secret-path-9" not in raw and b"example.com" not in raw, f"status={st} body={raw[:90]}")
    st, js, raw = api("GET", q("/v1/recall", url=sent_url, doc_type="meeting_minutes"))
    check("RV-25: a Google Docs URL carrying secrets is reduced to its canonical pattern",
          st == 200 and js["canonical_url"] == "docs.google.com/document/d/:id/edit" and js["form"]["provider"] == "google_docs", f"status={st}")
    rc, out, _ = cli("recall", "--help")
    check("RV-33: `dmem recall --help` lists the channel options", rc == 0 and all(f in out for f in ("--doc-type", "--locale", "--provider", "--kind", "--scope", "--limit", "--stdin")))
    rc, out, err = cli("recall", "--stdin", stdin=json.dumps({"url": N, "doc_type": "meeting_minutes", "extra": 1}).encode())
    check("RV-34: --stdin with an unknown field fails with invalid_input and no echo",
          rc != 0 and "invalid_input" in (err + out) and "extra" not in (err + out) and "example.org" not in (err + out), f"rc={rc} err={err[:80]}")
    rc, out, err = cli("recall", "--stdin", stdin=b"{not json")
    check("RV-34: --stdin with broken JSON fails without echo", rc != 0 and "not json" not in (err + out))
    rc, out, err = cli("recall", "--stdin", stdin=json.dumps({"url": N, "doc_type": "meeting_minutes", "locale": "ko-KR"}).encode())
    st, http_js, _ = api("GET", q("/v1/recall", url=N, doc_type="meeting_minutes", locale="ko-KR"))
    check("RV-34: valid --stdin JSON gives the same result as the argument form", rc == 0 and json.loads(out) == http_js, f"rc={rc}")
    md = Mcp(env={**ENV, "DMEM_URL": "http://127.0.0.1:9"})  # nothing listens there: bad input must fail before any network call
    bad = [{}, {"url": N, "zzz": 1}, {"url": N, "limit": 4}, {"url": N, "keywords": [f"k{i}" for i in range(9)]},
           {"url": N, "keywords": ["x" * 33]}, {"url": N, "scope": "bogus"}]
    outs = []
    for a in bad:
        try:
            outs.append(md.call("document_memory_recall", a))
        except Exception as e:  # noqa: BLE001
            outs.append((None, {"exc": str(e)[:60]}))
    check("RV-32: invalid MCP arguments are rejected as invalid_input before any network call",
          all(e is True and r.get("code") == "invalid_input" for e, r in outs), str(outs)[:200])
    md.close()
    m.close()
except SystemExit:
    pass
except Exception as exc:  # noqa: BLE001 - a crash must show up as a FAIL, never as silence
    import traceback
    check("harness: unexpected exception", False, repr(exc)[:160] + " @ line " + str(traceback.extract_tb(exc.__traceback__)[-1].lineno))
finally:
    SERVER.terminate()
    try:
        SERVER.wait(timeout=5)
    except Exception:  # noqa: BLE001
        SERVER.kill()
    LOG.close()

BODIES.append(open(os.path.join(TMP, "server.log"), "rb").read())
# Only the sentinel families this run actually fed to the product are scanned for echoes.
fed_back = S.scan(BODIES, SENT, families=["capability", "url_parts", "prose", "hidden"], use_variants=True)
check(f"RV-42: no sentinel (literal, JSON, percent, base64, hex) appears in any recall response, CLI output, MCP output or the server log ({len(BODIES)} outputs scanned)",
      not fed_back, f"{len(fed_back)} hits, ids={sorted({f.sentinel_id for f in fed_back})[:8]}")
shutil.rmtree(TMP, ignore_errors=True)
bad = [r for r in RESULTS if not r[1]]
print(f"\nSUMMARY {len(RESULTS) - len(bad)}/{len(RESULTS)} checks passed")
sys.exit(1 if bad else 0)
