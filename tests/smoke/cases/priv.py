"""PRIV-01..PRIV-10: privacy, consent, retention and deletion contracts."""
import json

from dmtest.runner import case
from .util import reject


@case("PRIV-01", "R1", needs=("fixtures",))
def priv_01(ctx):
    # Prepare an import preview outside the measured local-library flow.
    box = ctx.target.sandbox(server=False)
    try:
        cli = box.cli("local")
        preview = cli.json(["web", "preview", ctx.fx_url + "/pages/resume-ko.html"])
        preview_id = (preview.json or {}).get("preview_id") or "missing-preview"
        fixture_count = len(ctx.fx_log())

        saved = cli.json(["save", "--kind", "template", "--title", "privacy local", "--doc-type", "resume",
                          "--locale", "ko-KR", "--provider", "markdown", "--stdin", "--format", "markdown"],
                         stdin="# Privacy local\n\nA local template.")
        memory_id = (saved.json or {}).get("memory_id") or "missing-memory"
        searched = cli.json(["search", "privacy local"])
        copied = cli.json(["copy", memory_id])
        imported = cli.json(["import", "--preview", preview_id, "--as", "reference"])

        ctx.expect(preview.exit == 0 and preview_id != "missing-preview", "fixture preview setup must succeed")
        ctx.expect(saved.exit == 0 and (saved.json or {}).get("visibility") == "private", "a new local save must be private")
        results = (searched.json or {}).get("results", [])
        ctx.expect(searched.exit == 0 and any(item.get("memory_id") == memory_id for item in results), "local search must find the saved memory")
        ctx.expect(copied.exit == 0 and (copied.json or {}).get("visibility") == "private", "a local copy must be private")
        ctx.expect(imported.exit == 0 and (imported.json or {}).get("visibility") == "private", "a local import must be private")
        ctx.expect(box.request_log() == [], "local save, search, copy and import must make no server requests")
        ctx.expect(len(ctx.fx_log()) == fixture_count, "the measured local-library flow must make no external fixture requests")
    finally:
        box.close()


@case("PRIV-02", "F", needs=("server", "hooks"))
def priv_02(ctx):
    query = ctx.sentinels.value("url_parts", 1)
    fragment = ctx.sentinels.value("url_parts", 2)
    doc_id = ctx.sentinels.value("capability", 1)
    resource_key = ctx.sentinels.value("capability", 2)
    body = {"url": f"https://docs.google.com/document/d/{doc_id}/edit?resourcekey={resource_key}&{query}=1#{fragment}",
            "doc_type": "resume", "locale": "ko-KR", "keywords": ["zzz_sentinel", "Draft"]}
    result = ctx.cli("carol").json(["recall", "--stdin"], stdin=json.dumps(body))
    sent = [entry for entry in ctx.request_log() if entry.get("op") == "recall"]
    ctx.expect(result.exit == 0, "server recall must complete")
    ctx.expect(len(sent) == 1, f"one server recall request is expected, saw {len(sent)}")
    keys = set(sent[0].get("body_keys", [])) if sent else set()
    allowed = {"url", "doc_type", "locale", "provider", "keywords", "kind", "scope", "limit"}
    ctx.expect(keys <= allowed and {"url", "doc_type", "locale"} <= keys, f"recall request fields must be allowlisted: {sorted(keys)}")
    ctx.expect(not ctx.scan_sinks(("carol",), families=("capability", "url_parts")), "URL capability, query and fragment sentinels must not reach a sink")


@case("PRIV-03", "F", needs=("server", "hooks"))
def priv_03(ctx):
    ctx.load_library("shr-cat", identity="alice")
    accepted = ctx.cli("alice").json(["publish", "fx_s5", "--visibility", "public", "--license", "CC-BY-4.0", "--consent"])
    ctx.expect(accepted.exit == 0, "publish with explicit consent must succeed")

    records_result = ctx.cli("alice").json(["__test", "consents"])
    records = (records_result.json or {}).get("consents", [])
    mine = [record for record in records if record.get("memory_id") == "fx_s5"]
    record = mine[-1] if mine else {}
    ctx.expect(len(mine) == 1, "the server must record exactly one consent for the published memory")
    ctx.expect(record.get("consent_version") == "share-v1" and bool(record.get("at")), "the consent record must include its version and timestamp")
    ctx.expect(record.get("memory_id") == "fx_s5" and record.get("version") == 1 and record.get("visibility") == "public" and record.get("license") == "CC-BY-4.0",
               "the consent record must identify the published target")

    writes_before = sum(1 for entry in ctx.request_log() if entry.get("write"))
    denied = ctx.cli("alice").json(["publish", "fx_s5", "--visibility", "public", "--license", "CC-BY-4.0"])
    reject(ctx, denied, "consent_required", exit_code=4)
    writes_after = sum(1 for entry in ctx.request_log() if entry.get("write"))
    ctx.expect(writes_after == writes_before, "publish without consent must send no server write request")


@case("PRIV-04", "F", needs=("server", "hooks"))
def priv_04(ctx):
    ctx.load_library("shr-cat", identity="alice")
    queued = ctx.cli("alice").json(["publish", "fx_s5", "--visibility", "public", "--license", "CC-BY-4.0", "--consent"])
    ctx.expect(queued.exit == 0 and queued.json["review_state"] == "queued", f"the publish waits in review: {queued.json}")
    cancelled = ctx.cli("alice").json(["publish", "fx_s5", "--visibility", "private"])
    ctx.expect(cancelled.exit == 0 and cancelled.json["review_state"] == "none" and cancelled.json["visibility"] == "private", f"a private publish cancels the waiting request: {cancelled.json}")
    ctx.cli("alice").json(["__test", "approve-all"])  # the review worker must find nothing left to approve
    public = ctx.cli("anon").json(["search", "--scope", "public", "--limit", "20"]).json["results"]
    ctx.expect("fx_s5" not in {x["memory_id"] for x in public}, "the cancelled item never becomes public")
    ctx.expect(ctx.cli("anon").json(["expand", "fx_s5", "--level", "1"]).exit == 7, "and cannot be read by anyone else")


@case("PRIV-05", "F", needs=("server", "hooks"))
def priv_05(ctx):
    before = ctx.cli("alice").json(["status"]).json["consent"]
    for setting in ("on", "off", "on"):
        ctx.cli("alice", {"DMEM_TELEMETRY": setting}).json(["status"])
    after = ctx.cli("alice", {"DMEM_TELEMETRY": "off"}).json(["status"]).json["consent"]
    ctx.expect(before == after == {"sharing": "enabled"}, f"toggling telemetry must not change the sharing consent: {before} -> {after}")


@case("PRIV-06", "F", needs=("server", "hooks"))
def priv_06(ctx):
    ctx.load_library("shr-cat", identity="alice")
    machine = ctx.cli("alice").json(["publish", "fx_s5", "--visibility", "public", "--license", "CC-BY-4.0", "--consent"])
    ctx.expect(machine.json.get("notice") == "privacy.detection_limit", f"--json carries the fixed notice key: {machine.json}")
    ctx.schema_ok(machine.json, "doc_memory_publish", "PublishResult")
    human = ctx.cli("alice").run(["publish", "fx_s8", "--visibility", "public", "--license", "CC-BY-4.0", "--consent"])
    ctx.expect("not complete" in human.stdout and "responsible" in human.stdout, "the human output says detection is incomplete and the owner is responsible")
    with ctx.mcp("alice") as m:
        r = m.call("doc_memory_publish", {"memory_id": "fx_s2", "visibility": "public", "license": "CC-BY-SA-4.0", "consent": True, "consent_version": "share-v1"})
        ctx.expect(r is not None and not r.is_error and r.structured.get("notice") == "privacy.detection_limit", "the MCP result carries it too")
    private = ctx.cli("alice").json(["publish", "fx_s5", "--visibility", "private"])
    ctx.expect("notice" not in private.json, "un-publishing needs no notice")


@case("PRIV-07", "F", needs=("server", "hooks", "fixtures"))
def priv_07(ctx):
    # a preview expires after 15 minutes
    p = ctx.cli("alice").json(["web", "preview", ctx.fx_url + "/pages/resume-ko.html"])
    late = ctx.cli("alice", {"DMEM_TEST_CLOCK_OFFSET": str(16 * 60)}).json(["import", "--preview", p.json["preview_id"], "--as", "template"])
    ctx.expect(late.exit == 7 and late.code == "not_found", f"a 16 minute old preview is gone: exit {late.exit}")
    # a rejected publish payload lives 7 days, its audit row (reason codes) stays
    ctx.load_library("shr-cat", identity="alice")
    rejected = ctx.cli("alice").json(["publish", "fx_s8", "--visibility", "public", "--license", "CC-BY-4.0", "--consent"])
    ctx.expect(rejected.json["review_state"] == "rejected" and "personal_data" in rejected.json["reasons"], "the publish of a personal-data reference is rejected")
    now_view = ctx.cli("alice").json(["__test", "rejected"]).json
    ctx.expect(len(now_view["payloads"]) == 1 and len(now_view["audit"]) == 1, f"before the retention ends the payload is kept: {now_view}")
    week = ctx.cli("alice", {"DMEM_TEST_CLOCK_OFFSET": str(8 * 86400)}).json(["__test", "rejected"]).json
    ctx.expect(week["payloads"] == [], "an 8 day old rejected payload is deleted")
    ctx.expect([a["reasons"] for a in week["audit"]] == [["personal_data"]] and "title" not in json.dumps(week["audit"]), f"the audit fact (reason codes only) remains: {week['audit']}")
    # a receipt is gone after 30 days (MCP-17 shows the not_found; here the whole of the outcome path)
    ctx.cli("carol").json(["__test", "consents"])
    hint = recall_one(ctx)
    expired = ctx.cli("carol", {"DMEM_TEST_CLOCK_OFFSET": str(31 * 86400)}).json(["outcome", hint["receipt_id"], "success"])
    ctx.expect(expired.exit == 7, f"a 31 day old receipt cannot be reused: exit {expired.exit}")


def recall_one(ctx):
    ctx.load_library("rcl-lib", identity="carol")
    r = ctx.cli("carol").json(["recall", "--stdin"], stdin=json.dumps({"url": "docs.google.com/document/d/:id/edit", "doc_type": "resume", "locale": "ko-KR"}))
    return r.json["hints"][0]


@case("PRIV-08", "R1")
def priv_08(ctx):
    S = ctx.sentinels
    source = ctx.home().parent / "personal.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(f"# 연락처 메모\n\n담당자 {S.value('email', 1)} / {S.value('phone', 1)} 로 연락합니다.\n", encoding="utf-8")
    saved = ctx.cli().json(["save", "--kind", "reference", "--title", "연락 메모", "--doc-type", "other", "--locale", "ko-KR", "--provider", "markdown", "--file", str(source)])
    ctx.expect(saved.exit == 0, f"a reference with personal data is stored (kept, flagged): {saved.code}")
    stored = ctx.scan_sinks(("local",), families=("email", "phone"), server=False)
    ctx.expect(stored, "control: before the delete the personal values ARE in the user's own library (this scan can see them)")
    ctx.expect(ctx.cli().json(["delete", saved.json["memory_id"], "--yes"]).exit == 0, "delete")
    source.unlink()
    gone = ctx.scan_sinks(("local",), families=("email", "phone"), server=False)
    ctx.expect(not gone, f"after the delete no client-side sink (store, originals, cache, diagnostics) holds the values: {[g.sentinel_id for g in gone]}")


@case("PRIV-09", "F")
def priv_09(ctx):
    ctx.skip("account deletion (confirmation=DELETE) is a web/account operation (docs/spec/accounts-community-v1.md, privacy.md section 5), not a CLI or MCP tool; "
             "it is verified by the product's account tests (docs/test/functional-account.md)")


@case("PRIV-10", "F", needs=("server", "hooks"))
def priv_10(ctx):
    ctx.load_library("shr-cat", identity="alice")
    ctx.cli("alice").json(["publish", "fx_s5", "--visibility", "public", "--license", "CC-BY-4.0", "--consent"])
    ctx.cli("alice").json(["__test", "approve-all"])
    shown = []
    for who in ("anon", "bob"):
        cli = ctx.cli(who)
        shown.append(cli.json(["search", "--scope", "public", "--limit", "20"]).stdout)
        shown.append(cli.json(["expand", "fx_s1", "--level", "2"]).stdout)
        shown.append(cli.json(["expand", "fx_s5", "--level", "2"]).stdout)
        shown.append(cli.json(["recall", "--stdin"], stdin=json.dumps({"url": "www.example.org/pages/resume-ko.html", "doc_type": "resume"})).stdout)
    text = "\n".join(shown)
    for needle, label in (("source_ref", "source_ref"), ("src_", "source_ref value"), ("@", "an email"), ("account_id", "an account id"), ("device", "a device id")):
        ctx.expect(needle not in text, f"public responses must not contain {label}")
    ctx.expect("fx_s1" in text and "alice" in text, "control: the public responses do show the item and its author handle")
