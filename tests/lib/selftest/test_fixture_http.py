import json
import os
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, build_opener

from dmtest.fixture_http import FixtureServer


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class CountingRedirect(HTTPRedirectHandler):
    def __init__(self):
        super().__init__()
        self.count = 0

    def redirect_request(self, *args, **kwargs):
        self.count += 1
        return super().redirect_request(*args, **kwargs)


class FixtureHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="dmem-fixture-")
        cls.server = FixtureServer(cls.temp.name)
        cls.base = cls.server.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        cls.temp.cleanup()

    def setUp(self):
        self.server.reset()

    def get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=5) as response:
            return response.status, response.headers, response.read()

    def test_license_variants_and_resume_prose(self):
        markers = {
            "/pages/license-cc0.html": "creativecommons.org/publicdomain/zero/1.0/",
            "/pages/license-by-sa.html": "creativecommons.org/licenses/by-sa/4.0/",
            "/pages/license-mit.html": 'name="license" content="MIT"',
            "/pages/license-jsonld.html": '"license":"https://creativecommons.org/licenses/by/4.0/"',
            "/pages/license-nc.html": "creativecommons.org/licenses/by-nc/4.0/",
        }
        for path, marker in markers.items():
            with self.subTest(path=path):
                body = self.get(path)[2].decode("utf-8")
                self.assertIn(marker, body)
        none = self.get("/pages/license-none.html")[2].decode("utf-8")
        self.assertNotRegex(none, r'(?:rel|name)="license"|"license"\s*:')
        resume = self.get("/pages/resume-ko.html")[2].decode("utf-8")
        for n in range(1, 6):
            self.assertIn(f"PROSE_SENTINEL_{n}", resume)

    def test_noai_header_and_login_redirect(self):
        _, headers, _ = self.get("/pages/noai-header.html")
        self.assertEqual(headers.get("X-Robots-Tag"), "noai")
        self.assertIn(b'<meta name="robots" content="noai">', self.get("/pages/noai-meta.html")[2])
        opener = build_opener(NoRedirect())
        with self.assertRaises(urllib.error.HTTPError) as caught:
            opener.open(self.base + "/pages/login-required", timeout=5)
        self.assertEqual(caught.exception.code, 302)
        self.assertEqual(caught.exception.headers.get("Location"), "/login")
        caught.exception.close()
        login = self.get("/login")[2].decode("utf-8")
        self.assertIn('type="password"', login)

    def test_redirect_chain_count(self):
        redirects = CountingRedirect()
        opener = build_opener(redirects)
        target = quote("/pages/resume-us.html", safe="")
        with opener.open(self.base + "/redirect/3?to=" + target, timeout=5) as response:
            self.assertEqual(response.status, 200)
            self.assertIn(b"US Resume", response.read())
        self.assertEqual(redirects.count, 3)

    def test_big_body_length(self):
        _, _, body = self.get("/big")
        self.assertEqual(len(body), 6 * 1024 * 1024)

    def test_request_log_contains_header_names_only(self):
        secret = "COOKIE_VALUE_SENTINEL_9f3a"
        request = urllib.request.Request(self.base + "/pages/resume-us.html", headers={"Cookie": secret})
        with urllib.request.urlopen(request, timeout=5) as response:
            response.read()
        entry = next(item for item in self.server.log() if item["path"] == "/pages/resume-us.html")
        self.assertIn("Cookie", entry["header_names"])
        self.assertNotIn(secret, json.dumps(entry))
        log_text = (self.server.log_dir / "requests.jsonl").read_text(encoding="utf-8")
        self.assertNotIn(secret, log_text)

    def test_gzbomb_can_be_abandoned_without_blocking_server(self):
        started = time.monotonic()
        response = urllib.request.urlopen(self.base + "/gzbomb", timeout=3)
        data = response.read(1024)
        response.close()
        self.assertTrue(data)
        self.assertLess(time.monotonic() - started, 3)
        self.assertIn(b"Resume", self.get("/pages/resume-us.html")[2])

    def test_reset_truncates_request_log(self):
        self.get("/pages/resume-ko.html")
        self.assertTrue(self.server.log())
        self.server.reset()
        self.assertEqual(self.server.log(), [])

    def test_clean_shutdown_leaves_no_owned_process_group(self):
        with tempfile.TemporaryDirectory(prefix="dmem-fixture-stop-") as tmp:
            server = FixtureServer(tmp)
            server.start()
            process = server.process
            pid = process.pid
            server.stop()
            self.assertIsNotNone(process.poll())
            if os.name == "posix":
                with self.assertRaises(ProcessLookupError):
                    os.killpg(pid, 0)


if __name__ == "__main__":
    unittest.main()
