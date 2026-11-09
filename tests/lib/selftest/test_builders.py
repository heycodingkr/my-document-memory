"""HARN-01 / HARN-09: the file builders are deterministic and build what fixtures.md section 5 says they build."""
import hashlib
import io
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dmtest import builders


def names(blob):
    return set(zipfile.ZipFile(io.BytesIO(blob)).namelist())


class BuilderTests(unittest.TestCase):
    def test_same_input_same_bytes(self):
        for fn in (builders.tpl01, builders.deck5, builders.resume_ko_md, builders.invoice_kr_md, builders.rich_lossy_docx, builders.rich_lossy_pptx):
            self.assertEqual(hashlib.sha256(fn()).hexdigest(), hashlib.sha256(fn()).hexdigest(), fn.__name__)
        blocks = [{"type": "heading", "level": 1, "text": "제목"}, {"type": "paragraph", "text": "본문"}]
        self.assertEqual(builders.docx(blocks), builders.docx(blocks))
        self.assertNotEqual(builders.docx(blocks), builders.docx(blocks + [{"type": "paragraph", "text": "더"}]))

    def test_docx_and_pptx_are_valid_packages_with_their_main_parts(self):
        self.assertIn("word/document.xml", names(builders.tpl01()))
        deck = names(builders.deck5())
        self.assertEqual(len([n for n in deck if n.startswith("ppt/slides/slide") and n.endswith(".xml")]), 5)
        self.assertIsNone(zipfile.ZipFile(io.BytesIO(builders.tpl01())).testzip())

    def test_hostile_documents_carry_their_characteristic_parts(self):
        self.assertIn("word/vbaProject.bin", names(builders.evil_docx("macro")))
        self.assertTrue(any(n.startswith("word/embeddings/") for n in names(builders.evil_docx("ole"))))
        external = zipfile.ZipFile(io.BytesIO(builders.evil_docx("external")))
        self.assertTrue(any(b"TargetMode=\"External\"" in external.read(n) or b"TargetMode='External'" in external.read(n) for n in external.namelist() if n.endswith(".rels")))
        self.assertIn(b"DDEAUTO", zipfile.ZipFile(io.BytesIO(builders.evil_docx("dde"))).read("word/document.xml"))
        with self.assertRaises(ValueError):
            builders.evil_docx("nonsense")

    def test_zip_bomb_ratio_is_what_the_fixture_promises(self):
        blob = builders.zipbomb_docx()
        info = zipfile.ZipFile(io.BytesIO(blob)).getinfo("word/document.xml")
        self.assertGreaterEqual(info.file_size, 100 * 1024 * 1024)
        self.assertGreaterEqual(info.file_size / max(1, info.compress_size), 1000)
        self.assertLess(len(blob), 1024 * 1024, "the archive itself must stay small")

    def test_pdfs_with_and_without_a_text_layer(self):
        self.assertTrue(builders.pdf(["Hello fixture"]).startswith(b"%PDF-"))
        self.assertIn(b"Hello fixture", builders.pdf(["Hello fixture"]))
        scanned = builders.pdf(["Hello fixture"], scanned=True)
        self.assertNotIn(b"Hello fixture", scanned, "a scanned PDF has no text layer")

    def test_text_fixtures_have_the_expected_placeholders(self):
        self.assertIn("{{name}}".encode(), builders.resume_ko_md())
        self.assertIn("{{공급자명}}".encode(), builders.invoice_kr_md())


if __name__ == "__main__":
    unittest.main()
