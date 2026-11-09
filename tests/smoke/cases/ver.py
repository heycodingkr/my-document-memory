"""VER-01..VER-06: immutable versions and what each audience sees (docs/test/functional-tests.md, docs/spec/memory.md section 6, library.md)."""
import json

from dmtest.runner import case
from .util import recall, reject, save_md

DOCS = "docs.google.com/document/d/:id/edit"


def new_version(ctx, who, memory_id, base_version, text, title="수정본"):
    return ctx.cli(who).json(["save", "--kind", "template", "--title", title, "--doc-type", "resume", "--locale", "ko-KR", "--provider", "google_docs",
                              "--stdin", "--format", "markdown", "--memory", memory_id, "--base-version", str(base_version)], stdin=text)


def search_ids(ctx, who, scope="public"):
    r = ctx.cli(who).json(["search", "--scope", scope, "--limit", "20"])
    return {x["memory_id"]: x for x in (r.json or {}).get("results", [])}


@case("VER-01", "F", needs=("server", "hooks"))
def ver_01(ctx):
    ctx.load_library("shr-cat", identity="alice")
    first = ctx.cli("bob").json(["copy", "fx_s1"])
    ctx.expect(first.exit == 0 and first.json["derived_from"]["version"] == 1, f"the first copy points at version 1: {first.json}")
    v2 = new_version(ctx, "alice", "fx_s1", 1, "# 이력서\n\n## 경력\n수정된 경력 안내\n## 학력\n수정된 학력 안내", "공개 한국어 이력서 v2")
    ctx.expect(v2.exit == 0 and v2.json["version"] == 2, f"the owner saves version 2: {v2.json}")
    published = ctx.cli("alice").json(["publish", "fx_s1", "--visibility", "public", "--license", "CC-BY-4.0", "--consent", "--version", "2"])
    ctx.expect(published.exit == 0 and published.json["review_state"] == "queued", f"version 2 goes through review: {published.json}")
    ctx.cli("alice").json(["__test", "approve-all"])
    second = ctx.cli("bob").json(["copy", "fx_s1"])
    ctx.expect(second.exit == 0 and second.json["derived_from"]["version"] == 2, f"a new copy follows the published head (version 2): {second.json}")
    old = ctx.cli("bob").json(["expand", first.json["memory_id"], "--level", "1"])
    ctx.expect(old.exit == 0, "the earlier copy stays readable")
    all_copies = ctx.cli("bob").json(["search", "--scope", "mine", "--limit", "20"]).json["results"]
    versions = sorted(x["source"]["derived_from"]["version"] for x in all_copies if x["source"].get("derived_from"))
    ctx.expect(versions == [1, 2], f"the earlier copy still records derived_from.version 1 next to the new one's 2: {versions}")


@case("VER-02", "R1")
def ver_02(ctx):
    first = save_md(ctx, "# 양식\n\n## 경력\n첫 번째 내용", title="v1", extra=["--url-pattern", DOCS], provider="google_docs")
    ctx.expect(first.exit == 0, "save v1")
    memory = first.json["memory_id"]
    second = new_version(ctx, "local", memory, 1, "# 양식\n\n## 경력\n두 번째 내용", "v2")
    ctx.expect(second.exit == 0 and second.json["version"] == 2, f"save v2: {second.json}")
    texts = {n: [ctx.cli().json(["expand", memory, "--level", "2", "--version", str(n)]).stdout for _ in range(3)] for n in (1, 2)}
    ctx.expect(all(len(set(runs)) == 1 and runs[0] for runs in texts.values()), "the same version always returns byte-identical content")
    ctx.expect(texts[1][0] != texts[2][0] and "첫 번째" in texts[1][0] and "두 번째" in texts[2][0], "the two versions differ and each keeps its own content")


@case("VER-03", "R1")
def ver_03(ctx):
    saved = save_md(ctx, "# 양식\n\n## 경력\n첫 번째 내용", title="v1", extra=["--url-pattern", DOCS], provider="google_docs")
    memory = saved.json["memory_id"]
    new_version(ctx, "local", memory, 1, "# 양식\n\n## 경력\n두 번째 내용", "v2")
    hints = recall(ctx, DOCS, doc_type="resume", locale="ko-KR").json["hints"]
    ctx.expect([(h["memory_id"], h["version"]) for h in hints] == [(memory, 2)], f"only the head version is recalled: {[(h['memory_id'], h['version']) for h in hints]}")
    old = ctx.cli().json(["expand", memory, "--level", "1", "--version", "1"])
    ctx.expect(old.exit == 0 and old.json["version"] == 1, "the superseded version can still be expanded explicitly")


@case("VER-04", "F")
def ver_04(ctx):
    saved = save_md(ctx, "# 양식\n\n## 경력\n내용", title="v1", extra=["--url-pattern", DOCS], provider="google_docs")
    memory = saved.json["memory_id"]
    new_version(ctx, "local", memory, 1, "# 양식\n\n## 경력\n수정", "v2")
    ctx.expect(ctx.cli().json(["delete", memory, "--yes"]).exit == 0, "delete")
    for version in ("1", "2"):
        reject(ctx, ctx.cli().json(["expand", memory, "--level", "1", "--version", version]), "not_found", exit_code=7)
    reject(ctx, ctx.cli().json(["expand", memory, "--level", "1"]), "not_found", exit_code=7)


@case("VER-05", "F", needs=("server", "hooks"))
def ver_05(ctx):
    ctx.load_library("shr-cat", identity="alice")
    published = ctx.cli("alice").json(["publish", "fx_s5", "--visibility", "public", "--license", "CC-BY-4.0", "--consent"])
    ctx.expect(published.exit == 0 and published.json["review_state"] == "queued", f"publish version 1: {published.json}")
    ctx.cli("alice").json(["__test", "approve-all"])
    v2 = ctx.cli("alice").json(["save", "--kind", "template", "--title", "내부 이력서 v2", "--doc-type", "resume", "--locale", "ko-KR", "--provider", "markdown",
                                "--stdin", "--format", "markdown", "--memory", "fx_s5", "--base-version", "1"], stdin="# 이력서\n\n## 경력\n두 번째 버전")
    ctx.expect(v2.exit == 0 and v2.json["version"] == 2, f"save version 2: {v2.json}")
    seen = ctx.cli("anon").json(["expand", "fx_s5", "--level", "2"])
    ctx.expect(seen.exit == 0 and seen.json["version"] == 1 and "두 번째 버전" not in seen.stdout, "the public sees version 1 only; the new version is not published by saving it")
    again = ctx.cli("alice").json(["publish", "fx_s5", "--visibility", "public", "--license", "CC-BY-4.0", "--consent", "--version", "2"])
    ctx.expect(again.exit == 0 and again.json["review_state"] == "queued", f"publish version 2 explicitly: {again.json}")
    ctx.cli("alice").json(["__test", "approve-all"])
    after = ctx.cli("anon").json(["expand", "fx_s5", "--level", "2"])
    ctx.expect(after.exit == 0 and after.json["version"] == 2 and "두 번째 버전" in after.stdout, "after publishing version 2 the public sees it")


@case("VER-06", "F", needs=("server", "hooks"))
def ver_06(ctx):
    ctx.load_library("rcl-lib", identity="carol")
    hints = recall(ctx, DOCS, identity="carol", doc_type="resume", locale="ko-KR").json["hints"]
    ctx.expect(len(hints) >= 1 and hints[0].get("receipt_id"), "a linked recall returns receipts")
    receipt, shown = hints[0]["receipt_id"], hints[0]
    bad = ctx.cli("carol").json(["outcome", receipt, "success", "--used", f"{shown['memory_id']}@{shown['version'] + 5}"])
    reject(ctx, bad, "invalid_input")
    other = ctx.cli("carol").json(["outcome", receipt, "success", "--used", "fx_not_in_receipt@1"])
    reject(ctx, other, "invalid_input")
    good = ctx.cli("carol").json(["outcome", receipt, "success", "--used", f"{shown['memory_id']}@{shown['version']}"])
    ctx.expect(good.exit == 0 and good.json["recorded"] is True and good.json["duplicate"] is False, f"the refused calls recorded nothing, so the valid one is the first: {good.json}")
