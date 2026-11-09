"""FMT-01..FMT-14: StandardDoc adapters and export (docs/spec/formats.md)."""
import json
import stat
import zipfile
from html.parser import HTMLParser
from xml.etree import ElementTree as ET

from dmtest import builders
from dmtest.runner import case


def _write(ctx, name, data):
    path = ctx.home().parent / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
    return path


def _save_doc(ctx, title, doc, *, provider="other", locale="ko-KR", variant=None, doc_type="report", file=None):
    args = ["save", "--kind", "template", "--title", title, "--doc-type", doc_type,
            "--locale", locale, "--provider", provider]
    if variant:
        args += ["--variant", variant]
    if file is not None:
        args += ["--file", str(file)]
        return ctx.cli().json(args)
    args += ["--stdin", "--format", "stddoc"]
    return ctx.cli().json(args, stdin=json.dumps(doc, ensure_ascii=False))


def _save_markdown(ctx, title, markdown, *, provider="markdown", locale="ko-KR", variant=None, doc_type="report"):
    args = ["save", "--kind", "template", "--title", title, "--doc-type", doc_type,
            "--locale", locale, "--provider", provider]
    if variant:
        args += ["--variant", variant]
    args += ["--stdin", "--format", "markdown"]
    return ctx.cli().json(args, stdin=markdown)


def _expand(ctx, memory_id):
    r = ctx.cli().json(["expand", memory_id or "missing", "--level", "2"])
    return r, (((r.json or {}).get("l2") or {}).get("structure") or {})


def _blocks():
    return [
        {"type": "heading", "level": 1, "text": "Release"},
        {"type": "heading", "level": 2, "text": "Checks"},
        {"type": "list", "ordered": True, "items": ["Alpha", "  Nested"]},
        {"type": "table", "header": ["Item", "Status"], "rows": [["API", "Ready"], ["CLI", "Ready"]]},
        {"type": "callout", "tone": "note", "text": "Check output"},
        {"type": "callout", "tone": "warning", "text": "Review changes"},
    ]


def _doc(blocks=None, page=None, styles=None):
    return {"schema": "stddoc/1", "type": "document", "page": page, "styles": styles or {},
            "blocks": list(_blocks() if blocks is None else blocks), "slots": [], "rules": []}


def _export(ctx, memory_id, fmt, path):
    return ctx.cli().json(["export", memory_id or "missing", "--format", fmt, "--out", str(path)])


@case("FMT-01", "R1")
def fmt_01(ctx):
    saved = _save_doc(ctx, "fmt-markdown", _doc())
    memory_id = (saved.json or {}).get("memory_id")
    path = ctx.home().parent / "fmt-01.md"
    exported = _export(ctx, memory_id, "md", path)
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    expected = ["# Release", "## Checks", "1. Alpha", "  1. Nested", "| Item | Status |", "| --- | --- |",
                "> [!NOTE]", "> [!WARNING]"]
    ctx.expect(saved.exit == 0 and memory_id is not None and exported.exit == 0, "StandardDoc must save and export as Markdown")
    ctx.expect(all(mark in text for mark in expected), "Markdown must use heading, nested list, GFM table, and callout rules")
    positions = [text.find(mark) for mark in ("# Release", "## Checks", "1. Alpha", "| Item | Status |", "> [!NOTE]", "> [!WARNING]")]
    ctx.expect(all(p >= 0 for p in positions) and positions == sorted(positions), "exported blocks must keep their input order")


@case("FMT-02", "R1")
def fmt_02(ctx):
    saved = _save_doc(ctx, "fmt-roundtrip-source", _doc())
    memory_id = (saved.json or {}).get("memory_id")
    path = ctx.home().parent / "fmt-02.md"
    exported = _export(ctx, memory_id, "md", path)
    markdown = path.read_text(encoding="utf-8") if path.is_file() else ""
    imported = ctx.cli().json(["save", "--kind", "template", "--title", "fmt-roundtrip-import", "--doc-type", "report",
                               "--locale", "ko-KR", "--provider", "markdown", "--stdin", "--format", "markdown"], stdin=markdown)
    imported_id = (imported.json or {}).get("memory_id")
    expanded, structure = _expand(ctx, imported_id)
    kinds = [b.get("type") for b in structure.get("blocks", [])]
    expected = [b["type"] for b in _blocks()]
    ctx.expect(saved.exit == 0 and exported.exit == 0 and imported.exit == 0 and expanded.exit == 0,
               "Markdown export must be accepted by save --stdin --format markdown")
    ctx.expect(imported_id is not None and kinds == expected, f"Markdown round-trip block kinds/order: {kinds}")


@case("FMT-03", "R1")
def fmt_03(ctx):
    payload = '<script>alert(1)</script> "><img src=x onerror=alert(1)> [x](javascript:alert(1)) & <'
    saved = _save_markdown(ctx, "fmt-html-safety", payload)
    memory_id = (saved.json or {}).get("memory_id")
    path = ctx.home().parent / "fmt-03.html"
    exported = _export(ctx, memory_id, "html", path)
    html = path.read_text(encoding="utf-8") if path.is_file() else ""

    class Tags(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.names, self.text = [], []

        def handle_starttag(self, tag, attrs):
            self.names.append(tag)

        def handle_startendtag(self, tag, attrs):
            self.names.append(tag)

        def handle_data(self, data):
            self.text.append(data)

    parsed = Tags()
    parsed.feed(html)
    allowed = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "li", "table", "thead", "tbody",
               "tr", "th", "td", "blockquote", "aside", "img", "a", "strong", "em", "code", "br"}
    ctx.expect(saved.exit == 0 and memory_id is not None and exported.exit == 0, "unsafe text must still export as HTML")
    ctx.expect("<script" not in html.lower() and "onerror=" not in html.lower() and "javascript:" not in html.lower(),
               "HTML must not contain executable markup, event handlers, or javascript URLs")
    visible_text = "".join(parsed.text)
    preserved = ("<script>alert(1)</script>" in visible_text and '<img src=x onerror=alert(1)>' in visible_text
                 and " x" in visible_text and "& <" in visible_text)
    ctx.expect(set(parsed.names) <= allowed and preserved, "HTML tags must be allowlisted and displayed text must remain escaped as text")


@case("FMT-04", "R1")
def fmt_04(ctx):
    cases = [("A4", "ko-KR"), ("Letter", "en-US")]
    for size, locale in cases:
        page = {"size": size, "orientation": "portrait", "margins_mm": [25, 20, 25, 20]}
        doc = _doc([{"type": "heading", "level": 1, "text": f"{size} report"},
                    {"type": "table", "header": ["Field", "Value"], "rows": [["Paper", size]]}], page=page)
        saved = _save_doc(ctx, f"fmt-docx-{size.lower()}", doc, provider="docx", locale=locale)
        memory_id = (saved.json or {}).get("memory_id")
        path = ctx.home().parent / f"fmt-04-{size.lower()}.docx"
        exported = _export(ctx, memory_id, "docx", path)
        valid_zip, has_types, external_count = False, False, -1
        if path.is_file():
            try:
                with zipfile.ZipFile(path) as archive:
                    names = archive.namelist()
                    has_types = "[Content_Types].xml" in names
                    rels = [n for n in names if n.endswith(".rels")]
                    external_count = 0
                    for name in rels:
                        root = ET.fromstring(archive.read(name))
                        external_count += sum(1 for node in root.iter() if node.attrib.get("TargetMode") == "External")
                    valid_zip = has_types and "word/document.xml" in names and all(archive.read(n) for n in names if n.endswith(".xml"))
            except (OSError, zipfile.BadZipFile, ET.ParseError):
                valid_zip = False
        imported = ctx.cli().json(["save", "--kind", "template", "--title", f"fmt-docx-import-{size.lower()}", "--doc-type", "report",
                                   "--locale", locale, "--provider", "docx", "--variant", "roundtrip", "--file", str(path)])  # an independent form: the same scope would be a scope_conflict
        imported_id = (imported.json or {}).get("memory_id")
        expanded, structure = _expand(ctx, imported_id)
        blocks = structure.get("blocks", [])
        headings = [b.get("text") for b in blocks if b.get("type") == "heading"]
        tables = [b for b in blocks if b.get("type") == "table"]
        cells = (tables[0].get("header", []) + [v for row in tables[0].get("rows", []) for v in row]) if tables else []
        ctx.expect(saved.exit == 0 and exported.exit == 0 and imported.exit == 0 and expanded.exit == 0,
                   f"{size} DOCX must export and import")
        ctx.expect(valid_zip and external_count == 0, f"{size} DOCX must be a valid OOXML ZIP without external relationships")
        ctx.expect(headings == [f"{size} report"] and len(tables) == 1 and cells == ["Field", "Value", "Paper", size] and structure.get("page", {}).get("size") == size,
                   f"{size} DOCX round-trip must preserve heading, table cells, order, and page size")


@case("FMT-05", "R1")
def fmt_05(ctx):
    source = _write(ctx, "tpl01-monthly-report.docx", builders.tpl01())
    saved = _save_doc(ctx, "tpl01-monthly-report", {}, provider="docx", file=source)
    memory_id = (saved.json or {}).get("memory_id")
    expanded, structure = _expand(ctx, memory_id)
    blocks = structure.get("blocks", [])
    headings = [b.get("text") for b in blocks if b.get("type") == "heading"]
    tables = [b for b in blocks if b.get("type") == "table"]
    styles = structure.get("styles") or {}
    ctx.expect(saved.exit == 0 and memory_id is not None and expanded.exit == 0, "tpl01-monthly-report.docx must save and expand")
    sections = [heading for heading in headings if heading != "월간 운영 보고서"]
    ctx.expect(sections == ["요약", "지표", "위험", "요청"] and headings[:1] == ["월간 운영 보고서"],
               f"DOCX title must remain separate from section order: {headings}")
    ctx.expect(len(tables) == 1 and tables[0].get("header") == ["항목", "목표", "실적"] and len(tables[0].get("rows", [])) == 2,
               "DOCX table headers and both rows must be preserved")
    ctx.expect(any(k.lower() in ("title", "heading1") for k in styles) and any(k.lower() in ("normal", "body") for k in styles),
               f"DOCX title and body styles must appear in StandardDoc styles: {sorted(styles)}")

@case("FMT-06", "F", needs=("fixtures",))
def fmt_06(ctx):
    for kind in ("macro", "ole"):
        source = _write(ctx, f"fmt-06-{kind}.docx", builders.evil_docx(kind))
        saved = _save_doc(ctx, f"fmt-06-{kind}", {}, provider="docx", variant=f"fmt06_{kind}", file=source)
        ctx.expect(saved.exit == 2 and saved.code == "unsupported_format",
                   f"{kind} OOXML must be rejected as unsupported_format: exit={saved.exit} code={saved.code}")

    external = _write(ctx, "fmt-06-external.docx",
                      builders.evil_docx("external", url=f"{ctx.fx_url}/pages/resume-ko.html"))
    before = len(ctx.fx_log())
    saved_external = _save_doc(ctx, "fmt-06-external", {}, provider="docx", variant="fmt06_external", file=external)
    external_id = (saved_external.json or {}).get("memory_id")
    external_warnings = {w.get("code") if isinstance(w, dict) else w
                         for w in (saved_external.json or {}).get("warnings", [])}
    ctx.expect(saved_external.exit == 0 and external_id is not None,
               f"an external relationship DOCX is saved: {(saved_external.json or {}).get('error')}")
    ctx.expect("external_reference_removed" in external_warnings,
               f"external references are removed with a warning: {sorted(external_warnings)}")
    ctx.expect(len(ctx.fx_log()) == before,
               "reading an external relationship must not fetch its target")

    dde = _write(ctx, "fmt-06-dde.docx", builders.evil_docx("dde"))
    saved_dde = _save_doc(ctx, "fmt-06-dde", {}, provider="docx", variant="fmt06_dde", file=dde)
    dde_id = (saved_dde.json or {}).get("memory_id")
    dde_warnings = {w.get("code") if isinstance(w, dict) else w
                    for w in (saved_dde.json or {}).get("warnings", [])}
    expanded_dde, _ = _expand(ctx, dde_id)
    ctx.expect(saved_dde.exit == 0 and dde_id is not None and expanded_dde.exit == 0,
               f"a DDE DOCX is saved and can be expanded: exit={saved_dde.exit}/{expanded_dde.exit}")
    ctx.expect("fields_flattened" in dde_warnings and "DDEAUTO" not in expanded_dde.stdout,
               f"DDE instructions are removed and fields_flattened is reported: {sorted(dde_warnings)}")
    ctx.expect(len(ctx.fx_log()) == before,
               "processing OOXML relationships and fields makes no fixture request")

@case("FMT-09", "F", needs=("fixtures",))
def fmt_09(ctx):
    url = f"{ctx.fx_url}/p/google-slides/presentation/d/FIX_DECK/edit"
    imported = ctx.cli().json(["import", url, "--as", "template"])
    memory_id = (imported.json or {}).get("memory_id")
    warnings = {w.get("code") if isinstance(w, dict) else w
                for w in (imported.json or {}).get("warnings", [])}
    expanded, structure = _expand(ctx, memory_id)
    formats = [entry.get("format") for entry in ctx.fx_log()
               if "/google-slides/" in entry.get("path", "") and "/export" in entry.get("path", "")]
    ctx.expect(imported.exit == 0 and memory_id is not None and expanded.exit == 0,
               f"the Slides-shaped URL imports and expands: exit={imported.exit}/{expanded.exit}")
    ctx.expect(structure.get("type") == "deck" and "layout_inferred" in warnings,
               f"the result is a deck with inferred layout: type={structure.get('type')} warnings={sorted(warnings)}")
    ctx.expect(formats == ["pptx"] and not any(fmt in ("md", "html") for fmt in formats),
               f"Slides requests PPTX only, not Markdown or HTML: {formats}")


@case("FMT-10", "F", needs=("fixtures",))
def fmt_10(ctx):
    def sheet_import(path):
        r = ctx.cli().json(["import", ctx.fx_url + path, "--as", "template"])
        ctx.expect(r.exit == 0 and r.json.get("memory_id"), f"{path}: the Sheets-shaped URL is imported: exit={r.exit} {r.code}")
        if r.exit != 0:
            return {}, set(), ""
        expanded = ctx.cli().json(["expand", r.json["memory_id"], "--level", "2"])
        codes = {w["code"] if isinstance(w, dict) else w for w in r.json.get("warnings", [])}
        ctx.cli().json(["delete", r.json["memory_id"], "--yes"])  # both variants share one scope (docs.google.com/spreadsheets/d/:id/edit): free it for the next import
        return (expanded.json["l2"]["structure"] or {}), codes, expanded.stdout

    def export_formats(marker):
        return [e.get("format") for e in ctx.fx_log() if marker in e["path"] and "/export" in e["path"]]

    default, default_codes, default_text = sheet_import("/p/google-sheets/spreadsheets/d/FIX_SHEET/edit")
    ctx.expect(export_formats("/google-sheets/") == ["xlsx"], f"the default variant uses the workbook export only: {export_formats('/google-sheets/')}")
    ctx.expect(default.get("type") == "sheet" and [s["name"] for s in default.get("sheets", [])] == ["Quarters"], f"sheet names are kept: {default.get('sheets')}")
    ctx.expect([c["header"] for c in default.get("sheets", [{}])[0].get("columns", [])] == ["Quarter", "Value"], "column headers are kept")
    ctx.expect("sheet_support_deferred" in default_codes and "first_sheet_only" not in default_codes, f"the default variant says sheet support is deferred, not truncated: {sorted(default_codes)}")
    ctx.expect("Q1" not in default_text and "125" not in default_text, "only metadata is stored: no data rows")

    csv_only, csv_codes, csv_text = sheet_import("/p/google-sheets-csv/spreadsheets/d/FIX_SHEET/edit")
    ctx.expect(export_formats("/google-sheets-csv/") == ["xlsx", "csv"], f"the workbook is tried first, then CSV: {export_formats('/google-sheets-csv/')}")
    ctx.expect({"first_sheet_only", "sheet_support_deferred"} <= csv_codes, f"the CSV fallback warns that only the first sheet was read: {sorted(csv_codes)}")
    ctx.expect(csv_only.get("type") == "sheet" and [c["header"] for c in csv_only.get("sheets", [{}])[0].get("columns", [])] == ["Quarter", "Value"], "the CSV fallback keeps the header row")
    ctx.expect("Q1" not in csv_text and "125" not in csv_text, "the CSV fallback stores no data rows either")


@case("FMT-11", "F")
def fmt_11(ctx):
    text_pdf = _write(ctx, "text.pdf", builders.pdf("Quarterly figures on page one."))
    saved_text = ctx.cli().json(["save", "--kind", "reference", "--title", "text PDF reference",
                                 "--doc-type", "other", "--locale", "en-US", "--provider", "pdf",
                                 "--file", str(text_pdf)])
    memory_id = (saved_text.json or {}).get("memory_id")
    expanded = ctx.cli().json(["expand", memory_id or "missing", "--level", "2"])
    spans = ((expanded.json or {}).get("l2") or {}).get("spans", [])
    ctx.expect(saved_text.exit == 0 and memory_id is not None and expanded.exit == 0,
               f"text.pdf is saved as a reference: exit={saved_text.exit}/{expanded.exit}")
    ctx.expect(any(span.get("locator") == "page:1" for span in spans),
               f"text PDF spans identify page:1: {[span.get('locator') for span in spans]}")

    scan_pdf = _write(ctx, "scan.pdf", builders.pdf("", scanned=True))
    scanned = ctx.cli().json(["save", "--kind", "reference", "--title", "scanned PDF reference",
                              "--doc-type", "other", "--locale", "en-US", "--provider", "pdf",
                              "--file", str(scan_pdf)])
    error = (scanned.json or {}).get("error") or {}
    ctx.expect(scanned.exit == 2 and error.get("code") == "extract_empty"
               and error.get("reason") == "ocr_required",
               f"scanned PDF requires OCR: exit={scanned.exit} error={error}")


@case("FMT-12", "F", needs=("fixtures",))
def fmt_12(ctx):
    url = f"{ctx.fx_url}/p/notion/Quarterly-Report-0123456789abcdef0123456789abcdef"
    imported = ctx.cli().json(["import", url, "--as", "template"])
    memory_id = (imported.json or {}).get("memory_id")
    expanded, structure = _expand(ctx, memory_id)
    kinds = [block.get("type") for block in structure.get("blocks", [])]
    provider = ((imported.json or {}).get("form") or {}).get("provider")
    ctx.expect(imported.exit == 0 and memory_id is not None and expanded.exit == 0,
               f"the public Notion-shaped page imports and expands: exit={imported.exit}/{expanded.exit}")
    ctx.expect(provider == "notion",
               f"the imported provider is notion: {provider}")
    ctx.expect(kinds == ["heading", "list", "table", "callout"],
               f"headings, lists, tables and callouts map in order: {kinds}")


@case("FMT-13", "F")
def fmt_13(ctx):
    cases = [
        ("docx", builders.rich_lossy_docx(), "report"),
        ("pptx", builders.rich_lossy_pptx(), "pitch_deck"),
    ]
    expected = {"images_omitted", "comments_dropped", "unsupported_block"}
    for provider, data, doc_type in cases:
        source = _write(ctx, f"fmt-13-rich-lossy.{provider}", data)
        saved = _save_doc(ctx, f"fmt-13-rich-lossy-{provider}", {}, provider=provider,
                          locale="en-US" if provider == "pptx" else "ko-KR",
                          doc_type=doc_type, file=source)
        warnings = {w.get("code") if isinstance(w, dict) else w
                    for w in (saved.json or {}).get("warnings", [])}
        relevant = warnings & expected
        ctx.expect(saved.exit == 0 and (saved.json or {}).get("memory_id") is not None,
                   f"rich-lossy.{provider} imports: exit={saved.exit}")
        ctx.expect(expected <= warnings and len(relevant) >= 3,
                   f"each omitted image/comment/unsupported element is reported for {provider}: {sorted(warnings)}")


@case("FMT-14", "R1")
def fmt_14(ctx):
    image_doc = _doc([{"type": "heading", "level": 1, "text": "Export safety"},
                      {"type": "image", "alt": "Fixture image", "ref": "sha256:" + "a" * 64}])
    saved = _save_doc(ctx, "fmt-14-image-export", image_doc, variant="fmt14_assets")
    memory_id = (saved.json or {}).get("memory_id")
    ctx.expect(saved.exit == 0 and memory_id is not None, "the export fixture saves")

    relative = ctx.cli().json(["export", memory_id or "missing", "--format", "md", "--out", "fmt-14-relative.md"])
    existing = _write(ctx, "fmt-14-existing.md", "KEEP_EXISTING_FILE")
    existing_result = _export(ctx, memory_id, "md", existing)
    link_target = _write(ctx, "fmt-14-link-target.md", "KEEP_SYMLINK_TARGET")
    link_path = ctx.home().parent / "fmt-14-link.md"
    link_path.symlink_to(link_target)
    link_result = _export(ctx, memory_id, "md", link_path)
    missing_parent = ctx.home().parent / "fmt-14-missing-parent" / "export.md"
    missing_result = _export(ctx, memory_id, "md", missing_parent)

    normal = ctx.home().parent / "fmt-14-normal.md"
    normal_result = _export(ctx, memory_id, "md", normal)
    asset_dir = normal.with_name(normal.name + ".assets")
    ctx.expect(relative.exit == 2,
               f"relative output paths are rejected: exit={relative.exit} code={relative.code}")
    ctx.expect(existing_result.exit == 2 and existing.read_text(encoding="utf-8") == "KEEP_EXISTING_FILE",
               "an existing output file is rejected without changing its contents")
    ctx.expect(link_result.exit == 2 and link_path.is_symlink()
               and link_target.read_text(encoding="utf-8") == "KEEP_SYMLINK_TARGET",
               "a symlink output is rejected without following or changing its target")
    ctx.expect(missing_result.exit == 2 and not missing_parent.parent.exists(),
               "an output whose parent directory does not exist is rejected")
    ctx.expect(normal_result.exit == 0 and normal.is_file() and stat.S_IMODE(normal.stat().st_mode) == 0o600,
               f"a normal output is created with mode 0600: exit={normal_result.exit} mode={stat.S_IMODE(normal.stat().st_mode) if normal.exists() else None}")
    ctx.expect(not asset_dir.exists(), "v1 stores no image assets, so no asset directory may be created next to the export (formats.md section 5)")



@case("FMT-07", "F")
def fmt_07(ctx):
    import resource
    import sys

    source = _write(ctx, "fmt-07-zipbomb.docx", builders.zipbomb_docx())
    saved = _save_doc(ctx, "fmt-07-zipbomb", {}, provider="docx", file=source)
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    peak_mb = peak / (1024 * 1024) if sys.platform == "darwin" else peak / 1024
    listed = ctx.cli().json(["list"])
    results = (listed.json or {}).get("results", [])
    ctx.expect(saved.exit == 2 and saved.code == "payload_too_large",
               f"the oversized OOXML part is rejected: exit={saved.exit} code={saved.code}")
    ctx.expect(peak_mb <= 256, f"peak child RSS stays within 256 MiB: {peak_mb:.1f} MiB")
    ctx.expect(listed.exit == 0 and results == [],
               f"the rejected file leaves no partial memory: {results}")


@case("FMT-08", "R1")
def fmt_08(ctx):
    source = _write(ctx, "deck-5.pptx", builders.deck5())
    saved = _save_doc(ctx, "fmt-deck-5", {}, provider="pptx", locale="en-US",
                      doc_type="pitch_deck", file=source)
    memory_id = (saved.json or {}).get("memory_id")
    expanded, structure = _expand(ctx, memory_id)
    slides = structure.get("slides", [])
    expected_titles = ["표지", "문제", "해결", "시장", "요청"]
    expected_roles = ["cover", "problem", "solution", "market", "ask"]
    expected_bodies = [f"My Document Memory — {title}" for title in expected_titles]
    titles = [slide.get("title") for slide in slides]
    roles = [slide.get("role") for slide in slides]
    bodies = [[block.get("text") for block in slide.get("blocks", []) if block.get("type") == "paragraph"]
              for slide in slides]
    ctx.expect(saved.exit == 0 and memory_id is not None and expanded.exit == 0,
               f"deck-5.pptx must save and expand: exit={saved.exit}/{expanded.exit}")
    ctx.expect(structure.get("type") == "deck" and len(slides) == 5
               and [slide.get("index") for slide in slides] == [1, 2, 3, 4, 5],
               f"the StandardDoc is an ordered five-slide deck: type={structure.get('type')} slides={len(slides)}")
    ctx.expect((structure.get("theme") or {}).get("aspect") == "16:9",
               f"the deck aspect is 16:9: {(structure.get('theme') or {}).get('aspect')}")
    ctx.expect(roles == expected_roles,
               f"slide roles are inferred from titles: {roles}")
    ctx.expect(titles == expected_titles and bodies == [[body] for body in expected_bodies],
               f"slide title and body text are preserved in order: titles={titles} bodies={bodies}")
