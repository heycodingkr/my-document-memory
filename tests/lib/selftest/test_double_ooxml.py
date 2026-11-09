"""Focused OOXML/PDF contract tests for the standard-library test double."""
import os
from io import BytesIO
from pathlib import Path
import resource
import signal
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "env" / "dmem-double"))

from dmtest import builders
from dmem_double.errors import DmemError
from dmem_double.ooxml import (
    detect_format, extract_docx, extract_pdf, extract_pptx, extract_xlsx_meta,
    export_docx, export_pptx,
)


class OOXMLTests(unittest.TestCase):
    def test_fmt04_docx_round_trip_and_page(self):
        for size in ("A4", "Letter"):
            source = {"schema": "stddoc/1", "type": "document", "slots": [], "rules": [],
                      "page": {"size": size, "orientation": "portrait", "margins_mm": [25, 20, 25, 20]},
                      "blocks": [{"type": "heading", "level": 1, "text": "Start"},
                                 {"type": "paragraph", "text": "First"},
                                 {"type": "heading", "level": 3, "text": "Details"},
                                 {"type": "table", "header": ["A", "B"], "rows": [["1", "2"]]},
                                 {"type": "paragraph", "text": "End"}]}
            data = export_docx(source)
            self.assertIn(b"[Content_Types].xml", data)
            got, _ = extract_docx(data)
            self.assertEqual([(b["type"], b.get("text")) for b in got["blocks"] if b["type"] != "table"],
                             [("heading", "Start"), ("paragraph", "First"), ("heading", "Details"), ("paragraph", "End")])
            self.assertEqual(got["blocks"][3], {"type": "table", "header": ["A", "B"], "rows": [["1", "2"]]})
            self.assertEqual(got["page"]["size"], size)

    def test_fmt05_template_order_and_table(self):
        doc, warnings = extract_docx(builders.tpl01())
        headings = [b["text"] for b in doc["blocks"] if b["type"] == "heading"]
        self.assertEqual(headings[-4:], ["요약", "지표", "위험", "요청"])
        tables = [b for b in doc["blocks"] if b["type"] == "table"]
        self.assertEqual(tables, [{"type": "table", "header": ["항목", "목표", "실적"], "rows": [["매출", "100", "92"], ["활성 사용자", "500", "476"]]}])
        self.assertIn("heading1", doc["styles"])
        self.assertIn("body", doc["styles"])

    def test_fmt06_unsafe_parts_and_relationships(self):
        for kind in ("macro", "ole"):
            with self.assertRaises(DmemError) as cm: extract_docx(builders.evil_docx(kind))
            self.assertEqual(cm.exception.code, "unsupported_format")
        external, warnings = extract_docx(builders.evil_docx("external"))
        self.assertIn("external_reference_removed", warnings)
        self.assertNotIn(b"fixture.invalid", repr(external).encode())
        self.assertNotIn(b"fixture.invalid", repr(warnings).encode())
        # The current builder serializes document.xml before it inserts its DDE field.
        # Add the field to that deterministic base package so this test exercises real XML.
        base = zipfile.ZipFile(BytesIO(builders.evil_docx("dde")))
        parts = {n: base.read(n) for n in base.namelist()}; base.close()
        parts["word/document.xml"] = parts["word/document.xml"].replace(
            b"</w:body>", b'<w:p><w:r><w:instrText>DDEAUTO fixture</w:instrText></w:r></w:p></w:body>')
        out = BytesIO()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for name, value in parts.items(): z.writestr(name, value)
        dde, warnings = extract_docx(out.getvalue())
        self.assertIn("fields_flattened", warnings)
        self.assertNotIn("DDEAUTO", repr(dde))

    def test_fmt07_zip_bomb_rejected_before_inflation(self):
        data = builders.zipbomb_docx()
        before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        old_handler = signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("zip check exceeded 5s")))
        signal.alarm(5)
        try:
            with self.assertRaises(DmemError) as cm: extract_docx(data)
            self.assertEqual(cm.exception.code, "payload_too_large")
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
        after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        scale = 1 if sys.platform == "darwin" else 1024
        self.assertLessEqual(max(0, after-before), 8 * 1024 * 1024 // scale)

    def test_fmt08_deck_order_theme_and_roles(self):
        deck, _ = extract_pptx(builders.deck5())
        self.assertEqual(len(deck["slides"]), 5)
        self.assertEqual(deck["theme"]["aspect"], "16:9")
        self.assertEqual([s["role"] for s in deck["slides"]], ["cover", "problem", "solution", "market", "ask"])
        self.assertEqual([s["title"] for s in deck["slides"]], ["표지", "문제", "해결", "시장", "요청"])

    def test_fmt11_pdf_page_locators_and_scanned_error(self):
        doc, _ = extract_pdf(builders.pdf(["one", "two"]))
        self.assertEqual([s["locator"] for s in doc["spans"]], ["page:1", "page:2"])
        self.assertEqual([b["text"] for b in doc["blocks"]], ["one", "two"])
        with self.assertRaises(DmemError) as cm: extract_pdf(builders.pdf("scan", scanned=True))
        self.assertEqual((cm.exception.code, cm.exception.reason), ("extract_empty", "ocr_required"))

    def test_fmt13_loss_warnings(self):
        _, dw = extract_docx(builders.rich_lossy_docx())
        _, pw = extract_pptx(builders.rich_lossy_pptx())
        for warnings in (dw, pw):
            self.assertIn("images_omitted", warnings)
            self.assertIn("comments_dropped", warnings)

    def test_tpl08_pptx_export_round_trip(self):
        source, _ = extract_pptx(builders.deck5())
        data = export_pptx(source)
        self.assertIn(b"[Content_Types].xml", data)
        got, _ = extract_pptx(data)
        self.assertEqual(len(got["slides"]), 5)
        self.assertEqual([s["title"] for s in got["slides"]], [s["title"] for s in source["slides"]])
        self.assertEqual([got["slides"][i]["role"] for i in (0, 1, 4)], ["cover", "problem", "ask"])

    def test_xlsx_headers_and_format_detection(self):
        self.assertEqual(detect_format("data.pdf", b"%PDF-1.4"), "pdf")
        self.assertEqual(detect_format("notes.md", b"# Hi"), "markdown")
        self.assertIsNone(detect_format("data.exe", b"\x00\xff\x00"))
        out = BytesIO()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Data" sheetId="1" r:id="rId1"/></sheets></workbook>')
            z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
            z.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>One</t></is></c><c r="B1" t="inlineStr"><is><t>Two</t></is></c></row></sheetData></worksheet>')
        sheet, warnings = extract_xlsx_meta(out.getvalue())
        self.assertEqual(warnings, ["sheet_support_deferred"])
        self.assertEqual([c["header"] for c in sheet["sheets"][0]["columns"]], ["One", "Two"])


if __name__ == "__main__":
    unittest.main()
