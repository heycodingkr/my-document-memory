"""SMK-01..SMK-16: the local smoke journeys (docs/test/local-smoke.md, docs/test/host-smoke.md).

These run a user's path end to end through the CLI and the stdio MCP server and the loopback fixture server, without any host application. They reuse the
behaviour the feature cases prove in depth; what they add is that the whole path holds together. SMK-06, SMK-10, SMK-12 (device flow) and SMK-15 need a host or
a product build and are listed in tests/coverage.json with their reason.
"""
import hashlib
import json
import stat

from dmtest import builders
from dmtest.runner import case
from .util import recall
from .sec import sec_a04

DOCS = "docs.google.com/document/d/:id/edit"
COMMANDS = ("recall", "search", "list", "expand", "save", "web search", "web preview", "import", "copy", "publish", "delete", "outcome", "export", "status", "vocab",
            "link", "unlink", "doctor", "install", "uninstall")


@case("SMK-01", "R1")
def smk_01(ctx):
    version, help_ = ctx.cli().run(["--version"]), ctx.cli().run(["--help"])
    ctx.expect(version.exit == 0 and "dmem" in version.stdout.lower(), "--version exits 0")
    ctx.expect(help_.exit == 0 and all(name in help_.stdout for name in COMMANDS), "--help names every command of cli.md section 2")
    ctx.expect(ctx.cli().run(["no-such-command"]).exit == 2, "an unknown sub-command exits 2")
    ctx.expect(not ctx.scan_sinks(("local",), families=("api_key", "jwt", "bearer", "private_key")), "no secret in the output")
    m = ctx.mcp()
    ctx.expect(m.ping(), "dmem-mcp starts and answers")
    m.proc.p.stdin.close()
    try:
        m.proc.p.wait(timeout=5)
    except Exception:
        pass
    ctx.expect(m.proc.p.poll() == 0, "and exits 0 when its input ends")


@case("SMK-02", "R1")
def smk_02(ctx):
    with ctx.mcp(initialize=False) as m:
        init = m.initialize()
        tools = m.list_tools()
        names = [t["name"] for t in tools]
        ctx.expect(len(tools) == 12 and all(n.startswith("doc_memory_") for n in names) and len(set(names)) == 12, f"twelve doc_memory_* tools: {names}")
        reads = {t["name"] for t in tools if t["annotations"].get("readOnlyHint")}
        ctx.expect(reads == {"doc_memory_status", "doc_memory_recall", "doc_memory_search", "doc_memory_expand", "doc_memory_web_search", "doc_memory_web_preview"}, "read/write annotations")
        ctx.expect(m.noise_bytes == 0, "stdout is JSON-RPC only")
        size = len(json.dumps({"tools": tools, "instructions": init["result"]["instructions"]}, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        ctx.expect(size <= 12000, f"the catalogue is {size} bytes (budget 12,000)")


@case("SMK-03", "F", needs=("server", "hooks"))
def smk_03(ctx):
    ctx.load_library("rcl-lib", identity="carol")
    query = {"url": "https://docs.google.com/document/d/FIXTURE_DOC_ID_0123456789ABCDEFGHIJKLMNOPQ/edit?usp=sharing", "doc_type": "resume", "locale": "ko-KR"}
    canonical = {"url": DOCS, "doc_type": "resume", "locale": "ko-KR"}
    ids = lambda r: [h["memory_id"] for h in r.json["hints"]]  # noqa: E731
    raw, plain = ctx.cli("carol").json(["recall", "--stdin"], stdin=json.dumps(query)), ctx.cli("carol").json(["recall", "--stdin"], stdin=json.dumps(canonical))
    ctx.expect(ids(raw) == ids(plain) == ["fx_m1", "fx_m4", "fx_m5"], f"a raw and a canonical URL give the same order (RCL-01): {ids(raw)}")
    ctx.expect(raw.json["untrusted"] is True and len(raw.json["hints"]) <= 3 and all(h.get("receipt_id") for h in raw.json["hints"]), "untrusted, at most 3, receipts for the linked caller")
    with ctx.mcp("carol") as m:
        via = m.call("doc_memory_recall", canonical)
        ctx.expect([h["memory_id"] for h in via.structured["hints"]] == ids(plain), "MCP gives the CLI's hints in the CLI's order")
    anon = ctx.cli("anon").json(["recall", "--stdin"], stdin=json.dumps(canonical))
    ctx.expect(anon.exit == 0 and all("receipt_id" not in h for h in anon.json["hints"]), "an anonymous caller gets no receipts")


@case("SMK-04", "R1")
def smk_04(ctx):
    cli = recall(ctx, "example.com/never-saved", doc_type="proposal", locale="ko-KR")
    with ctx.mcp() as m:
        mcp = m.call("doc_memory_recall", {"url": "example.com/never-saved", "doc_type": "proposal", "locale": "ko-KR"})
    ctx.expect(cli.exit == 0 and cli.json["hints"] == [] and cli.json["reason"] == "no_match", "CLI: empty result, no_match, exit 0")
    ctx.expect(not mcp.is_error and mcp.structured["hints"] == [] and mcp.structured["reason"] == "no_match", "MCP: the same, and not an error")


@case("SMK-05", "R1")
def smk_05(ctx):
    sentinel = ctx.sentinels.value("prose", 6)  # L2_ONLY_SENTINEL
    saved = ctx.cli().json(["save", "--kind", "template", "--title", "양식", "--doc-type", "resume", "--locale", "ko-KR", "--provider", "markdown", "--stdin", "--format", "markdown"],
                           stdin=f"# 양식\n\n## 경력\n{sentinel} 본문")
    memory = saved.json["memory_id"]
    l1, l2 = ctx.cli().json(["expand", memory, "--level", "1"]), ctx.cli().json(["expand", memory, "--level", "2"])
    ctx.expect(sentinel not in l1.stdout and sentinel in l2.stdout, "the L2-only sentinel appears at level 2 only")
    ctx.expect({"author_handle", "license", "origin"} <= set(l1.json["source"]) and l1.json["version"] == 1, "level 1 carries the summary, source, licence and version")
    ctx.expect(sentinel not in recall(ctx, DOCS, doc_type="resume").stdout, "and recall never shows it")
    with ctx.mcp() as m:
        ctx.expect(sentinel not in m.call("doc_memory_expand", {"memory_id": memory, "level": 1}).text and sentinel in m.call("doc_memory_expand", {"memory_id": memory, "level": 2}).text, "MCP agrees")


@case("SMK-07", "R1")
def smk_07(ctx):
    source = ctx.home().parent / "resume-ko.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(builders.resume_ko_md())
    args = ["save", "--kind", "template", "--title", "내 이력서", "--doc-type", "resume", "--locale", "ko-KR", "--provider", "markdown", "--file", str(source)]
    dry = ctx.cli().json(args + ["--dry-run"])
    ctx.expect(dry.exit == 0 and dry.json["dry_run"] is True and ctx.cli().json(["list"]).json["results"] == [], "a dry run stores nothing")
    first, again = ctx.cli().json(args), ctx.cli().json(args)
    ctx.expect(first.exit == 0 and first.json["visibility"] == "private" and again.json["created"] is False and again.json["memory_id"] == first.json["memory_id"], "stored privately; the same content again is created:false")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    original = ctx.home() / "originals" / digest
    ctx.expect(original.is_file() and stat.S_IMODE(original.stat().st_mode) == 0o600, "the original is kept with mode 0600")
    memory = first.json["memory_id"]
    ctx.expect(ctx.cli().json(["list"]).json["results"][0]["memory_id"] == memory and ctx.cli().json(["expand", memory, "--level", "2"]).exit == 0, "list and expand")
    out = ctx.home().parent / "exported.md"
    ctx.expect(ctx.cli().json(["export", memory, "--format", "md", "--out", str(out)]).exit == 0 and stat.S_IMODE(out.stat().st_mode) == 0o600 and "{{name}}" in out.read_text(encoding="utf-8"), "export writes a private Markdown file")
    ctx.expect(ctx.cli().json(["delete", memory, "--yes"]).exit == 0 and ctx.cli().json(["expand", memory, "--level", "1"]).exit == 7 and not original.exists(), "delete removes it, the original included; expand then exits 7")


@case("SMK-08", "F", needs=("server", "hooks"))
def smk_08(ctx):
    ctx.load_library("shr-cat", identity="alice")
    before = ctx.cli("alice").json(["expand", "fx_s1", "--level", "2"]).stdout
    found = ctx.cli("bob").json(["search", "--scope", "public", "--limit", "20"])
    item = next((x for x in found.json["results"] if x["memory_id"] == "fx_s1"), None)
    ctx.expect(item is not None and item["source"]["author_handle"] == "alice" and item["source"]["license"] == "CC-BY-4.0" and item["version"] == 1, "the search result shows author, licence and version")
    ctx.expect(ctx.cli("bob").json(["expand", "fx_s1", "--level", "1"]).exit == 0, "expand")
    copied = ctx.cli("bob").json(["copy", "fx_s1"])
    ctx.expect(copied.exit == 0 and copied.json["visibility"] == "private" and copied.json["derived_from"]["author_handle"] == "alice", "the copy is private and remembers its author")
    ctx.expect(copied.json["memory_id"] in {x["memory_id"] for x in ctx.cli("bob").json(["list"]).json["results"]}, "it is in bob's library")
    ctx.expect(ctx.cli("alice").json(["expand", "fx_s1", "--level", "2"]).stdout == before, "the original is untouched")


@case("SMK-09", "F", needs=("fixtures",))
def smk_09(ctx):
    ctx.search_provider("fixture")
    found = ctx.cli().json(["web", "search", "이력서 양식", "--limit", "5"])
    ctx.expect(found.exit == 0 and found.json["candidates"] and all("?" not in c["url"] for c in found.json["candidates"]), "web search returns canonical candidate URLs")
    preview = ctx.cli().json(["web", "preview", ctx.fx_url + "/pages/resume-ko.html"])
    ctx.expect(preview.exit == 0 and ctx.cli().json(["list"]).json["results"] == [], "a preview stores nothing")
    full = ctx.cli().json(["import", ctx.fx_url + "/pages/resume-ko.html", "--as", "template"])
    only = ctx.cli().json(["import", ctx.fx_url + "/pages/license-none.html", "--as", "template"])
    ctx.expect(full.json["copy_policy_applied"] == "full" and only.json["copy_policy_applied"] == "structure_only", "CC-BY is full; no licence is structure only")
    ctx.expect("PROSE_SENTINEL" not in ctx.cli().json(["expand", only.json["memory_id"], "--level", "2"]).stdout, "the structure-only import holds no prose")
    hostile = ctx.cli().json(["import", ctx.fx_url + "/pages/hostile-inject.html", "--as", "template"])
    stored = ctx.cli().json(["expand", hostile.json["memory_id"], "--level", "2"]).stdout
    ctx.expect(hostile.exit == 0 and "HIDDEN_SENTINEL" not in stored and "<script" not in stored, "hidden and active content is not stored")
    names = {n.lower() for e in ctx.fx_log() for n in e["header_names"]}
    ctx.expect(ctx.fx_log() and not ({"cookie", "authorization"} & names), "no credential header went to the site")


@case("SMK-11", "F", needs=("server", "hooks"))
def smk_11(ctx):
    ctx.load_library("shr-cat", identity="alice")
    writes = len([e for e in ctx.request_log() if e["write"]])
    no = ctx.cli("alice").json(["publish", "fx_s5", "--visibility", "public", "--license", "CC-BY-4.0"])
    ctx.expect(no.exit == 4 and len([e for e in ctx.request_log() if e["write"]]) == writes, "without consent: exit 4, no write")
    yes = ctx.cli("alice").json(["publish", "fx_s5", "--visibility", "public", "--license", "CC-BY-4.0", "--consent"])
    ctx.expect(yes.exit == 0 and yes.json["review_state"] in ("queued", "approved"), f"with consent: {yes.json}")
    ctx.cli("alice").json(["__test", "approve-all"])
    seen = next((x for x in ctx.cli("anon").json(["search", "--scope", "public", "--limit", "20"]).json["results"] if x["memory_id"] == "fx_s5"), None)
    ctx.expect(seen is not None and seen["source"]["author_handle"] == "alice" and seen["source"]["license"] == "CC-BY-4.0" and seen["version"] == 1, "author, licence and version show in the public search")


@case("SMK-12", "F", needs=("server", "hooks"))
def smk_12(ctx):
    writes = len([e for e in ctx.request_log() if e["write"]])
    for who in ("anon", "local"):
        for args in (["publish", "fx_s1", "--visibility", "private"], ["outcome", "rcpt_x", "success"]):
            ctx.expect(ctx.cli(who).json(args).exit == 3, f"{who} {args[0]} without a link: exit 3")
    ctx.expect(len([e for e in ctx.request_log() if e["write"]]) == writes, "and no server write")
    ctx.expect(ctx.cli("anon").json(["search", "--scope", "public"]).exit == 0, "anonymous reading stays possible")


@case("SMK-13", "F", needs=("server", "hooks"))
def smk_13(ctx):
    ctx.load_library("shr-cat", identity="alice")
    down = {"DMEM_TEST_SERVER_DOWN": "1"}
    saved = ctx.cli("anon", down).json(["save", "--kind", "template", "--title", "로컬", "--doc-type", "memo", "--locale", "ko-KR", "--provider", "markdown", "--stdin", "--format", "markdown"], stdin="# 메모\n\n본문입니다")
    ctx.expect(saved.exit == 0, f"with the server down a local save still works: {saved.code}")
    ctx.expect(len(ctx.cli("anon", down).json(["list"]).json["results"]) == 1, "and the local library lists")
    ctx.expect(ctx.cli("anon", down).json(["recall", "example.com/x", "--scope", "mine"]).exit == 0, "a mine-scope recall works")
    gone = ctx.cli("anon", down).json(["search", "--scope", "public"])
    ctx.expect(gone.exit == 5 and gone.code == "server_unavailable", f"a command that needs the server exits 5: {gone.exit} {gone.code}")
    ctx.expect(ctx.cli("anon").json(["search", "--scope", "public"]).exit == 0, "and recovers when the server is back")


@case("SMK-14", "R1")
def smk_14(ctx):
    box = ctx.target.sandbox(server=False)
    cli, session = box.cli("local"), box.mcp("local")
    session.initialize()
    cli.json(["status"])
    root, child = box.tmp, session.proc.p
    box.close()
    ctx.expect(child.poll() is not None, "the MCP server this smoke started is gone")
    ctx.expect(not root.exists(), "and its disposable directory too")


@case("SMK-16", "F", needs=("server", "hooks", "fixtures"))
def smk_16(ctx):
    sec_a04(ctx)  # the eight-sink sentinel sweep after a session of sentinel-bearing inputs
