"""CORE URL contract checks for the Python test double."""
import os
import re
import sys
import unittest
from pathlib import Path
from unittest import mock


DOUBLE_ROOT = Path(__file__).resolve().parents[2] / "env" / "dmem-double"
sys.path.insert(0, str(DOUBLE_ROOT))

from dmem_double.errors import DmemError
from dmem_double.urls import Canonical, canonicalize, is_canonical, is_capability_host, source_ref


class DoubleUrlTests(unittest.TestCase):
    def assert_url(self, url, pattern, provider="other", isolated=False):
        result = canonicalize(url, isolated=isolated)
        self.assertIsInstance(result, Canonical)
        self.assertEqual(result.pattern, pattern, url)
        self.assertEqual(result.provider, provider, url)
        return result

    def assert_rejected(self, url, reason, isolated=False):
        with self.assertRaises(DmemError, msg=url) as caught:
            canonicalize(url, isolated=isolated)
        self.assertEqual(caught.exception.code, "url_rejected")
        self.assertEqual(caught.exception.reason, reason)
        return caught.exception

    def test_core_01_spec_examples_and_canonical_idempotence(self):
        accepted = [
            ("https://docs.google.com/document/d/FIXTURE_DOC_ID_0123456789ABCDEFGHIJKLMNOPQ/edit?usp=sharing&resourcekey=0-x#heading=h.abc", "docs.google.com/document/d/:id/edit", "google_docs"),
            ("https://docs.google.com/document/u/1/d/FIXTURE_DOC_ID_0123456789ABCDEFGHIJKLMNOPQ/edit", "docs.google.com/document/d/:id/edit", "google_docs"),
            ("https://docs.google.com/presentation/d/FIXTURE_DECK_ID_0123456789ABCDEFGHIJKLMNO/edit#slide=id.p3", "docs.google.com/presentation/d/:id/edit", "google_slides"),
            ("https://docs.google.com/spreadsheets/d/FIXTURE_SHEET_ID_0123456789ABCDEFGHIJKLMN/edit?gid=0", "docs.google.com/spreadsheets/d/:id/edit", "google_sheets"),
            ("https://www.notion.so/myws/Quarterly-Report-0123456789abcdef0123456789abcdef?pvs=4", "www.notion.so/:id", "notion"),
            ("https://acme.notion.site/Invoice-Template-0123456789abcdef0123456789abcdef", "acme.notion.site/:id", "notion"),
            ("https://www.example.org/forms/invoice.docx?download=1", "www.example.org/forms/invoice.docx", "docx"),
            ("https://example.com/templates/resume/modern?utm_source=x#top", "example.com/templates/resume/modern", "other"),
            ("https://example.com/people/948203/profile", "example.com/people/:id/profile", "other"),
            ("https://example.com/blog/my-private-project-948203", "example.com/blog/:id", "other"),
        ]
        for url, pattern, provider in accepted:
            with self.subTest(url=url):
                self.assert_url(url, pattern, provider)
                self.assertTrue(is_canonical(pattern), pattern)
        rejected = [
            ("https://user:pw@example.com/", "userinfo_not_allowed"),
            ("http://example.com/", "scheme_not_allowed"),
            ("https://192.168.0.1/x", "host_not_allowed"),
            ("https://example.com/u/jane.doe@corp.test/doc", "pii_in_url"),
        ]
        for url, reason in rejected:
            with self.subTest(url=url):
                self.assert_rejected(url, reason)

    def test_core_02_only_https_is_allowed(self):
        urls = [
            "http://example.com/a", "ftp://example.com/", "file:///etc/passwd",
            "data:text/html,x", "javascript:alert(1)", "gopher://example.com/",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assert_rejected(url, "scheme_not_allowed")

    def test_core_03_userinfo_is_rejected_without_echo(self):
        urls = [
            "https://user:pw_SENTINEL@example.com/",
            "https://USERINFO_SENTINEL@example.com/x",
        ]
        for url in urls:
            with self.subTest(url=url):
                error = self.assert_rejected(url, "userinfo_not_allowed")
                self.assertNotIn("SENTINEL", str(error))
                self.assertNotIn("SENTINEL", repr(error.error_object()))

    def test_core_04_query_and_fragment_are_dropped(self):
        self.assert_url(
            "https://example.com/templates/resume/modern?utm_source=Q_SENTINEL#F_SENTINEL",
            "example.com/templates/resume/modern",
        )

    def test_core_05_default_port_only(self):
        self.assert_url("https://example.com:443/x", "example.com/x")
        self.assert_rejected("https://example.com:8443/x", "host_not_allowed")

    def test_core_06_host_and_path_normalization(self):
        rows = [
            ("https://EXAMPLE.com./Templates/A", "example.com/templates/a"),
            ("https://bücher.example/x", "xn--bcher-kva.example/x"),
        ]
        for url, pattern in rows:
            with self.subTest(url=url):
                self.assert_url(url, pattern)

    def test_core_07_unsafe_hosts_including_legacy_ip_forms(self):
        hosts = [
            "127.0.0.1", "10.0.0.5", "192.168.1.1", "169.254.169.254",
            "[::1]", "[fd00::1]", "2130706433", "0x7f.1", "0177.0.0.1",
            "localhost", "intranet", "metadata.google.internal",
        ]
        for host in hosts:
            url = f"https://{host}/x"
            with self.subTest(host=host):
                self.assert_rejected(url, "host_not_allowed")

    def test_core_08_isolated_loopback_aliases_and_fixture_host(self):
        google = "http://127.0.0.1:8123/p/google-docs/document/d/FIX_KO_RESUME/edit"
        result = self.assert_url(google, "docs.google.com/document/d/:id/edit", "google_docs", isolated=True)
        self.assertEqual(result.host, "docs.google.com")
        self.assertEqual(result.fetch_url, google)

        fixture = "http://127.0.0.1:8123/pages/a?x=1#heading"
        result = self.assert_url(fixture, "fixture.test/pages/a", "other", isolated=True)
        self.assertEqual(result.host, "fixture.test")
        self.assertEqual(result.fetch_url, "http://127.0.0.1:8123/pages/a")

        for url in (google, fixture):
            with self.subTest(url=url):
                self.assert_rejected(url, "scheme_not_allowed", isolated=False)

        notion = canonicalize("http://[::1]:9999/p/notion/ws/Title-0123456789abcdef0123456789abcdef", isolated=True)
        self.assertEqual((notion.pattern, notion.provider), ("www.notion.so/:id", "notion"))
        self.assert_rejected("http://10.0.0.5:9000/pages/a", "scheme_not_allowed", isolated=True)

    def test_core_09_to_14_generic_segment_rules(self):
        rows = [
            ("https://example.com/people/948203/profile", "example.com/people/:id/profile"),
            ("https://example.com/people/12/profile", "example.com/people/:id/profile"),
            ("https://example.com/orders/123e4567-e89b-12d3-a456-426614174000", "example.com/orders/:id"),
            ("https://example.com/x/0123456789abcdef0123", "example.com/x/:id"),
            ("https://example.com/blog/my-private-project-948203", "example.com/blog/:id"),
            ("https://example.com/p/title-abcdef01", "example.com/p/:id"),
            ("https://example.com/blog/my-first-post", "example.com/blog/my-first-post"),
            ("https://example.com/s/Ab3dE6gH9jK2mN5pQ8sT", "example.com/s/:id"),
            ("https://example.com/s/abcdefghijklmnopqrst", "example.com/s/abcdefghijklmnopqrst"),
            ("https://example.com/@jane/posts", "example.com/:handle/posts"),
            ("https://example.com/a/b/c<d/e", "example.com/a/b"),
            ("https://example.com/a/b/c/d/e/f/g/h/i", "example.com/a/b/c/d/e/f/g/h"),
            ("https://example.com/a/" + "x" * 41 + "/tail", "example.com/a"),
        ]
        for url, pattern in rows:
            with self.subTest(url=url):
                self.assert_url(url, pattern)
        self.assert_rejected("https://example.com/u/jane.doe@corp.test/doc", "pii_in_url")

    def test_core_15_google_provider_routes(self):
        rows = [
            ("https://docs.google.com/document/u/1/d/GDOC_ID_SENTINEL_0123456789ABCDEFGHIJ/edit?usp=sharing&resourcekey=RK_SENTINEL_x#heading=h.x", "docs.google.com/document/d/:id/edit", "google_docs"),
            ("https://docs.google.com/document/d/ID/preview", "docs.google.com/document/d/:id/preview", "google_docs"),
            ("https://docs.google.com/document/d/ID/foo/bar", "docs.google.com/document/d/:id", "google_docs"),
            ("https://docs.google.com/document/create", "docs.google.com/document", "google_docs"),
            ("https://docs.google.com/presentation/d/ID/edit#slide=id.p3", "docs.google.com/presentation/d/:id/edit", "google_slides"),
            ("https://docs.google.com/spreadsheets/d/ID/edit?gid=0", "docs.google.com/spreadsheets/d/:id/edit", "google_sheets"),
        ]
        for url, pattern, provider in rows:
            with self.subTest(url=url):
                result = self.assert_url(url, pattern, provider)
                self.assertNotIn("SENTINEL", result.pattern)

    def test_core_16_notion_provider_routes(self):
        rows = [
            ("https://www.notion.so/myws/Quarterly-Report-0123456789abcdef0123456789abcdef?pvs=4", "www.notion.so/:id"),
            ("https://acme.notion.site/Invoice-Template-0123456789abcdef0123456789abcdef", "acme.notion.site/:id"),
            ("https://notion.so/0123456789abcdef0123456789abcdef", "notion.so/:id"),
        ]
        for url, pattern in rows:
            with self.subTest(url=url):
                self.assert_url(url, pattern, "notion")

    def test_core_17_extension_providers(self):
        rows = [
            ("invoice.docx?download=1", "docx"), ("deck.PPTX", "pptx"),
            ("sheet.xlsx", "xlsx"), ("a.pdf", "pdf"),
            ("a.md", "markdown"), ("a.txt", "txt"),
        ]
        for path, provider in rows:
            url = "https://www.example.org/forms/" + path
            with self.subTest(path=path):
                pattern = "www.example.org/forms/" + path.split("?")[0].lower()
                self.assert_url(url, pattern, provider)

    def test_core_18_other_hosts_and_capability_id_redaction(self):
        rows = [
            ("https://example.com/anything", "example.com/anything", "other"),
            ("https://docs.google.com/forms/d/Ab3dE6gH9jK2mN5pQ8sT/edit", "docs.google.com/forms/d/:id/edit", "other"),
            ("https://www.canva.com/design/DAFxxxxxxxxA/abcDEF123456/view", "www.canva.com/design/:id", "other"),
        ]
        for url, pattern, provider in rows:
            with self.subTest(url=url):
                self.assert_url(url, pattern, provider)

    def test_core_20_source_ref_properties(self):
        canonical = "docs.google.com/document/d/:id/edit"
        key = bytes(range(32))
        first = source_ref(canonical, key)
        self.assertEqual(first, source_ref(canonical, key))
        self.assertNotEqual(first, source_ref(canonical, bytes(reversed(range(32)))))
        self.assertRegex(first, re.compile(r"^src_[a-z2-7]{26}$"))
        self.assertNotIn("FIXTURE_DOC_ID", first)
        self.assertEqual(len(first), 30)

    def test_core_24_url_length_limit(self):
        prefix = "https://example.com/"
        allowed = prefix + "x" * (2048 - len(prefix))
        rejected = prefix + "x" * (2049 - len(prefix))
        self.assertEqual(len(allowed), 2048)
        self.assertEqual(len(rejected), 2049)
        self.assertEqual(canonicalize(allowed).pattern, "example.com/")
        self.assert_rejected(rejected, "too_long")

    def test_canonical_pattern_and_capability_host_helpers(self):
        good = [
            "example.com/", "example.com/path-1", "docs.google.com/document/d/:id/edit",
            "notion.so/:id", "example.com/:handle",
        ]
        bad = [
            "https://example.com/path", "EXAMPLE.com/path", "example.com/path?x=1",
            "example.com:443/path", "example.com/Path", "example.com/a//b",
        ]
        for text in good:
            with self.subTest(pattern=text):
                self.assertTrue(is_canonical(text))
        for text in bad:
            with self.subTest(pattern=text):
                self.assertFalse(is_canonical(text))

        hosts = [
            "docs.google.com", "drive.google.com", "notion.so", "acme.notion.site",
            "dropbox.com", "onedrive.live.com", "1drv.ms", "team.sharepoint.com",
            "canva.com", "figma.com", "www.canva.com", "www.docs.google.com",
        ]
        for host in hosts:
            with self.subTest(host=host):
                self.assertTrue(is_capability_host(host))
        self.assertFalse(is_capability_host("example.com"))
        self.assertFalse(is_capability_host("notion.site"))

    def test_documented_mutations_are_exercised(self):
        with mock.patch.dict(os.environ, {"DMEM_DOUBLE_MUTATION": "leak_query"}):
            result = canonicalize("https://example.com/path?Q_SENTINEL=x#frag")
            self.assertEqual(result.pattern, "example.com/path?Q_SENTINEL=x")
        with mock.patch.dict(os.environ, {"DMEM_DOUBLE_MUTATION": "capability_leak"}):
            google = canonicalize("https://docs.google.com/document/d/RAW_GOOGLE_ID/edit")
            notion = canonicalize("https://www.notion.so/Title-0123456789abcdef0123456789abcdef")
            self.assertEqual(google.pattern, "docs.google.com/document/d/RAW_GOOGLE_ID/edit")
            self.assertEqual(notion.pattern, "www.notion.so/0123456789abcdef0123456789abcdef")


if __name__ == "__main__":
    unittest.main()
