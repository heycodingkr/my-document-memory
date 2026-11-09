"""TPL-01..TPL-08: the form flows the product is built for (docs/test/functional-tests.md, overview section 10 plus country/provider variants).

TPL-01..03 are the overview's own cases; TPL-04..08 add the per-country and per-provider differences.
"""
import json
import zipfile

from dmtest import builders
from dmtest.runner import case
from .util import recall, reject, save_md

DOCS = "docs.google.com/document/d/:id/edit"
SLIDES = "docs.google.com/presentation/d/:id/edit"
LETTER = {"size": "Letter", "orientation": "portrait"}


def stddoc(blocks, slots=(), page=None):
    return json.dumps({"schema": "stddoc/1", "type": "document", "page": page, "styles": {}, "blocks": blocks, "slots": list(slots), "rules": []}, ensure_ascii=False)


def heading(text, level=1):
    return {"type": "heading", "level": level, "text": text}


def save_doc(ctx, title, doc, *, doc_type="resume", locale="ko-KR", provider="google_docs", variant=None, patterns=(DOCS,), identity="local"):
    form = {"doc_type": doc_type, "locale": locale, "provider": provider}
    if variant:
        form["variant"] = variant
    with ctx.mcp(identity) as m:
        r = m.call("doc_memory_save", {"kind": "template", "title": title, "form": form, "url_patterns": list(patterns), "content": {"format": "stddoc", "data": doc}})
    ctx.expect(r is not None and not r.is_error, f"save {title}: {None if r is None else r.structured}")
    return (r.structured if r is not None and not r.is_error else {})


def structure(ctx, memory_id, who="local"):
    r = ctx.cli(who).json(["expand", memory_id, "--level", "2"])
    return ((r.json or {}).get("l2") or {}).get("structure") or {}, r


def write(ctx, name, data):
    path = ctx.home().parent / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


@case("TPL-01", "R1")
def tpl_01(ctx):
    source = write(ctx, "tpl01-monthly-report.docx", builders.tpl01())
    saved = ctx.cli().json(["save", "--kind", "template", "--title", "월간 보고서", "--doc-type", "report", "--locale", "ko-KR", "--provider", "docx", "--file", str(source)])
    ctx.expect(saved.exit == 0, f"upload failed: {saved.json}")
    shape, expanded = structure(ctx, saved.json["memory_id"])
    sections = [b["text"] for b in shape.get("blocks", []) if b.get("type") == "heading" and b["text"] != "월간 운영 보고서"]
    ctx.expect(sections == ["요약", "지표", "위험", "요청"], f"the section order survives extraction: {sections}")
    ctx.expect(shape.get("page", {}).get("size") == "Letter" and shape.get("styles"), f"page and styles are kept: {shape.get('page')} {sorted(shape.get('styles', {}))}")
    ctx.expect(saved.json["visibility"] == "private" and saved.json["memory_id"] in {x["memory_id"] for x in ctx.cli().json(["list"]).json["results"]}, "it is stored as a personal template")
    out = ctx.home().parent / "again.docx"
    exported = ctx.cli().json(["export", saved.json["memory_id"], "--format", "docx", "--out", str(out)])
    again = ctx.cli().json(["save", "--kind", "template", "--title", "새 문서", "--doc-type", "report", "--locale", "en-US", "--provider", "docx", "--file", str(out)])
    shape2, _ = structure(ctx, again.json["memory_id"]) if again.exit == 0 else ({}, None)
    ctx.expect(exported.exit == 0 and again.exit == 0 and [b["text"] for b in shape2.get("blocks", []) if b.get("type") == "heading" and b["text"] != "월간 운영 보고서"] == sections,
               "a new document started from the exported form keeps the section order")


@case("TPL-02", "F", needs=("server", "hooks"))
def tpl_02(ctx):
    ctx.load_library("shr-cat", identity="alice")
    found = {x["memory_id"]: x for x in ctx.cli("bob").json(["search", "--scope", "public", "--doc-type", "resume"]).json["results"]}
    ctx.expect("fx_s1" in found, "step 1: search finds the public resume form")
    before = ctx.cli("alice").json(["expand", "fx_s1", "--level", "2"]).stdout
    preview = ctx.cli("bob").json(["expand", "fx_s1", "--level", "1"])
    source = preview.json["source"]
    ctx.expect(preview.exit == 0 and source["author_handle"] == "alice" and source["license"] == "CC-BY-4.0" and preview.json["version"] == 1, f"step 2: the preview shows author, licence and version: {source}")
    start = ctx.cli("bob").json(["copy", "fx_s1"])
    ctx.expect(start.exit == 0 and start.json["derived_from"] == {"memory_id": "fx_s1", "version": 1, "author_handle": "alice", "license": "CC-BY-4.0"}, f"step 3: the usage record names author, licence and version: {start.json}")
    ctx.expect(start.json["memory_id"] in {x["memory_id"] for x in ctx.cli("bob").json(["list"]).json["results"]}, "bob now has his own copy")
    ctx.expect(ctx.cli("alice").json(["expand", "fx_s1", "--level", "2"]).stdout == before, "the original is untouched")


@case("TPL-03", "F", needs=("server", "hooks"))
def tpl_03(ctx):
    ctx.load_library("shr-cat", identity="alice")
    missing = lambda who, op: ctx.cli(who).json([op, "fx_nonexistent_zz"] + (["--level", "1"] if op == "expand" else []))  # noqa: E731
    for who in ("anon", "bob"):
        ctx.expect("fx_s4" not in {x["memory_id"] for x in ctx.cli(who).json(["search", "--scope", "all", "--limit", "20"]).json["results"]}, f"{who}: the team form is not listed")
        for op in ("expand", "copy"):
            mine = ctx.cli(who).json([op, "fx_s4"] + (["--level", "1"] if op == "expand" else []))
            reject(ctx, mine, "not_found", exit_code=7)
            ctx.expect(mine.stdout == missing(who, op).stdout, f"{who}/{op}: a team-only form must answer exactly like a missing one (existence stays hidden)")
        hints = recall(ctx, "example.com/team/quote", identity=who, doc_type="quote", locale="ko-KR").json["hints"]
        ctx.expect("fx_s4" not in {h["memory_id"] for h in hints}, f"{who}: recall does not return it")
    ctx.expect(ctx.cli("carol").json(["expand", "fx_s4", "--level", "1"]).exit == 0, "a team member still can read it")


@case("TPL-04", "F")
def tpl_04(ctx):
    kr = save_doc(ctx, "한국 이력서", stddoc([heading("이력서"), heading("인적사항", 2)], [{"name": n, "type": "text", "required": True} for n in ("name_ko", "phone", "address_kr")], {"size": "A4", "orientation": "portrait"}))
    us = save_doc(ctx, "US resume", stddoc([heading("Resume"), heading("Experience", 2)], [{"name": "name", "type": "text", "required": True}], LETTER), locale="en-US", variant="us_chronological")
    jp = save_doc(ctx, "履歴書", stddoc([heading("履歴書"), heading("学歴", 2)], [{"name": n, "type": "text", "required": True} for n in ("furigana", "birth_date")], {"size": "A4", "orientation": "portrait"}),
                  locale="ja-JP", variant="jp_rirekisho")
    ids = {kr.get("memory_id"), us.get("memory_id"), jp.get("memory_id")}
    ctx.expect(len(ids) == 3 and None not in ids, "three separate memories coexist")
    expect_slots = {"ko-KR": (kr, {"name_ko", "phone", "address_kr"}, "A4"), "en-US": (us, {"name"}, "Letter"), "ja-JP": (jp, {"furigana", "birth_date"}, "A4")}
    for locale, (memory, slots, paper) in expect_slots.items():
        shape, _ = structure(ctx, memory.get("memory_id", "missing"))
        ctx.expect({s["name"] for s in shape.get("slots", [])} == slots and shape.get("page", {}).get("size") == paper, f"{locale}: slots {sorted(s['name'] for s in shape.get('slots', []))} and page {shape.get('page')}")
        first = recall(ctx, DOCS, doc_type="resume", locale=locale).json["hints"][0]
        ctx.expect(first["memory_id"] == memory.get("memory_id"), f"{locale}: the exact-locale form is the first hint")
    ctx.expect("photo" not in {s["name"] for s in structure(ctx, us.get("memory_id", "missing"))[0].get("slots", [])} and "age" not in {s["name"] for s in structure(ctx, us.get("memory_id", "missing"))[0].get("slots", [])},
               "the US form has no photo or age slot")


@case("TPL-05", "F")
def tpl_05(ctx):
    memory = save_doc(ctx, "US Letter resume", stddoc([heading("Resume")], [{"name": "name", "type": "text", "required": True}], LETTER), locale="en-US")
    before = ctx.cli().json(["expand", memory["memory_id"], "--level", "2"]).stdout
    hint = recall(ctx, DOCS, doc_type="resume", locale="ko-KR").json["hints"][0]
    codes = {w["code"] for w in hint["warnings"]}
    ctx.expect({"paper_mismatch", "date_order_mismatch", "currency_mismatch", "name_order_mismatch"} <= codes, f"a US Letter form for a ko-KR task warns: {sorted(codes)}")
    shape, _ = structure(ctx, memory["memory_id"])
    ctx.expect(shape.get("page", {}).get("size") == "Letter", "expand shows the stored page size")
    ctx.expect(ctx.cli().json(["expand", memory["memory_id"], "--level", "2"]).stdout == before, "recalling never changes the form itself")


@case("TPL-06", "F")
def tpl_06(ctx):
    deck = json.dumps({"schema": "stddoc/1", "type": "deck", "theme": {"aspect": "16:9"}, "slides": [{"index": 1, "role": "cover", "layout": "title_body", "title": "표지", "blocks": []}]}, ensure_ascii=False)
    for provider in ("google_slides", "pptx"):  # host-wide patterns: the decks are route candidates for ANY docs.google.com URL, so only the form can keep them out
        save_doc(ctx, f"deck {provider}", deck, doc_type="pitch_deck", locale="en-US", provider=provider, patterns=("docs.google.com/*",))
    hints = recall(ctx, SLIDES, doc_type="pitch_deck", locale="en-US", provider="google_slides").json["hints"]
    ctx.expect([h["form"]["provider"] for h in hints] == ["google_slides", "pptx"], f"the exact provider ranks first: {[h['form']['provider'] for h in hints]}")
    for fields in ({"doc_type": "resume", "locale": "en-US"}, {}):
        r = recall(ctx, DOCS, **fields)
        ctx.expect(r.exit == 0 and r.json["hints"] == [], f"a document-family query {fields} must not return decks: {[h['title'] for h in (r.json or {}).get('hints', [])]}")


@case("TPL-07", "F")
def tpl_07(ctx):
    doc = stddoc([heading("보고서"), {"type": "paragraph", "text": "작성자: {{name}}"}, {"type": "paragraph", "text": "작성일: {{date}}"}],
                 [{"name": "name", "type": "text", "required": True}, {"name": "date", "type": "date", "required": True}])
    memory = save_doc(ctx, "슬롯 양식", doc, doc_type="report")
    out = ctx.home().parent / "slots.md"
    exported = ctx.cli().json(["export", memory["memory_id"], "--format", "md", "--out", str(out)])
    text = out.read_text(encoding="utf-8") if out.is_file() else ""
    ctx.expect(exported.exit == 0 and "{{name}}" in text and "{{date}}" in text, "the placeholders stay in the exported Markdown")
    shape, _ = structure(ctx, memory["memory_id"])
    ctx.expect({s["name"]: s["required"] for s in shape.get("slots", [])} == {"name": True, "date": True}, f"slots[].required matches: {shape.get('slots')}")


@case("TPL-08", "F")
def tpl_08(ctx):
    source = write(ctx, "deck-5.pptx", builders.deck5())
    saved = ctx.cli().json(["save", "--kind", "template", "--title", "덱", "--doc-type", "pitch_deck", "--locale", "en-US", "--provider", "pptx", "--file", str(source)])
    ctx.expect(saved.exit == 0, f"deck upload failed: {saved.json}")
    first, _ = structure(ctx, saved.json["memory_id"])
    out = ctx.home().parent / "deck-out.pptx"
    exported = ctx.cli().json(["export", saved.json["memory_id"], "--format", "pptx", "--out", str(out)])
    valid = exported.exit == 0 and zipfile.is_zipfile(out)
    count = 0
    if valid:
        with zipfile.ZipFile(out) as z:
            count = len([n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")])
    ctx.expect(valid and count == 5, f"a valid PPTX with 5 slides: valid={valid} slides={count}")
    again = ctx.cli().json(["save", "--kind", "template", "--title", "덱 다시", "--doc-type", "pitch_deck", "--locale", "ko-KR", "--provider", "pptx", "--file", str(out)])
    second, _ = structure(ctx, again.json["memory_id"]) if again.exit == 0 else ({}, None)
    roles = lambda s: [x["role"] for x in s.get("slides", [])]  # noqa: E731
    ctx.expect(roles(first)[:1] == ["cover"] and "ask" in roles(first) and "problem" in roles(first), f"the roles of the original: {roles(first)}")
    ctx.expect(roles(second) == roles(first) and [x.get("title") for x in second.get("slides", [])] == [x.get("title") for x in first.get("slides", [])], f"re-import keeps roles and titles: {roles(second)}")
