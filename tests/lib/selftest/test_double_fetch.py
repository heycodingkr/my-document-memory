"""Fetch guard, preview store and search client of the double (IMP-08..IMP-16, DISC-01..DISC-07)."""
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests" / "lib"))
sys.path.insert(0, str(ROOT / "tests" / "env" / "dmem-double"))
from dmem_double import fetch  # noqa: E402
from dmem_double.errors import DmemError  # noqa: E402
from dmtest.fixture_http import FixtureServer  # noqa: E402


def blocked(fn, code, reason=None):
    try:
        fn()
    except DmemError as exc:
        assert exc.code == code and (reason is None or exc.reason == reason), (exc.code, exc.reason)
        return
    raise AssertionError(f"expected {code}/{reason}")


class Guard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="dmem-fetch-")
        cls.server = FixtureServer(cls.tmp.name)
        cls.base = cls.server.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        cls.tmp.cleanup()

    def setUp(self):
        self.server.reset()
        os.environ.pop("DMEM_TEST_RESOLVE", None)
        os.environ.pop("DMEM_TEST_CLOCK_OFFSET", None)

    def get(self, path, **kw):
        return fetch.fetch(self.base + path, isolated=True, **kw)

    def test_ip_blocked_table(self):
        for ip in ("10.0.0.5", "127.0.0.1", "169.254.169.254", "172.16.0.1", "192.168.1.9", "100.64.0.1", "0.0.0.0", "::1", "fd00::1", "fe80::1",
                   "::ffff:10.0.0.5", "64:ff9b::a00:5", "224.0.0.1"):
            self.assertTrue(fetch.ip_blocked(ip), ip)
        for ip in ("93.184.216.34", "8.8.8.8", "2606:4700::1111", "203.0.113.10"):
            self.assertFalse(fetch.ip_blocked(ip), ip)

    def test_imp09_private_literals_never_connect(self):
        for url in ("https://10.0.0.5/", "https://169.254.169.254/latest/meta-data", "https://[fd00::1]/", "https://2130706433/", "https://0x7f.1/", "https://192.168.1.9/x"):
            blocked(lambda u=url: fetch.fetch(u), "fetch_blocked", "private_address")
        blocked(lambda: fetch.fetch(self.base + "/pages/resume-ko.html", isolated=False), "fetch_blocked", "private_address")  # loopback needs isolated mode
        self.assertEqual(self.server.log(), [])

    def test_imp10_resolver_sees_every_address(self):
        os.environ["DMEM_TEST_RESOLVE"] = "mixed.test=203.0.113.10,10.0.0.7;loop.test=127.0.0.1"
        blocked(lambda: fetch.fetch("https://mixed.test/x"), "fetch_blocked", "private_address")
        blocked(lambda: fetch.fetch("https://loop.test/x", isolated=True), "fetch_blocked", "private_address")
        self.assertEqual(fetch.resolve("mixed.test"), ["203.0.113.10", "10.0.0.7"])

    def test_imp11_redirects(self):
        self.assertEqual(self.get("/redirect/3?to=/pages/resume-ko.html").status, 200)
        blocked(lambda: self.get("/redirect/4?to=/pages/resume-ko.html"), "fetch_blocked", "redirect_limit")
        blocked(lambda: self.get("/redirect/private"), "fetch_blocked", "private_address")  # Location: http://10.255.255.1/
        self.assertTrue(fetch.is_downgrade("https://example.com/a", "http://example.com/b"))  # the loopback fixture is http-only: unit level (L0)
        self.assertFalse(fetch.is_downgrade("http://127.0.0.1/a", "http://127.0.0.1/b"))
        self.assertFalse(fetch.is_downgrade("https://example.com/a", "https://example.com/b"))

    def test_imp12_schemes_and_ports(self):
        for url in ("file:///etc/passwd", "ftp://example.com/x", "data:text/html,x", "javascript:alert(1)", "gopher://example.com/", "https://example.com:8443/"):
            blocked(lambda u=url: fetch.fetch(u), "fetch_blocked")

    def test_imp13_size_limits_stop_early(self):
        import tracemalloc
        tracemalloc.start()
        started = time.monotonic()
        blocked(lambda: self.get("/big"), "fetch_blocked", "size")
        blocked(lambda: self.get("/gzbomb"), "fetch_blocked", "size")  # 200 MiB of zeros once decoded, ~200 KiB on the wire
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        self.assertLess(peak, 40 * 1024 * 1024)  # the decoder never materialised the bomb (cap 5 MiB + bounded buffers)
        self.assertLess(time.monotonic() - started, 8)

    def test_imp14_timeout(self):
        started = time.monotonic()
        blocked(lambda: self.get("/slow", timeout=2.0), "fetch_blocked", "timeout")
        self.assertLess(time.monotonic() - started, 6)

    def test_imp15_content_type(self):
        blocked(lambda: self.get("/type-mismatch.docx"), "fetch_blocked", "content_type")
        blocked(lambda: self.get("/binary"), "fetch_blocked", "content_type")

    def test_imp16_login_pages_and_no_credentials(self):
        for path in ("/pages/login-required", "/pages/unauthorized", "/pages/forbidden"):
            blocked(lambda p=path: self.get(p), "fetch_blocked", "login_required")
        self.get("/pages/resume-ko.html")
        names = {n.lower() for row in self.server.log() for n in row["header_names"]}
        self.assertFalse(names & {"cookie", "authorization", "referer"})

    def test_imp08_noai_header(self):
        blocked(lambda: self.get("/pages/noai-header.html"), "fetch_blocked", "signal_noai")
        self.assertEqual(self.get("/pages/noai-meta.html").status, 200)

    def test_preview_store_ttl(self):
        with tempfile.TemporaryDirectory() as home:
            store = fetch.PreviewStore(home)
            pid = store.put({"doc": {"blocks": []}})
            self.assertEqual(store.get(pid), {"doc": {"blocks": []}})
            self.assertEqual(oct((Path(home) / "previews" / f"{pid}.json").stat().st_mode & 0o777), "0o600")
            os.environ["DMEM_TEST_CLOCK_OFFSET"] = "1000"  # 16 min 40 s later
            blocked(lambda: store.get(pid), "not_found")
            blocked(lambda: store.get("pv_000000000000"), "not_found")


class Search(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="dmem-search-")
        cls.server = FixtureServer(cls.tmp.name)
        cls.base = cls.server.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        cls.tmp.cleanup()

    def test_disc01_none_is_unavailable_without_network(self):
        self.server.reset()
        blocked(lambda: fetch.web_search("이력서 양식", "none", 5), "search_unavailable")
        self.assertEqual(self.server.log(), [])

    def test_disc02_07_fixture_provider(self):
        spec = f"fixture:{self.base}/search"
        out = fetch.web_search("이력서 양식", spec, 5)
        self.assertLessEqual(len(out["candidates"]), 5)
        out = fetch.web_search("이력서 양식", spec, 10)
        urls_ = [c["url"] for c in out["candidates"]]
        self.assertFalse(any(u.startswith(("file:", "http://192.168")) for u in urls_))
        self.assertGreaterEqual(out["filtered"], 2)
        self.assertTrue(all("?" not in u for u in urls_))

    def test_disc04_05_query_guards(self):
        spec = f"fixture:{self.base}/search"
        self.server.reset()
        blocked(lambda: fetch.web_search("sk-test-" + "A1b2C3d4" * 4, spec, 5), "secret_detected")
        blocked(lambda: fetch.web_search("x" * 201, spec, 5), "payload_too_large")
        fetch.web_search("x" * 200, spec, 5)
        self.assertEqual(len([r for r in self.server.log() if r["path"] == "/search"]), 1)  # only the valid 200-char query went out


if __name__ == "__main__":
    unittest.main()
