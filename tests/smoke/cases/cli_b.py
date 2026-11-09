"""CLI-08..CLI-31 (the L2-automatable rows of docs/test/tool-forms/cli-form.md that are not already a feature case).

Most rows trace to a feature case (RCL, SHR, IMP, ...); these check them again as the CLI's own contract: exit codes, --json shape, no prompts, no colour.
"""
import json
import re

from dmtest.runner import case
from .util import recall, reject, save_md

DOCS = "docs.google.com/document/d/:id/edit"


def seed(ctx, n=2, who="local"):
    for i in range(n):
        save_md(ctx, f"# 이력서 {i}\n\n## 경력\n내용 {i}", title=f"양식 {i}", extra=["--url-pattern", DOCS, "--variant", f"v{i}"], provider="google_docs", identity=who)


@case("CLI-08", "R1")
def cli_08(ctx):
    seed(ctx, 5)
    r = recall(ctx, DOCS, doc_type="resume", locale="ko-KR")
    ctx.expect(r.exit == 0 and len(r.json["hints"]) == 3, "at most three hints, exit 0")
    for h in r.json["hints"]:
        ctx.expect({"matched_on", "scope", "version", "locale_match"} <= set(h) and "receipt_id" not in h, f"each hint has its match information and no receipt: {sorted(h)}")
    ctx.expect(r.json["untrusted"] is True and r.json["framing"].startswith("UNTRUSTED REFERENCE DATA"), "untrusted framing")


@case("CLI-09", "R1")
def cli_09(ctx):
    r = recall(ctx, "example.com/never-saved", doc_type="proposal", locale="ko-KR")
    ctx.expect(r.exit == 0 and r.json["hints"] == [] and r.json["reason"] == "no_match", "an unknown URL/form is an empty result, not an error")


@case("CLI-10", "R1")
def cli_10(ctx):
    vocab = ctx.cli().json(["vocab"])
    ctx.expect(vocab.exit == 0 and "keywords" in vocab.json, f"`dmem vocab` lists the vocabularies: {sorted(vocab.json or {})}")
    save_md(ctx, "# 메모\n\n본문", title="내 키워드", doc_type="memo", extra=["--url-pattern", "example.com/*", "--keyword", "내전용키워드"])
    local = ctx.cli().json(["recall", "example.com/x", "내전용키워드", "--doc-type", "memo", "--scope", "mine"])
    ctx.expect(local.exit == 0 and local.json["hints"] and "keywords" in local.json["hints"][0]["matched_on"], "a local (mine) recall accepts any keyword")
    ctx.expect("keyword" not in local.stderr.lower(), "and says nothing about vocabulary")
    box = ctx.target.sandbox(server=True)
    try:
        remote = box.cli("alice").json(["recall", "example.com/x", "내전용키워드", "--scope", "all"])
        ctx.expect(remote.exit == 0 and "keyword" in remote.stderr.lower() and "내전용키워드" not in remote.stderr, "a remote scope drops it and tells the user on stderr without echoing it")
    finally:
        box.close()


@case("CLI-11", "R1")
def cli_11(ctx):
    seed(ctx, 1)
    memory = ctx.cli().json(["list"]).json["results"][0]["memory_id"]
    ctx.expect(ctx.cli().json(["expand", memory, "--level", "1"]).json["l2"] is None, "level 1 carries no L2")
    ctx.expect(ctx.cli().json(["expand", memory, "--level", "2"]).json["l2"] is not None, "level 2 does")
    reject(ctx, ctx.cli().json(["expand", memory, "--level", "3"]), "invalid_input")
    reject(ctx, ctx.cli().json(["expand", memory, "--level", "1", "--version", "9"]), "not_found", exit_code=7)


@case("CLI-12", "R1")
def cli_12(ctx):
    seed(ctx, 3)
    listed = ctx.cli().json(["list"])
    ctx.expect(listed.exit == 0 and len(listed.json["results"]) == 3 and listed.json["remote"] is False, "list shows the local library and remote=false")
    ctx.expect(all({"memory_id", "version", "kind", "title", "form", "source"} <= set(x) for x in listed.json["results"]), "each result has its fields")
    for scope in ("public", "team"):
        r = ctx.cli().json(["search", "--scope", scope])
        ctx.expect(r.exit == 0 and r.json["results"] == [] and r.json["reason"] == "scope_unavailable_local", f"local {scope}: scope_unavailable_local")
    page = ctx.cli().json(["list", "--limit", "2"])
    ctx.expect(len(page.json["results"]) == 2 and page.json.get("next_cursor"), "a limit paginates with a cursor")


@case("CLI-13", "F", needs=("server", "hooks"))
def cli_13(ctx):
    ctx.load_library("shr-cat", identity="alice")
    copied = ctx.cli("bob").json(["copy", "fx_s1"])
    ctx.expect(copied.exit == 0 and copied.json["visibility"] == "private" and copied.json["derived_from"]["memory_id"] == "fx_s1", f"a private copy that remembers its origin: {copied.json}")
    over = ctx.cli("bob").json(["copy", "fx_s3", "--copy-mode", "full"])
    ctx.expect(over.exit == 4 and over.json["error"]["allowed_modes"] == ["structure_only"], f"a mode above the ceiling exits 4 with allowed_modes: {over.json}")


@case("CLI-14", "F", needs=("server", "hooks"))
def cli_14(ctx):
    ctx.load_library("shr-cat", identity="alice")
    before = len([e for e in ctx.request_log() if e["write"]])
    no = ctx.cli("alice").json(["publish", "fx_s5", "--visibility", "public", "--license", "CC-BY-4.0"])
    ctx.expect(no.exit == 4 and no.code == "consent_required" and len([e for e in ctx.request_log() if e["write"]]) == before, "without consent: exit 4 and no write")
    yes = ctx.cli("alice").json(["publish", "fx_s5", "--visibility", "public", "--license", "CC-BY-4.0", "--consent"])
    ctx.expect(yes.exit == 0 and yes.json["review_state"] == "queued", "with consent: into the review queue")
    ctx.expect(ctx.cli("alice").json(["publish", "fx_s5", "--visibility", "private"]).exit == 0, "private needs no consent")


@case("CLI-15", "F", needs=("server", "hooks"))
def cli_15(ctx):
    ctx.load_library("shr-cat", identity="alice")
    before = len([e for e in ctx.request_log() if e["write"]])
    for args in (["publish", "fx_s1", "--visibility", "private"], ["outcome", "rcpt_x", "success"]):
        r = ctx.cli("anon").json(args)
        ctx.expect(r.exit == 3 and r.code == "auth_required", f"anonymous {args[0]}: exit 3")
    ctx.expect(len([e for e in ctx.request_log() if e["write"]]) == before, "no server write")
    ctx.expect(ctx.cli("anon").json(["copy", "fx_s1"]).exit == 0, "an anonymous copy goes to the local library")


@case("CLI-16", "R1")
def cli_16(ctx):
    seed(ctx, 1)
    memory = ctx.cli().json(["list"]).json["results"][0]["memory_id"]
    reject(ctx, ctx.cli().json(["delete", memory]), "invalid_input")  # no --yes, no terminal: it must not wait for an answer
    ctx.expect(ctx.cli().json(["expand", memory, "--level", "1"]).exit == 0, "nothing was deleted")
    ctx.expect(ctx.cli().json(["delete", memory, "--yes"]).exit == 0, "with --yes it is deleted")
    reject(ctx, ctx.cli().json(["expand", memory, "--level", "1"]), "not_found", exit_code=7)


@case("CLI-17", "F", needs=("fixtures",))
def cli_17(ctx):
    p = ctx.cli().json(["web", "preview", ctx.fx_url + "/pages/resume-ko.html"])
    ctx.expect(p.exit == 0 and ctx.cli().json(["list"]).json["results"] == [], "a preview stores nothing")
    full = ctx.cli().json(["import", ctx.fx_url + "/pages/resume-ko.html", "--as", "template"])
    only = ctx.cli().json(["import", ctx.fx_url + "/pages/license-none.html", "--as", "template"])
    ctx.expect(full.json["copy_policy_applied"] == "full" and only.json["copy_policy_applied"] == "structure_only", "the licence decides the copy policy")
    via = ctx.cli().json(["import", "--preview", p.json["preview_id"], "--as", "reference"])
    ctx.expect(via.exit in (0, 2), "importing by preview id is accepted by the CLI grammar")


@case("CLI-18", "F", needs=("fixtures",))
def cli_18(ctx):
    reject(ctx, ctx.cli().json(["web", "search", "이력서"]), "search_unavailable", exit_code=5)
    ctx.search_provider("fixture")
    ok = ctx.cli().json(["web", "search", "이력서", "--limit", "3"])
    ctx.expect(ok.exit == 0 and 0 < len(ok.json["candidates"]) <= 3 and all("?" not in c["url"] for c in ok.json["candidates"]), "candidates with canonical URLs")
    reject(ctx, ctx.cli().json(["web", "search", ctx.sentinels.value("api_key", 1)]), "secret_detected")


@case("CLI-19", "R1")
def cli_19(ctx):
    q, f = ctx.sentinels.value("url_parts", 1), ctx.sentinels.value("url_parts", 2)
    r = ctx.cli().json(["recall", f"https://example.com/x?{q}#{f}"])
    ctx.expect(r.exit == 0 and q not in r.stdout + r.stderr and f not in r.stdout + r.stderr, "a URL with query and fragment is shortened before anything is printed")
    for payload in ("not json", json.dumps({"url": "example.com/x", "unknown_field": q}), json.dumps({"url": "example.com/x", "limit": 99})):
        bad = ctx.cli().json(["recall", "--stdin"], stdin=payload)
        ctx.expect(bad.exit == 2 and q not in bad.stdout + bad.stderr, f"--stdin: invalid input exits 2 without echoing it ({payload[:12]}...)")
    ctx.expect(ctx.cli().json(["recall", "--stdin"], stdin="x" * (70 * 1024)).exit == 2, "an oversized stdin body is refused")


@case("CLI-21", "R1")
def cli_21(ctx):
    seed(ctx, 1)
    ctx.expect(ctx.cli().json(["list"]).exit == 0 and ctx.cli().json(["recall", DOCS, "--scope", "mine"]).exit == 0, "with no server the local list and recall work")
    ctx.expect(save_md(ctx, "# 오프라인\n\n본문", title="offline", doc_type="memo", extra=["--url-pattern", "example.com/*"]).exit == 0, "and a local save works")
    r = ctx.cli().json(["publish", "mem_x", "--visibility", "public", "--license", "CC0-1.0", "--consent"])
    ctx.expect(r.exit == 3, f"a server-only command says authentication is needed, it does not hang or crash: exit {r.exit}")


@case("CLI-22", "R1")
def cli_22(ctx):
    seed(ctx, 1)
    memory = ctx.cli().json(["list"]).json["results"][0]["memory_id"]
    import stat
    for fmt in ("md", "html", "docx", "json"):
        path = ctx.home().parent / f"out.{fmt}"
        r = ctx.cli().json(["export", memory, "--format", fmt, "--out", str(path)])
        ctx.expect(r.exit == 0 and path.is_file() and stat.S_IMODE(path.stat().st_mode) == 0o600, f"{fmt}: created with mode 0600")
        again = ctx.cli().json(["export", memory, "--format", fmt, "--out", str(path)])
        ctx.expect(again.exit == 2, f"{fmt}: an existing file is never overwritten")
    ctx.expect(ctx.cli().json(["export", memory, "--format", "md", "--out", "relative.md"]).exit == 2, "a relative path is refused")


@case("CLI-23", "F", needs=("server", "hooks"))
def cli_23(ctx):
    ctx.load_library("rcl-lib", identity="carol")
    hint = ctx.cli("carol").json(["recall", "--stdin"], stdin=json.dumps({"url": DOCS, "doc_type": "resume", "locale": "ko-KR"})).json["hints"][0]
    rid = hint["receipt_id"]
    ctx.expect(ctx.cli("carol").json(["outcome", rid, "great"]).exit == 2, "an outcome outside the enum exits 2")
    ctx.expect(ctx.cli("carol").json(["outcome", "r" * 129, "success"]).exit == 2, "a receipt id over 128 characters exits 2")
    ctx.expect(ctx.cli("carol").json(["outcome", rid, "success", "--used", "fx_nope@1"]).exit == 2, "a version outside the receipt exits 2")
    ok = ctx.cli("carol").json(["outcome", rid, "success", "--used", f"{hint['memory_id']}@{hint['version']}"])
    again = ctx.cli("carol").json(["outcome", rid, "success", "--used", f"{hint['memory_id']}@{hint['version']}"])
    ctx.expect(ok.json["duplicate"] is False and again.json["duplicate"] is True, "resending the same result is a duplicate")
    ctx.expect(ctx.cli("bob").json(["outcome", rid, "success"]).exit == 7, "another user's receipt exits 7")


@case("CLI-25", "R1")
def cli_25(ctx):
    seed(ctx, 1)
    memory = ctx.cli().json(["list"]).json["results"][0]["memory_id"]
    r = ctx.cli().run(["delete", memory], timeout=10.0)
    ctx.expect(not r.timed_out and r.exit == 2, f"a command that needs confirmation never waits for a terminal (exit {r.exit}, timed out: {r.timed_out})")


@case("CLI-27", "R1")
def cli_27(ctx):
    seed(ctx, 1)
    for args in (["status"], ["list"], ["recall", DOCS], ["expand", "mem_missing", "--level", "1"], ["publish", "x", "--visibility", "bogus"], ["vocab"]):
        r = ctx.cli().json(args)
        ctx.expect(r.json is not None and r.json.get("schema_version") == 1, f"{args[0]}: stdout is exactly one JSON document with schema_version 1 (exit {r.exit})")
        if r.exit != 0:
            ctx.expect("error" in r.json and r.json["error"]["code"], f"{args[0]}: an error is also a JSON document on stdout")


@case("CLI-28", "R1")
def cli_28(ctx):
    seed(ctx, 1)
    for args in (["--help"], ["status"], ["list"], ["expand", "mem_missing", "--level", "1"]):
        r = ctx.cli(extra_env={"NO_COLOR": "1"}).run(args)
        ctx.expect("\x1b[" not in r.stdout + r.stderr, f"{args[0]}: no ANSI escapes without a terminal")


@case("CLI-31", "F", needs=("server", "hooks"))
def cli_31(ctx):
    for who in ("alice", "anon"):
        cli = ctx.cli(who).json(["status"]).json
        with ctx.mcp(who) as m:
            mcp = m.call("doc_memory_status", {}).structured
        ctx.expect({k for k in cli} == {k for k in mcp}, f"{who}: the CLI and the MCP tool report the same fields")
        ctx.expect({"mode", "auth", "consent", "vocab", "search_provider", "isolated", "data_dir"} <= set(cli), f"{who}: the documented fields are there")
        ctx.expect(not re.search(r"@|token|email|account", json.dumps({k: v for k, v in cli.items() if k != "data_dir"}).lower()), f"{who}: no email, account id or token")
    ctx.expect(ctx.cli("anon").json(["status"]).json["auth"] == "anonymous" and ctx.cli("alice").json(["status"]).json["auth"] == "linked", "anonymous and linked are told apart")
