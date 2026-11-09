"""SEC-A04: after a session full of sentinel-bearing inputs, none of the eight sinks may hold a sentinel (docs/test/security-scenarios.md).

Sentinel inputs travel by stdin or file only: a value the harness itself puts into argv would be "found" in the argv sink by construction.
"""
import json

from dmtest.runner import case

SECRETS = ("api_key", "jwt", "bearer", "private_key")
PII = ("email", "phone", "national_id", "card", "account")
LOCATORS = ("capability", "url_parts")


def save_args(title, doc_type="resume"):
    return ["save", "--kind", "template", "--title", title, "--doc-type", doc_type, "--locale", "ko-KR", "--provider", "markdown", "--stdin", "--format", "markdown"]


@case("SEC-A04", "F", needs=("server", "hooks", "fixtures"))
def sec_a04(ctx):
    S = ctx.sentinels
    ctx.search_provider("fixture")
    alice = ctx.cli("alice")
    for family in SECRETS:  # a secret anywhere in the document: the whole save is refused
        body = "# 양식\n\n" + "\n\n".join(f"문단 {i} 정상 문장입니다." for i in range(20)) + f"\n\n{S.value(family, 1)}\n"
        refused = alice.json(save_args(f"secret-{family}"), stdin=body)
        ctx.expect(refused.exit == 2 and refused.code == "secret_detected", f"{family}: a secret must refuse the save (exit {refused.exit})")
    pii_body = "# 이력서\n\n## 인적사항\n" + "\n".join(f"- {S.value(f, 1)}" for f in PII) + "\n"
    kept = alice.json(save_args("pii-template"), stdin=pii_body)
    ctx.expect(kept.exit == 0, f"a template with personal data is stored (slotified): exit {kept.exit}")
    level2 = alice.json(["expand", kept.json["memory_id"], "--level", "2"]) if kept.exit == 0 else None
    ctx.expect(level2 is not None and level2.exit == 0, "the stored template can be expanded")
    for family, secret_url in (("url_parts", f"https://user:{S.value('url_parts', 3)}@example.com/x"), ("url_parts", "https://example.com/x?" + S.value("url_parts", 1) + "#" + S.value("url_parts", 2))):
        alice.json(["recall", "--stdin"], stdin=json.dumps({"url": secret_url, "doc_type": "resume"}))
    cap = S.value("capability", 1)
    docs = f"{ctx.fx_url}/p/google-docs/document/d/{cap}/edit?resourcekey={S.value('capability', 2)}"
    with ctx.mcp("alice") as m:  # the URL travels in a JSON-RPC message, never in argv
        imported = m.call("doc_memory_import", {"url": docs, "as": "template"})
        ctx.expect(imported is not None and not imported.is_error, f"import of a capability URL: {None if imported is None else imported.code}")
        if imported is not None and not imported.is_error:
            alice.json(["export", imported.structured["memory_id"], "--format", "json", "--out", str(ctx.home("alice").parent / "export.json")])
    alice.json(["recall", "--stdin"], stdin=json.dumps({"url": docs, "doc_type": "resume"}))  # recalling by a capability URL must not echo or keep its id
    alice.json(["recall", "--stdin"], stdin=json.dumps({"url": "example.com/x", "doc_type": S.value("email", 2)}))  # an invalid form value that is also a sentinel
    with ctx.mcp("alice") as m:
        m.call("doc_memory_save", {"kind": "template", "title": "mcp-secret", "form": {"doc_type": "resume", "locale": "ko-KR", "provider": "markdown"},
                                   "content": {"format": "markdown", "data": "# 양식\n\n본문\n\n" + S.value("bearer", 2)}})
        m.call("doc_memory_recall", {"url": "https://example.com/y?" + S.value("url_parts", 4), "doc_type": "resume"})
        m.call("doc_memory_import", {"url": docs, "as": "reference"})
    report = ctx.sweep(families=SECRETS + PII + LOCATORS, identities=("alice",), allow_empty=("logs_diagnostics", "cache"))
    ctx.expect(not report["empty"], f"a sweep that collected nothing in a sink proves nothing (HARN-14): empty sinks {report['empty']}")
    leaks = {sink: sorted({f.sentinel_id for f in found}) for sink, found in report["findings"].items()}
    ctx.expect(not leaks, f"sentinels found in sinks (ids only): {leaks}")
