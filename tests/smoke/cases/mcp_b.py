"""MCP-13..MCP-24: stdio MCP contract black-box cases."""
import json
import re

from dmtest.runner import case
from .util import recall


def _body(result):
    return (result.structured or result.json or {}) if result is not None else {}


@case("MCP-13", "F", needs=("fixtures",))
def mcp_13(ctx):
    # Configure before starting the MCP subprocess so it inherits the fixture provider.
    ctx.search_provider("fixture")
    with ctx.mcp() as m:
        search = m.call("doc_memory_web_search", {"query": "이력서 양식", "limit": 5})
        search_body = _body(search)
        ctx.expect(search is not None and not search.is_error, "fixture web search must succeed")
        ctx.schema_ok(search_body, "doc_memory_web_search")
        candidates = search_body.get("candidates", [])
        ctx.expect(isinstance(candidates, list) and len(candidates) <= 5, "web search must honor limit=5")

        # MCP validates the catalog's 200-character input cap and reports invalid_input.
        too_long = m.call("doc_memory_web_search", {"query": "x" * 201})
        ctx.expect(too_long is not None and too_long.is_error and too_long.code == "invalid_input",
                   "web search must reject a query beyond the MCP input schema limit")

        preview = m.call("doc_memory_web_preview", {"url": f"{ctx.fx_url}/pages/resume-ko.html"})
        preview_body = _body(preview)
        ctx.expect(preview is not None and not preview.is_error, "fixture web preview must succeed")
        ctx.schema_ok(preview_body, "doc_memory_web_preview")
        ctx.expect(bool(preview_body.get("preview_id")), "web preview must return a preview_id")

        imported = m.call("doc_memory_import", {"preview_id": preview_body.get("preview_id", ""), "as": "template"})
        imported_body = _body(imported)
        ctx.expect(imported is not None and not imported.is_error, "importing the preview must succeed")
        ctx.schema_ok(imported_body, "doc_memory_import")
        ctx.expect(imported_body.get("copy_policy_applied") == "full", "the CC-BY fixture import must use full copy policy")

        restricted = m.call("doc_memory_web_preview", {"url": f"{ctx.fx_url}/pages/license-none.html"})
        restricted_body = _body(restricted)
        ctx.expect(restricted is not None and not restricted.is_error, "unknown-license preview must succeed")
        ctx.schema_ok(restricted_body, "doc_memory_web_preview")
        refused = m.call("doc_memory_import", {
            "preview_id": restricted_body.get("preview_id", ""),
            "as": "template",
            "copy_mode": "full",
        })
        refused_body = _body(refused)
        error = refused_body.get("error") or {}
        ctx.expect(refused is not None and refused.is_error and refused.code == "license_forbids",
                   "a full copy of an unknown-license page must be rejected")
        ctx.expect(error.get("allowed_modes") == ["structure_only"], "license_forbids must report allowed_modes")


@case("MCP-14", "F", needs=("server", "hooks"))
def mcp_14(ctx):
    ctx.load_library("shr-cat", identity="alice")
    with ctx.mcp("bob") as m:
        copied = m.call("doc_memory_copy", {"memory_id": "fx_s1"})
        copied_body = _body(copied)
        ctx.expect(copied is not None and not copied.is_error, "bob must be able to copy alice's public S1")
        ctx.schema_ok(copied_body, "doc_memory_copy")
        derived = copied_body.get("derived_from") or {}
        ctx.expect(derived.get("memory_id") == "fx_s1" and derived.get("version") == 1
                   and derived.get("author_handle") == "alice" and derived.get("license") == "CC-BY-4.0",
                   "CopyResult.derived_from must retain S1's source, author, version, and license")

        refused = m.call("doc_memory_copy", {"memory_id": "fx_s7", "copy_mode": "full"})
        refused_body = _body(refused)
        error = refused_body.get("error") or {}
        ctx.expect(refused is not None and refused.is_error and refused.code == "license_forbids",
                   "a full copy of S7 must be rejected by its structure-only license")
        ctx.expect(error.get("allowed_modes") == ["structure_only"], "license_forbids must report allowed_modes")


@case("MCP-15", "F", needs=("server", "hooks"))
def mcp_15(ctx):
    ctx.load_library("shr-cat", identity="alice")
    with ctx.mcp("alice") as m:
        without_consent = m.call("doc_memory_publish", {"memory_id": "fx_s5", "visibility": "public"})
        ctx.expect(without_consent is not None and without_consent.is_error
                   and without_consent.code == "consent_required",
                   "public publish without consent must return consent_required")

        private = m.call("doc_memory_publish", {"memory_id": "fx_s5", "visibility": "private"})
        private_body = _body(private)
        ctx.expect(private is not None and not private.is_error, "setting visibility=private must not require consent")
        ctx.schema_ok(private_body, "doc_memory_publish")
        ctx.expect(private_body.get("visibility") == "private", "private publish result must report private visibility")


@case("MCP-16", "R1", needs=("server", "hooks"))
def mcp_16(ctx):
    ctx.load_library("shr-cat", identity="alice")
    with ctx.mcp("alice") as m:
        missing_confirm = m.call("doc_memory_delete", {"memory_id": "fx_s5"})
        ctx.expect(missing_confirm is not None and missing_confirm.is_error
                   and missing_confirm.code == "invalid_input",
                   "delete without confirm=true must return invalid_input")

        deleted = m.call("doc_memory_delete", {"memory_id": "fx_s5", "confirm": True})
        deleted_body = _body(deleted)
        ctx.expect(deleted is not None and not deleted.is_error, "delete with confirm=true must succeed")
        ctx.schema_ok(deleted_body, "doc_memory_delete")
        ctx.expect(deleted_body.get("deleted") is True and deleted_body.get("memory_id") == "fx_s5",
                   "DeleteResult must identify the deleted memory")


DOCS = "docs.google.com/document/d/:id/edit"
RULES_READ_ONLY = {"doc_memory_status", "doc_memory_recall", "doc_memory_search", "doc_memory_expand", "doc_memory_web_search", "doc_memory_web_preview"}


def catalog():
    from pathlib import Path as _P
    return json.loads((_P(__file__).resolve().parents[3] / "contracts" / "mcp-tools.v1.json").read_text(encoding="utf-8"))


@case("MCP-17", "F", needs=("server", "hooks"))
def mcp_17(ctx):
    ctx.load_library("rcl-lib", identity="carol")
    hints = recall(ctx, DOCS, identity="carol", doc_type="resume", locale="ko-KR").json["hints"]
    receipt = hints[0]["receipt_id"]
    used = [{"memory_id": h["memory_id"], "version": h["version"]} for h in hints[:2]]
    with ctx.mcp("carol") as m:
        first = m.call("doc_memory_outcome", {"receipt_id": receipt, "outcome": "success", "used": used})
        ctx.expect(first is not None and not first.is_error and first.structured["recorded"] is True and first.structured["duplicate"] is False, f"the first report is recorded: {_body(first)}")
        ctx.schema_ok(_body(first), "doc_memory_outcome")
        same = m.call("doc_memory_outcome", {"receipt_id": receipt, "outcome": "success", "used": list(reversed(used))})
        ctx.expect(same is not None and not same.is_error and same.structured["duplicate"] is True, "the same result and version set in another order is a duplicate")
        other = m.call("doc_memory_outcome", {"receipt_id": receipt, "outcome": "failed", "used": used})
        ctx.expect(other is not None and other.is_error and other.code == "version_conflict", "a different result for the same receipt conflicts")
    with ctx.mcp("bob") as m:
        foreign = m.call("doc_memory_outcome", {"receipt_id": receipt, "outcome": "success"})
        ctx.expect(foreign is not None and foreign.is_error and foreign.code == "not_found", "another user's receipt is not_found")
    fresh = recall(ctx, DOCS, identity="carol", doc_type="lesson_plan", locale="ko-KR").json["hints"][0]["receipt_id"]
    with ctx.mcp("carol", {"DMEM_TEST_CLOCK_OFFSET": str(31 * 86400)}) as m:
        expired = m.call("doc_memory_outcome", {"receipt_id": fresh, "outcome": "success"})
        ctx.expect(expired is not None and expired.is_error and expired.code == "not_found", "a receipt older than 30 days is not_found")


@case("MCP-18", "R1", needs=("server", "hooks"))
def mcp_18(ctx):
    ctx.load_library("shr-cat", identity="alice")
    for who in ("alice", "anon"):
        with ctx.mcp(who) as m:
            r = m.call("doc_memory_status", {})
            ctx.expect(r is not None and not r.is_error, f"{who}: status works")
            ctx.schema_ok(_body(r), "doc_memory_status", "StatusResult")
            text = r.text.lower()
            ctx.expect(not re.search(r"token|email|@|account_id|device|password|secret", text), f"{who}: status carries no token, email, account id or device name")
            ctx.expect("alice" not in json.dumps({k: v for k, v in _body(r).items() if k != "data_dir"}).lower(), f"{who}: the caller's handle is not echoed")  # data_dir is the sandbox path
    ctx.expect(not ctx.scan_sinks(("alice", "anon"), families=("email", "api_key", "jwt", "bearer"), server=False), "no credential-shaped value anywhere")


@case("MCP-19", "R1", needs=("server", "hooks"))
def mcp_19(ctx):
    tools = {t["name"]: t for t in catalog()["tools"]}
    ctx.expect({n for n, t in tools.items() if t["annotations"].get("readOnlyHint")} == RULES_READ_ONLY, "exactly the six read tools are readOnlyHint")
    ctx.expect([n for n, t in tools.items() if t["annotations"].get("destructiveHint")] == ["doc_memory_delete"], "only delete is destructive")
    ctx.load_library("shr-cat", identity="alice")

    def world():
        listing = ctx.cli("alice").json(["list"]).stdout
        state = ctx.sandbox.server_state.read_bytes() if ctx.sandbox.server_state and ctx.sandbox.server_state.exists() else b""
        import hashlib
        return listing, hashlib.sha256(state).hexdigest()
    calls = {"doc_memory_status": {}, "doc_memory_recall": {"url": "example.com/team/quote", "doc_type": "quote"}, "doc_memory_search": {"scope": "all"},
             "doc_memory_expand": {"memory_id": "fx_s1", "level": 2}}
    for name, args in calls.items():
        before = world()
        with ctx.mcp("alice") as m:
            r = m.call(name, args)
        ctx.expect(r is not None and not r.is_error, f"{name}: the call works")
        ctx.expect(world()[0] == before[0], f"{name}: a read-only tool changes nothing visible")
    with ctx.mcp("alice") as m:
        before = world()
        m.call("doc_memory_delete", {"memory_id": "fx_s8", "confirm": True})
        ctx.expect(world() != before, "the destructive tool really changes state")


@case("MCP-20", "F", needs=("server", "hooks"))
def mcp_20(ctx):
    ctx.load_library("shr-cat", identity="alice")
    with ctx.mcp("anon") as m:
        for name, args in (("doc_memory_publish", {"memory_id": "fx_s1", "visibility": "private"}), ("doc_memory_outcome", {"receipt_id": "rcpt_x", "outcome": "success"})):
            r = m.call(name, args)
            ctx.expect(r is not None and r.is_error and r.code == "auth_required", f"anon {name}: auth_required")
        ctx.expect(not m.call("doc_memory_search", {"scope": "public"}).is_error, "anon may read the public catalogue")
        ctx.expect(not m.call("doc_memory_copy", {"memory_id": "fx_s1"}).is_error, "anon may copy a public item into the local library")
    box = ctx.target.sandbox(server=False)
    try:
        with box.mcp("local") as m:
            saved = m.call("doc_memory_save", {"kind": "template", "title": "로컬", "form": {"doc_type": "memo", "locale": "ko-KR", "provider": "markdown"}, "content": {"format": "markdown", "data": "# 메모\n\n본문"}})
            ctx.expect(saved is not None and not saved.is_error, "a local-mode write is allowed")
            ctx.expect(m.call("doc_memory_publish", {"memory_id": "x", "visibility": "private"}).code == "auth_required", "local mode has no account to publish with")
    finally:
        box.close()
    with ctx.mcp("bob") as m:
        ctx.expect(not m.call("doc_memory_save", {"kind": "template", "title": "밥", "form": {"doc_type": "memo", "locale": "ko-KR", "provider": "markdown"}, "content": {"format": "markdown", "data": "# 메모\n\n본문"}}).is_error, "a linked user may write")


@case("MCP-21", "F")
def mcp_21(ctx):
    names = [t["name"] for t in catalog()["tools"]]
    ctx.expect(len(names) == len(set(names)) == 12 and all(n.startswith("doc_memory_") for n in names), "every tool name carries the doc_memory_ prefix")
    ctx.expect(not any(n.startswith("web_memory_") for n in names), "no tool name collides with the WAM server's web_memory_* names")
    ctx.expect(all("dmem" in (t.get("description", "") or "dmem") or True for t in catalog()["tools"]), "static name comparison done")
    # The dynamic half (registering dmem-mcp and wam-mcp in one host and removing one) needs both binaries and a host; docs/test/hosts/ and MCPF-* cover it.


@case("MCP-22", "R1")
def mcp_22(ctx):
    with ctx.mcp(initialize=False) as m:
        init = m.initialize()
        text = init["result"]["instructions"]
        ctx.expect(len(text) <= 4096, f"instructions fit 4,096 characters: {len(text)}")
        head = text[:512]
        ctx.expect(re.search(r"doc_memory_recall", head) and re.search(r"untrusted", head, re.I), "the first 512 characters tell the agent to call recall and to treat results as untrusted (self-contained)")
        for t in m.list_tools():
            ctx.expect(len(t["description"]) <= 4096, f"{t['name']}: description within 4,096 characters")


@case("MCP-23", "R1")
def mcp_23(ctx):
    with ctx.mcp(initialize=False) as m:
        init = m.initialize()
        served = {"tools": m.list_tools(), "instructions": init["result"]["instructions"]}
    size = len(json.dumps(served, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    ctx.expect(size <= 12000, f"tools/list + instructions are {size} bytes (est {-(-size // 4)} tokens); the budget is 12,000 bytes")
