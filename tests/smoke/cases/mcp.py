"""MCP-01..MCP-12: stdio MCP contract cases (docs/test/functional-tests.md)."""
import json
import time
from pathlib import Path

from dmtest.runner import case
from .util import recall, save_md


ROOT = Path(__file__).resolve().parents[3]
VERSIONS = ("2024-11-05", "2025-03-26", "2025-11-25")


def _catalog():
    return json.loads((ROOT / "contracts" / "mcp-tools.v1.json").read_text(encoding="utf-8"))


@case("MCP-01", "R1")
def mcp_01(ctx):
    for version in VERSIONS:
        with ctx.mcp(initialize=False) as session:
            reply = session.initialize(version)
            result = (reply or {}).get("result") or {}
            ctx.expect(reply is not None and "result" in reply, f"initialize must reply for {version}")
            ctx.expect(result.get("protocolVersion") == version, f"initialize must negotiate requested supported version {version}")
            ctx.expect(isinstance(result.get("serverInfo"), dict) and bool(result.get("serverInfo", {}).get("name")),
                       f"initialize must include serverInfo for {version}")
            ctx.expect(isinstance(result.get("capabilities", {}).get("tools"), dict),
                       f"initialize must advertise tools capability for {version}")
            ctx.expect(isinstance(result.get("instructions"), str) and bool(result.get("instructions")),
                       f"initialize must include instructions for {version}")

    unsupported = "2099-01-01"
    with ctx.mcp(initialize=False) as session:
        reply = session.initialize(unsupported)
        negotiated = ((reply or {}).get("result") or {}).get("protocolVersion")
        ctx.expect(reply is not None and "result" in reply, "initialize must answer an unsupported requested version")
        ctx.expect(isinstance(negotiated, str) and negotiated in VERSIONS,
                   "an unsupported requested version must receive a supported negotiated version")


@case("MCP-02", "R1")
def mcp_02(ctx):
    catalog = _catalog()
    expected = catalog["tools"]
    for version in ("2024-11-05", "2025-11-25"):
        with ctx.mcp(initialize=False) as session:
            initialized = session.initialize(version)
            ctx.expect(initialized is not None and "result" in initialized, f"initialize before tools/list for {version}")
            actual = session.list_tools()
            expected_names = [tool["name"] for tool in expected]
            actual_names = [tool.get("name") for tool in actual]
            ctx.expect(len(actual) == 12, f"{version}: tools/list must contain 12 tools, got {len(actual)}")
            ctx.expect(actual_names == expected_names, f"{version}: tools/list names must match the catalog in order")
            by_name = {tool.get("name"): tool for tool in actual}
            for spec in expected:
                name = spec["name"]
                served = by_name.get(name) or {}
                ctx.expect(served.get("inputSchema") == spec.get("inputSchema"),
                           f"{version}: {name} inputSchema must match the catalog")
                if version == "2024-11-05":
                    ctx.expect("annotations" not in served, f"{version}: {name} must omit annotations")
                    ctx.expect("outputSchema" not in served, f"{version}: {name} must omit outputSchema")
                else:
                    ctx.expect(served.get("annotations") == spec.get("annotations"),
                               f"{version}: {name} annotations must match the catalog")
                    has_output = "outputSchema" in served
                    ctx.expect(has_output == (name == "doc_memory_delete"),
                               f"{version}: outputSchema must be present only for doc_memory_delete")


@case("MCP-04", "R1")
def mcp_04(ctx):
    before = ctx.cli().json(["list"])
    with ctx.mcp(initialize=False) as session:
        initialized = session.initialize("2025-11-25")
        ctx.expect(initialized is not None and "result" in initialized, "initialize before invalid method calls")
        method_error = session.rpc("doc_memory_unknown_method")
        tool_error = session.rpc("tools/call", {"name": "doc_memory_unknown_tool", "arguments": {}})
        ctx.expect(method_error is not None and method_error.get("error", {}).get("code") == -32601,
                   "an unknown method must return JSON-RPC error -32601")
        ctx.expect(tool_error is not None and tool_error.get("error", {}).get("code") == -32602,
                   "an unknown tool must return JSON-RPC error -32602")
    after = ctx.cli().json(["list"])
    ctx.expect(before.exit == 0 and after.exit == 0 and before.json == after.json,
               "unknown method and tool calls must not change the library list")


DOCS = "docs.google.com/document/d/:id/edit"


def tool_save(title="양식", variant=None, body="# 양식\n\n## 경력\n본문 내용", doc_type="resume", locale="ko-KR", **extra):
    form = {"doc_type": doc_type, "locale": locale, "provider": "google_docs"}
    if variant:
        form["variant"] = variant
    return {"kind": "template", "title": title, "form": form, "url_patterns": [DOCS], "content": {"format": "markdown", "data": body}, **extra}


def saved_ids(ctx):
    return [m["memory_id"] for m in ctx.cli().json(["list"]).json["results"]]


@case("MCP-03", "R1")
def mcp_03(ctx):
    with ctx.mcp() as m:
        saved = m.call("doc_memory_save", tool_save("본 양식"))
        ctx.expect(saved is not None and not saved.is_error, "save succeeds")
        memory = saved.structured["memory_id"]
        calls = [("doc_memory_status", {}), ("doc_memory_save", tool_save("두 번째", variant="second")), ("doc_memory_recall", {"url": DOCS, "doc_type": "resume"}),
                 ("doc_memory_search", {"scope": "mine"}), ("doc_memory_expand", {"memory_id": memory, "level": 2}), ("doc_memory_copy", {"memory_id": memory}),
                 ("doc_memory_delete", {"memory_id": memory, "confirm": True})]
        for name, args in calls:
            r = m.call(name, args)
            ctx.expect(r is not None and not r.is_error, f"{name}: a valid call succeeds ({None if r is None else r.code})")
            if r is None or r.is_error:
                continue
            ctx.expect(r.json == r.structured, f"{name}: the text JSON and structuredContent are the same document")
            ctx.schema_ok(r.structured, name, f"{name} result")


@case("MCP-05", "R1")
def mcp_05(ctx):
    secret = ctx.sentinels.value("prose", 1)
    before = saved_ids(ctx)
    with ctx.mcp() as m:
        bad = [("doc_memory_recall", {"url": DOCS, "limit": "three"}), ("doc_memory_recall", {"url": DOCS, "scope": secret}), ("doc_memory_recall", {"url": DOCS, "extra_field": secret}),
               ("doc_memory_recall", {"url": DOCS, "limit": 0}), ("doc_memory_recall", {"url": DOCS, "limit": 4}), ("doc_memory_search", {"limit": 21}),
               ("doc_memory_expand", {"memory_id": "x", "level": 3}), ("doc_memory_save", {"kind": secret, "title": "t", "form": {}}), ("doc_memory_delete", {"memory_id": "x"})]
        for name, args in bad:
            r = m.call(name, args)
            ctx.expect(r is not None and r.is_error and r.code == "invalid_input", f"{name} {list(args)}: expected an invalid_input tool error, got {None if r is None else r.code}")
            ctx.expect(r is None or secret not in r.text, f"{name}: the error must not echo the input")
    ctx.expect(saved_ids(ctx) == before, "no state change")


@case("MCP-06", "R1")
def mcp_06(ctx):
    with ctx.mcp() as m:
        m.call("doc_memory_status", {})
        m.call("doc_memory_save", tool_save("stdout"))
        m.call("doc_memory_recall", {"url": DOCS})
        m.call("doc_memory_recall", {"url": "http://bad.example/"})  # an error path writes a log line too
        m.rpc("no_such_method")
        m.list_tools()
        m.ping()
        time.sleep(0.2)
        ctx.expect(m.noise_bytes == 0, f"only JSON-RPC messages may appear on stdout, saw {m.noise_bytes} other bytes")
        lines = [line for line in bytes(m.raw_out).splitlines() if line.strip()]
        ctx.expect(len(lines) >= 7 and all(line.startswith(b"{") for line in lines), "every stdout line is a JSON object")


@case("MCP-07", "R1")
def mcp_07(ctx):
    marker = b"MARKER_MUST_NOT_ECHO"
    garbage = {"oversize frame": b'{"jsonrpc":"2.0","id":1,"method":"ping","params":{"x":"' + marker + b"a" * (70 * 1024) + b'"}}\n',
               "invalid UTF-8": b'{"jsonrpc":"2.0","id":2,"method":"ping","params":{"x":"' + marker + b'\xff\xfe"}}\n',
               "invalid JSON": b"{not json " + marker + b"\n"}
    with ctx.mcp() as m:
        for label, raw in garbage.items():
            m.send_raw(raw)
            reply = m.read(timeout=10.0)
            code = ((reply or {}).get("error") or {}).get("code")
            ctx.expect(reply is not None and code in (-32700, -32600, -32602), f"{label}: a JSON-RPC error is returned (got {code})")
            ctx.expect(reply is None or marker not in json.dumps(reply).encode(), f"{label}: the error must not echo the input")
            ctx.expect(m.ping(timeout=10.0), f"{label}: the connection stays usable (ping)")


@case("MCP-08", "R1", needs=("fixtures",))
def mcp_08(ctx):
    with ctx.mcp() as m:
        ident = 4242
        m.send({"jsonrpc": "2.0", "id": ident, "method": "tools/call", "params": {"name": "doc_memory_web_preview", "arguments": {"url": ctx.fx_url + "/slow"}}})
        time.sleep(1.0)
        ctx.expect(m.ping(), "ping is answered while a request is in flight")
        m.notify("notifications/cancelled", {"requestId": ident})
        m.notify("notifications/cancelled", {"requestId": 987654})  # an unknown id is ignored
        ctx.expect(m.ping(), "ping still works after both cancellations")
        deadline = time.monotonic() + 14
        late = None
        while time.monotonic() < deadline and late is None:
            late = m.read(timeout=1.0, ident=ident)
        ctx.expect(late is None, "a cancelled request must not be answered")
        ctx.expect(m.ping(), "and the server is still healthy")


@case("MCP-09", "R1")
def mcp_09(ctx):
    with ctx.mcp() as m:
        for i in range(5):
            m.call("doc_memory_save", tool_save(f"양식 {i}", variant=f"v{i}"))
        r = m.call("doc_memory_recall", {"url": DOCS, "doc_type": "resume", "locale": "ko-KR"})
        ctx.expect(r is not None and not r.is_error, "recall succeeds")
        ctx.schema_ok(r.structured, "doc_memory_recall", "RecallResult")
        ctx.expect(len(r.structured["hints"]) == 3, f"at most 3 hints: {len(r.structured['hints'])}")
        ctx.expect(r.structured["untrusted"] is True, "the result is framed as untrusted")
        cli = recall(ctx, DOCS, doc_type="resume", locale="ko-KR")
        strip = lambda hints: [{k: v for k, v in h.items() if k != "receipt_id"} for h in hints]  # noqa: E731
        ctx.expect(strip(cli.json["hints"]) == strip(r.structured["hints"]), "MCP and CLI agree (RCL-14)")


@case("MCP-10", "F")
def mcp_10(ctx):
    with ctx.mcp() as m:
        for i in range(5):
            m.call("doc_memory_save", tool_save(f"양식 {i}", variant=f"v{i}"))
        first = m.call("doc_memory_search", {"scope": "mine", "limit": 2})
        ctx.schema_ok(first.structured, "doc_memory_search", "SearchResult")
        ctx.expect(len(first.structured["results"]) == 2 and first.structured.get("next_cursor"), "the first page has 2 results and a cursor")
        second = m.call("doc_memory_search", {"scope": "mine", "limit": 2, "cursor": first.structured["next_cursor"]})
        third = m.call("doc_memory_search", {"scope": "mine", "limit": 2, "cursor": second.structured["next_cursor"]})
        ids = [x["memory_id"] for r in (first, second, third) for x in r.structured["results"]]
        ctx.expect(len(ids) == 5 and len(set(ids)) == 5 and not third.structured.get("next_cursor"), f"the cursor walks all five results exactly once: {len(ids)}")
        too_many = m.call("doc_memory_search", {"scope": "mine", "limit": 21})
        ctx.expect(too_many.is_error and too_many.code == "invalid_input", "limit above 20 is refused")
        ctx.expect(len(m.call("doc_memory_search", {"scope": "mine", "limit": 20}).structured["results"]) == 5, "limit 20 is allowed")


@case("MCP-11", "R1")
def mcp_11(ctx):
    with ctx.mcp() as m:
        saved = m.call("doc_memory_save", tool_save("v1", body="# 양식\n\n## 경력\n첫 번째"))
        memory = saved.structured["memory_id"]
        m.call("doc_memory_save", tool_save("v2", body="# 양식\n\n## 경력\n두 번째", memory_id=memory, base_version=1))
        l1 = m.call("doc_memory_expand", {"memory_id": memory, "level": 1})
        l2 = m.call("doc_memory_expand", {"memory_id": memory, "level": 2})
        old = m.call("doc_memory_expand", {"memory_id": memory, "level": 2, "version": 1})
        ctx.expect(l1.structured["level"] == 1 and l1.structured["l2"] is None, "level 1 carries no L2")
        ctx.expect(l2.structured["level"] == 2 and l2.structured["version"] == 2 and "두 번째" in l2.text, "level 2 shows the head")
        ctx.expect(old.structured["version"] == 1 and "첫 번째" in old.text and "두 번째" not in old.text, "version pins the content")
        missing = m.call("doc_memory_expand", {"memory_id": "mem_does_not_exist", "level": 1})
        ctx.expect(missing.is_error and missing.code == "not_found", "an unknown memory is not_found")
        for r in (l1, l2, old):
            ctx.schema_ok(r.structured, "doc_memory_expand", "ExpandResult")


@case("MCP-12", "R1")
def mcp_12(ctx):
    tools = {t["name"]: t for t in _catalog()["tools"]}
    keys = set(tools["doc_memory_save"]["inputSchema"]["properties"])
    ctx.expect(not ({"file", "path", "file_path", "filename"} & keys), f"the MCP save takes inline content only; its fields: {sorted(keys)}")
    ctx.expect("doc_memory_save" in tools and "content" in keys, "inline content is the way in")
    with ctx.mcp() as m:
        dry = m.call("doc_memory_save", tool_save("dry", dry_run=True))
        ctx.expect(dry is not None and not dry.is_error and dry.structured["dry_run"] is True and dry.structured["memory_id"] is None, f"dry_run stores nothing: {dry.structured if dry else None}")
        ctx.expect(saved_ids(ctx) == [], "the library is empty after a dry run")
        first = m.call("doc_memory_save", tool_save("real"))
        again = m.call("doc_memory_save", tool_save("real"))
        ctx.expect(first.structured["created"] is True and again.structured["created"] is False and again.structured["memory_id"] == first.structured["memory_id"], "an identical re-save returns created:false")
        secret = m.call("doc_memory_save", tool_save("secret", variant="s", body="# 양식\n\n" + ctx.sentinels.value("api_key", 1)))
        ctx.expect(secret.is_error and secret.code == "secret_detected", "a secret in the content is refused")
        ctx.expect(ctx.sentinels.value("api_key", 1) not in secret.text, "and not echoed")
        ctx.schema_ok(first.structured, "doc_memory_save", "SaveResult")
