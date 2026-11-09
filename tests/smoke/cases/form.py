"""FORM-01..FORM-16: form normalisation, locale matching and convention warnings (docs/spec/form.md)."""
import json

from dmtest.runner import case
from .util import recall, reject, save_md

DOCS = "docs.google.com/document/d/:id/edit"


def form_of(ctx, **fields):
    r = recall(ctx, DOCS, **fields)
    return r, ((r.json or {}).get("form") or {})


@case("FORM-01", "R1")
def form_01(ctx):
    r, form = form_of(ctx, provider="notion")
    ctx.expect(r.exit == 0 and form.get("provider") == "notion", "an explicit provider must win over the detected one without an error")


@case("FORM-02", "R1")
def form_02(ctx):
    for value, expected in [("이력서", "resume"), ("Resume", "resume"), ("RESUME ", "resume"), ("ＲＥＳＵＭＥ", "resume"), ("견적서", "quote"), ("見積書", "quote"),
                            ("angebot", "quote"), ("회의록", "meeting_minutes"), ("議事録", "meeting_minutes"), ("교안", "lesson_plan")]:
        r, form = form_of(ctx, doc_type=value)
        ctx.expect(r.exit == 0 and form.get("doc_type") == expected, f"alias {expected}")


@case("FORM-03", "R1")
def form_03(ctx):
    for value, doc, variant in [("履歴書", "resume", "jp_rirekisho"), ("세금계산서", "invoice", "kr_tax_invoice"), ("適格請求書", "invoice", "jp_qualified"), ("cv", "resume", "cv")]:
        r = save_md(ctx, f"# {value}\n\n본문", doc_type=value, title=f"t-{variant}")
        ctx.expect(r.exit == 0 and r.json["form"]["doc_type"] == doc and r.json["form"]["variant"] == variant, f"alias {value} must imply variant {variant}")
    r = save_md(ctx, "# 履歴書\n\n본문", doc_type="履歴書", extra=["--variant", "us_chronological"], title="explicit")
    ctx.expect(r.exit == 0 and r.json["form"]["variant"] == "us_chronological", "an explicit variant must win")


@case("FORM-04", "R1")
def form_04(ctx):
    reject(ctx, save_md(ctx, "# x\n\ntext", doc_type="foo"), "invalid_form", "doc_type_unknown")
    reject(ctx, recall(ctx, DOCS, doc_type="foo"), "invalid_form", "doc_type_unknown")
    ctx.expect(ctx.cli().json(["list"]).json["results"] == [], "a rejected save must store nothing")


@case("FORM-05", "R1")
def form_05(ctx):
    for value, expected in [("ko_KR", "ko-KR"), ("KO-kr", "ko-KR"), ("ko-kr", "ko-KR"), ("ko", "ko")]:
        r, form = form_of(ctx, locale=value)
        ctx.expect(r.exit == 0 and form.get("locale") == expected, f"locale {value} -> {expected}")


@case("FORM-06", "R1")
def form_06(ctx):
    for value in ("xx-YY", "ko-US", "en-AU"):
        reject(ctx, recall(ctx, DOCS, locale=value), "invalid_form", "locale_unknown")


@case("FORM-07", "R1")
def form_07(ctx):
    derived = ctx.cli().json(["save", "--kind", "template", "--title", "r-derived", "--doc-type", "resume", "--locale", "en-US", "--provider", "markdown",
                              "--stdin", "--format", "markdown"], stdin="# h\n\ntext")
    ctx.expect(derived.exit == 0 and derived.json["form"]["region"] == "US", "region must derive from the locale when it is not given")
    with ctx.mcp() as m:
        override = m.call("doc_memory_save", {"kind": "template", "title": "kr-region", "form": {"doc_type": "resume", "locale": "en-US", "region": "KR", "provider": "markdown"},
                                               "content": {"format": "markdown", "data": "# h\n\ntext body"}})
        ctx.expect(override is not None and not override.is_error and override.structured["form"]["region"] == "KR", "an explicit region must override the locale's")
        bad = m.call("doc_memory_save", {"kind": "template", "title": "zz", "form": {"doc_type": "resume", "locale": "en-US", "region": "ZZ", "provider": "markdown"},
                                          "content": {"format": "markdown", "data": "# h\n\ntext body"}})
        ctx.expect(bad is not None and bad.is_error and bad.code == "invalid_form", "an unknown region must be rejected")


@case("FORM-08", "R1")
def form_08(ctx):
    def save(page, provider="docx"):
        with ctx.mcp() as m:
            return m.call("doc_memory_save", {"kind": "template", "title": "p", "form": {"doc_type": "resume" if provider == "docx" else "pitch_deck", "locale": "ko-KR", "provider": provider, "page": page},
                                               "content": {"format": "markdown", "data": "# h\n\nbody text"}})
    ok = save({"size": "A4", "orientation": "portrait", "margins_mm": [25, 20, 25, 20]})
    ctx.expect(ok is not None and not ok.is_error and ok.structured["form"]["page"]["size"] == "A4", "a valid page must be stored")
    for bad in ({"size": "B5", "orientation": "portrait"}, {"size": "A4", "orientation": "diagonal"}, {"size": "A4", "orientation": "portrait", "margins_mm": [0, 0, 101, 0]}):
        r = save(bad)
        ctx.expect(r is not None and r.is_error and r.code in ("invalid_form", "invalid_input"), f"invalid page accepted: {bad}")
    r = save({"size": "A4", "orientation": "landscape"}, provider="pptx")
    ctx.expect(r is not None and r.is_error, "a document page size on a deck provider must be rejected")
    r = save({"size": "16:9", "orientation": "landscape"}, provider="docx")
    ctx.expect(r is not None and r.is_error, "a slide aspect on a document provider must be rejected")


@case("FORM-09", "R1")
def form_09(ctx):
    ok = save_md(ctx, "# h\n\nbody", extra=["--variant", "us_chronological"], title="v-ok")
    ctx.expect(ok.exit == 0 and ok.json["form"]["variant"] == "us_chronological", "valid variant")
    for value in ("Has Space", "UPPER", "x" * 33, ""):
        r = save_md(ctx, "# h\n\nbody", extra=["--variant", value], title="v-bad")
        ctx.expect(r.exit == 2 and r.code in ("invalid_form", "invalid_input"), f"bad variant accepted: {value!r}")


@case("FORM-10", "R1")
def form_10(ctx):
    for provider, family in [("google_slides", "deck"), ("pptx", "deck"), ("google_sheets", "sheet"), ("xlsx", "sheet"), ("docx", "document"), ("other", "document")]:
        with ctx.mcp() as m:
            r = m.call("doc_memory_save", {"kind": "template", "title": f"f-{provider}", "form": {"doc_type": "other", "locale": "ko-KR", "provider": provider},
                                            "content": {"format": "markdown", "data": "# h\n\nbody text"}})
        ctx.expect(r is not None and not r.is_error and r.structured["form"]["family"] == family, f"{provider} family must be {family}")
    for doc, provider in [("pitch_deck", "google_docs"), ("resume", "google_slides")]:
        r = save_md(ctx, "# h\n\nbody", doc_type=doc, provider=provider, title="mismatch")
        reject(ctx, r, "invalid_form", "family_mismatch")


PATTERN = ["--url-pattern", DOCS]
LETTER = {"size": "Letter", "orientation": "portrait"}


def save_form(ctx, title, locale, doc_type="resume", page=None, variant=None, identity="local"):
    """Save through MCP (the only surface that takes a page object) on the shared Docs pattern."""
    form = {"doc_type": doc_type, "locale": locale, "provider": "google_docs"}
    if page:
        form["page"] = page
    if variant:
        form["variant"] = variant
    with ctx.mcp(identity) as m:
        r = m.call("doc_memory_save", {"kind": "template", "title": title, "form": form, "url_patterns": [DOCS],
                                       "content": {"format": "markdown", "data": f"# {title}\n\nbody text for {title}"}})
    ctx.expect(r is not None and not r.is_error, f"save {title} failed: {None if r is None else r.structured}")
    return r


def hints_by_title(r):
    return {h["title"]: h for h in (r.json or {}).get("hints", [])}


@case("FORM-11", "R1")
def form_11(ctx):
    save_form(ctx, "kr", "ko-KR")
    save_form(ctx, "us", "en-US", page=LETTER)
    expected = {"ko-KR": ("exact", "none"), "ko": ("language", "none"), "en-GB": ("none", "language"), "ja-JP": ("none", "none"), None: ("unspecified", "unspecified")}
    for locale, (kr, us) in expected.items():
        fields = {"doc_type": "resume", "limit": 3}
        if locale:
            fields["locale"] = locale
        got = {title: h["locale_match"] for title, h in hints_by_title(recall(ctx, DOCS, **fields)).items()}
        ctx.expect(got == {"kr": kr, "us": us}, f"locale_match for query {locale}: expected kr={kr} us={us}, got {got}")


@case("FORM-12", "R1")
def form_12(ctx):
    save_form(ctx, "us-letter", "en-US", page=LETTER)
    r = recall(ctx, DOCS, doc_type="resume", locale="ko-KR")
    hint = hints_by_title(r).get("us-letter")
    ctx.expect(hint is not None, "the en-US Letter template must be returned for a ko-KR query")
    warnings = (hint or {}).get("warnings", [])
    codes = {w.get("code") for w in warnings}
    ctx.expect({"paper_mismatch", "date_order_mismatch", "currency_mismatch", "name_order_mismatch"} <= codes, f"a US Letter template for ko-KR must warn about all four conventions: {sorted(map(str, codes))}")
    ctx.expect(all(w.get("code") for w in warnings), "every warning needs a code")
    expanded = ctx.cli().json(["expand", hint["memory_id"], "--level", "1"]) if hint else None
    ctx.expect(expanded is not None and expanded.exit == 0 and expanded.json["form"]["locale"] == "en-US", "expand must return the stored form")


@case("FORM-13", "R1")
def form_13(ctx):
    save_form(ctx, "kr", "ko-KR")
    save_form(ctx, "us-letter", "en-US", page=LETTER)
    kr = hints_by_title(recall(ctx, DOCS, doc_type="resume", locale="ko-KR")).get("kr")
    ctx.expect(kr is not None and kr["warnings"] == [], f"a ko-KR memory for a ko-KR query must carry no convention warnings: {None if kr is None else kr['warnings']}")
    us = hints_by_title(recall(ctx, DOCS, doc_type="resume", locale="en-GB")).get("us-letter")
    codes = {w["code"] for w in (us or {}).get("warnings", [])}
    ctx.expect(us is not None and codes == {"paper_mismatch", "date_order_mismatch", "currency_mismatch"}, f"an en-US memory for an en-GB query must warn paper/date/currency only, got {sorted(codes)}")


@case("FORM-14", "F", needs=("hooks",))
def form_14(ctx):
    status = ctx.cli().json(["status"]).json
    versions = status.get("vocab") or {}
    ctx.expect(set(versions) == {"doc_types", "regions", "licenses", "keywords"} and all(isinstance(v, str) and v for v in versions.values()), f"status must report vocabulary versions: {versions}")
    legacy = save_form(ctx, "legacy", "ko-KR", doc_type="memo").structured
    save_form(ctx, "fresh", "ko-KR", doc_type="memo", variant="v2")  # same scope_key would upsert, so the variant differs
    ctx.cli().json(["__test", "patch", legacy["memory_id"], json.dumps({"l0_form": {"doc_type": "legacy_x"}})])  # data written under another vocabulary version
    ordered = recall(ctx, DOCS, locale="ko-KR")  # no doc_type filter: both are candidates
    titles = [h["title"] for h in ordered.json["hints"]]
    ctx.expect(titles == ["fresh", "legacy"], f"data with an unknown doc_type is preserved and ranked after the fresh item: {titles}")
    ctx.expect(ordered.json["hints"][-1]["freshness"] == "needs_reverify" and ordered.json["hints"][-1]["form"]["doc_type"] == "legacy_x", "the legacy record must be labelled needs_reverify and keep its stored value")
    ctx.expect(ctx.cli().json(["expand", legacy["memory_id"], "--level", "1"]).exit == 0, "the preserved record must stay expandable")
    ctx.expect(recall(ctx, DOCS, doc_type="memo", locale="ko-KR").json["hints"][0]["title"] == "fresh", "a strict doc_type filter excludes the legacy value")


@case("FORM-15", "R1")
def form_15(ctx):
    r = save_md(ctx, "# h\n\nbody", doc_type="pitch_deck", provider="pptx", title="ok-deck")
    ctx.expect(r.exit == 0, "pptx + pitch_deck is compatible")
    for doc, provider in [("pitch_deck", "google_docs"), ("pitch_deck", "other"), ("resume", "google_slides")]:
        reject(ctx, save_md(ctx, "# h\n\nbody", doc_type=doc, provider=provider, title="bad"), "invalid_form", "family_mismatch")


@case("FORM-16", "R1")
def form_16(ctx):
    save_form(ctx, "kr-resume", "ko-KR")
    save_form(ctx, "us-resume", "en-US", page=LETTER)
    save_form(ctx, "jp-resume", "ja-JP", variant="jp_rirekisho")
    listed = ctx.cli().json(["list", "--doc-type", "resume"]).json["results"]
    ctx.expect(len({m["memory_id"] for m in listed}) == 3, "KR/US/JP resumes must coexist as three separate memories")
    for locale, first in [("ko-KR", "kr-resume"), ("ja-JP", "jp-resume"), ("en-US", "us-resume")]:
        hints = recall(ctx, DOCS, doc_type="resume", locale=locale).json["hints"]
        ctx.expect(len(hints) == 3 and hints[0]["title"] == first, f"{locale}: first hint must be {first}, got {[h['title'] for h in hints]}")
