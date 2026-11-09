#!/usr/bin/env python3
"""Read-only hosted API checks; private credentials never enter output."""
import argparse
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--api", default="https://api.mydocumentmemory.com")
parser.add_argument("--web", default="https://mydocumentmemory.com")
parser.add_argument("--env", type=Path, default=Path(".env.production"))
parser.add_argument("--out", type=Path)
args = parser.parse_args()
api, web = args.api.rstrip("/"), args.web.rstrip("/")
for base in (api, web):
    url = urllib.parse.urlsplit(base)
    assert (url.scheme == "https" and url.hostname and not url.username
            and not url.password and not url.query and not url.fragment
            and not url.path), "Use an HTTPS origin without a path"
config = dict(line.split("=", 1) for line in args.env.read_text().splitlines()
              if "=" in line and not line.startswith("#"))
token = config["DMEM_TOKEN"].strip().strip("\"'")
assert len(token) >= 16, "Private library token required"
passed = []


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


opener = urllib.request.build_opener(NoRedirect())


def request(path, *, base=api, auth=None, origin=None, method="GET", extra=None):
    headers = dict(extra or {})
    if auth is not None:
        headers["Authorization"] = "Bearer " + auth
    if origin:
        headers["Origin"] = origin
    req = urllib.request.Request(base + path, headers=headers, method=method)
    try:
        response = opener.open(req, timeout=15)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        raw = response.read()
        assert token.encode() not in raw, "Response contains private credentials"
        return response.code, raw, response.headers


def read(path, **kwargs):
    code, raw, headers = request(path, **kwargs)
    assert code == 200, f"{path}: HTTP {code}"
    return json.loads(raw), headers


assert read("/healthz")[0] == {"ready": True}
passed.append("API public certificate and HTTPS readiness")
code, _, headers = request("/healthz", base="http://" + urllib.parse.urlsplit(api).netloc)
assert code in (301, 308) and headers.get("Location") == api + "/healthz"
passed.append("HTTP redirects to the same HTTPS API path")

catalog, _ = read("/v1/public/templates")
assert catalog["items"] and all(t["visibility"] == "public" for t in catalog["items"])
assert read("/v1/auth/config")[0] == read("/v1/auth/config", base=web)[0]
assert read("/v1/auth/config")[0]["email_enabled"] is True
passed.append("anonymous public templates and unchanged email configuration")
for credential in (None, "wrong-connection-token"):
    code, raw, _ = request("/v1/templates", auth=credential)
    assert code == 401 and json.loads(raw)["code"] == "auth_required"
passed.append("missing and invalid credentials rejected")
status, _ = read("/v1/status", auth=token)
assert status["service"] == "my-document-memory"
status, headers = read("/v1/status", auth=token, origin=web)
assert status["service"] == "my-document-memory"
assert headers.get("Access-Control-Allow-Origin") == web
assert headers.get("Access-Control-Allow-Credentials") == "true"
passed.append("token clients and exact hosted web Origin accepted")

code, _, headers = request("/v1/templates", method="OPTIONS", origin=web, extra={
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "authorization,content-type",
})
assert code in (200, 204) and headers.get("Access-Control-Allow-Origin") == web
assert "POST" in headers.get("Access-Control-Allow-Methods", "")
assert {"authorization", "content-type"} <= {
    h.strip().lower() for h in headers.get("Access-Control-Allow-Headers", "").split(",")
}
passed.append("hosted web CORS preflight accepted")
code, raw, headers = request("/v1/status", auth=token, origin="https://untrusted.invalid")
assert code == 401 and json.loads(raw)["code"] == "auth_required"
assert headers.get("Access-Control-Allow-Origin") is None
passed.append("unrelated Origin rejected without permissive CORS")
for path in ("/", "/assets/probe.js"):
    assert request(path)[0] == 404, f"{path} must not serve the web app"
passed.append("API hostname exposes no web assets")
assert read("/healthz", base=web)[0] == {"ready": True}
passed.append("existing web HTTPS readiness preserved")
result = {"api": api, "web": web, "passed": passed}
if args.out:
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
for check in passed:
    print("PASS:", check)
