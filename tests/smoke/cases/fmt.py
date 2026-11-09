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
                                   "--locale", locale, "--provider", "docx", "--file", str(path)])
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
