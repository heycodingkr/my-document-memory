#!/usr/bin/env python3
"""WI real Rust CLI/MCP/HTTP acceptance, fake browser controls, optional actual Arise/UI.

    cargo build --workspace --examples
    pnpm --dir web build
    python3 -B tests/smoke/web-memory-v1.py --arise --browser

All databases/servers/documents are disposable. Only a newly owned Arise tab is changed.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests/lib"))
from dmtest.fixture_http import FixtureServer
from dmtest.mcpclient import McpSession

TOKEN = "synthetic-web-smoke-token-at-least-32"
CAPTURE = "synthetic-capture-secret-for-web-smoke-12345"
BIN = ROOT / "target/debug"
RESULTS = []


def check(name, ok):
    RESULTS.append({"id": name, "verdict": "PASS" if ok else "FAIL"})
    print(("PASS " if ok else "FAIL ") + name, flush=True)
    assert ok, name


def value(reply):
    assert reply is not None and not reply.is_error, "tool failed"
    result = reply.structured if reply.structured is not None else reply.json
    return result.get("reply", result) if isinstance(result, dict) else result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arise", action="store_true")
    parser.add_argument("--browser", action="store_true")
    args = parser.parse_args()
    out = ROOT / "target/e2e-logs/web-memory" / (time.strftime("%Y%m%d-%H%M%S") + "-" + str(os.getpid()))
    out.mkdir(parents=True)
    print("evidence:", out, flush=True)
    with tempfile.TemporaryDirectory(prefix="dmem-web-") as temporary, FixtureServer(out / "fixture") as fixture:
        tmp = Path(temporary)
        site = fixture.base_url
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        env = {**os.environ, "DMEM_URL": base, "DMEM_TOKEN": TOKEN, "DMEM_CAPTURE_SECRET": CAPTURE,
               "DMEM_ADDR": f"127.0.0.1:{port}", "DMEM_DATABASE": str(tmp / "library.sqlite3"),
               "DMEM_FIXTURE_ADDR": urllib.parse.urlsplit(site).netloc, "DMEM_WEB_DIR": str(ROOT / "web/dist")}
        log = (out / "server.log").open("wb")
        server = subprocess.Popen([str(BIN / "examples/web_fixture")], cwd=tmp, env=env, stdout=log, stderr=log)

        def http(path, data=None, token=TOKEN):
            request = urllib.request.Request(base + path, data=None if data is None else json.dumps(data).encode(), headers={"Content-Type": "application/json", **({"Authorization": "Bearer " + token} if token else {})})
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    return response.status, json.load(response)
            except urllib.error.HTTPError as error:
                return error.code, json.load(error)

        def cli(*a, expected=0):
            result = subprocess.run([str(BIN / "dmem"), *a], cwd=tmp, env=env, capture_output=True, text=True, timeout=30)
            assert result.returncode == expected, result.stderr
            assert TOKEN not in result.stdout + result.stderr and CAPTURE not in result.stdout + result.stderr
            return json.loads(result.stdout) if expected == 0 else result.stderr

        def count():
            with sqlite3.connect(tmp / "library.sqlite3") as db:
                return db.execute("SELECT count(*) FROM records WHERE owner='local'").fetchone()[0]

        def start_mcp(command):
            session = McpSession(command, env)
            assert session.initialize() is not None
            return session

        try:
            for _ in range(100):
                assert server.poll() is None, "fixture server exited"
                try:
                    if http("/healthz")[0] == 200:
                        break
                except OSError:
                    pass
                time.sleep(.05)
            else:
                raise AssertionError("fixture server did not start")
            before = count()
            preview = cli("web", "preview", site + "/pages/resume-ko.html?URL_QUERY_SENTINEL=1#URL_FRAGMENT_SENTINEL")
            check("WI-08 preview creates no record", count() == before and preview["untrusted"] and preview["license"] == "CC-BY-4.0")
            check("WI-06 projected source excludes query and fragment", "URL_QUERY_SENTINEL" not in json.dumps(preview) and "URL_FRAGMENT_SENTINEL" not in json.dumps(preview))
            imported = cli("web", "import", preview["preview_id"], "--provider", "google_docs", "--doc-type", "resume", "--locale", "ko-KR")
            template = cli("template-show", imported["id"])
            check("WI-11 CLI form is preserved", template["form"]["provider"] == "google_docs" and template["form"]["locale"] == "ko-KR" and imported["origin"]["copy_policy"] == "structure_only")
            again = cli("web", "import", preview["preview_id"], "--provider", "google_docs", "--doc-type", "resume", "--locale", "ko-KR")
            check("WI-10 repeat import is idempotent", again["id"] == imported["id"] and not again["created"])
            check("WI-17 CLI origin persists", cli("web", "origin", imported["id"])["license"] == "CC-BY-4.0")
            check("WI-09 private provenance is isolated", http("/v1/web/origins/" + imported["id"], token="synthetic-web-bob-token-at-least-32")[0] == 404)
            with start_mcp([str(BIN / "dmem-mcp")]) as mcp:
                names = {t["name"] for t in mcp.list_tools()}
                check("WI-17 real MCP web tools are present", {"document_web_search", "document_web_preview", "document_web_import", "document_web_origin"} <= names)
                reference = value(mcp.call("document_web_import", {"preview_id": preview["preview_id"], "kind": "reference", "copy_mode": "full"}))
                source = http("/v1/sources/" + reference["id"])[1]
                check("WI-12 licensed full reference includes visible text", "PROSE_SENTINEL_1" in json.dumps(source))
                nc = value(mcp.call("document_web_preview", {"url": site + "/pages/license-nc.html"}))
                denied = mcp.call("document_web_import", {"preview_id": nc["preview_id"], "kind": "reference", "copy_mode": "full"})
                check("WI-02 restrictive full copy is refused", denied.is_error and denied.json["code"] == "license_forbids")
                structure = value(mcp.call("document_web_import", {"preview_id": nc["preview_id"], "kind": "reference"}))
                source = http("/v1/sources/" + structure["id"])[1]
                check("WI-02 structure copy removes body and table cells", "PROSE_SENTINEL_N1" not in json.dumps(source) and "BODYCELL_N1" not in json.dumps(source) and structure["body_chars_removed"] > 0)
                check("WI-17 MCP stdout has no noise", mcp.noise_bytes == 0)
            for path, provider, forbidden in [("/p/google-docs/document/d/FIX_KO_RESUME/edit", "google_docs", "FIX_KO_RESUME"), ("/p/google-slides/presentation/d/FIX_DECK/edit", "google_slides", "FIX_DECK")]:
                exported = cli("web", "preview", site + path)
                check("WI-14 " + provider + " export", exported["provider"] == provider and exported["outline"] and forbidden not in json.dumps(exported))
            status, error = http("/v1/web/preview", {"url": "http://169.254.169.254/latest/meta-data/"})
            check("WI-07 metadata endpoint refused", status == 422 and error["code"] == "fetch_blocked")
            status, error = http("/v1/web/search", {"query": "document templates"})
            check("WI-15 missing search config is explicit", status == 503 and error["code"] == "search_unavailable")
            command = [str(BIN / "dmem"), "browser-mcp", "--browser-mcp", sys.executable, "--browser-arg=-u", "--browser-arg=" + str(ROOT / "tests/fixtures/browser-mcp-web.py")]
            with start_mcp(command) as bridge:
                names = {t["name"] for t in bridge.list_tools()}
                check("WI-19 browser tools and clip aliases coexist", {"browser_tabs", "document_web_preview", "document_memory_clip_current_tab", "doc_memory_clip_current_tab"} <= names)
                sid = "synthetic-web-bridge"
                value(bridge.call("browser_new_tab", {"session_id": sid, "url": site + "/synthetic?BRIDGE_QUERY_SENTINEL=1"}))
                normal = value(bridge.call("document_memory_clip_current_tab", {"session_id": sid}))
                check("WI-20 bridge produces captured provenance", normal["origin"]["provenance"] == "captured" and "BRIDGE_QUERY_SENTINEL" not in json.dumps(normal))
                pid = None
                for mode in ["foreign", "expired", "no_lease", "eval_error", "sensitive", "changed"]:
                    state = value(bridge.call("browser_test_mode", {"mode": mode}))
                    if pid is None:
                        pid = state["pid"]
                    before = count()
                    blocked = bridge.call("document_memory_clip_current_tab", {"session_id": sid})
                    check("WI-21 refuse " + mode, blocked.is_error and count() == before and state["pid"] == pid)
                blocked = bridge.call("document_memory_clip_current_tab", {"session_id": sid, "url": "https://example.com/"})
                check("WI-22 model cannot supply capture URL", blocked.is_error and blocked.json["code"] == "invalid_input")
                bridge.send([])
                reply = bridge.read(timeout=5)
                check("WI-19 malformed request gets a response", reply is not None and reply.get("error", {}).get("code") == -32600)
                check("WI-19 retained bridge stdout is pure JSON", bridge.noise_bytes == 0)
            if args.browser:
                result = subprocess.run(["pnpm", "--dir", "web", "test:e2e", "tests/web-memory.spec.ts"], cwd=ROOT, env={**env, "DMEM_E2E_URL": base, "DMEM_E2E_TOKEN": TOKEN, "DMEM_WEB_FIXTURE_URL": site, "DMEM_E2E_OUTPUT_DIR": str(out / "playwright")}, capture_output=True, text=True, timeout=120)
                (out / "web.log").write_text(result.stdout + result.stderr)
                check("WI-18 web import workflow", result.returncode == 0)
            if args.arise:
                run_arise(env, site, base, out, cli, http)
            with sqlite3.connect(tmp / "library.sqlite3") as db:
                payloads = "\n".join(r[0] for r in db.execute("SELECT payload FROM records UNION ALL SELECT payload FROM web_origins"))
                check("WI-06 persistent payloads exclude URL secrets", all(marker not in payloads for marker in ["URL_QUERY_SENTINEL", "URL_FRAGMENT_SENTINEL", "BRIDGE_QUERY_SENTINEL"]))
        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
            log.close()
            (out / "results.json").write_text(json.dumps(RESULTS, indent=2))
            (out / "summary.md").write_text("# Web memory product smoke\n\n" + "\n".join(f"- {r['verdict']} {r['id']}" for r in RESULTS) + "\n")
    print("complete:", len(RESULTS), "checks; evidence", out)


def run_arise(env, site, base, out, cli, http):
    session = "dmem-web-arise-" + str(time.time_ns())
    tab = None
    with McpSession([str(BIN / "dmem"), "browser-mcp", "--browser-mcp", "/Applications/Arise.app/Contents/MacOS/agent_browser"], env) as browser:
        def wait_eval(js, accept, label):
            # Navigation can invalidate an in-flight CEF evaluation. A successful
            # evaluation of the actual expected state is still mandatory.
            last = None
            for _ in range(60):
                reply = browser.call("browser_eval", {"session_id": session, "js": js})
                if reply is not None and not reply.is_error:
                    last = value(reply)
                    if accept(last.get("result")):
                        return last
                elif reply is not None:
                    last = reply.json
                time.sleep(.15)
            (out / ("arise-" + label + "-error.json")).write_text(json.dumps(last))
            raise AssertionError("Arise state did not become ready: " + label)

        assert browser.initialize() is not None
        browser.list_tools()
        before = value(browser.call("browser_tabs", {"session_id": session}))
        user_before = {t["tab_id"]: (t.get("url"), t.get("title")) for t in before.get("tabs", []) if not t.get("owner")}
        try:
            opened = value(browser.call("browser_new_tab", {"session_id": session, "url": site + "/pages/resume-ko.html?ARISE_QUERY_SENTINEL=1#ARISE_FRAGMENT_SENTINEL", "activate": False}))
            tab = opened["tab_id"]
            wait_eval("location.pathname", lambda result: result == "/pages/resume-ko.html", "source")
            result = value(browser.call("document_memory_clip_current_tab", {"session_id": session, "form": {"provider": "google_docs", "doc_type": "resume", "locale": "ko-KR"}}))
            template = cli("template-show", result["id"])
            check("WI-23 actual Arise clip persists correct structure", result["origin"]["provenance"] == "captured" and "경력" in template["sections"] and template["form"]["locale"] == "ko-KR")
            check("WI-23 actual Arise provenance projects private URL parts", all(s not in json.dumps(result) for s in ["ARISE_QUERY_SENTINEL", "ARISE_FRAGMENT_SENTINEL"]))
            shot = browser.call("browser_screenshot", {"session_id": session})
            for block in shot.raw.get("content", []):
                if block.get("type") == "image":
                    (out / "arise-source.png").write_bytes(base64.b64decode(block["data"]))
            value(browser.call("browser_navigate", {"session_id": session, "url": site + "/pages/hostile-static.html"}))
            wait_eval("location.pathname", lambda result: result == "/pages/hostile-static.html", "hostile")
            hostile = value(browser.call("document_memory_clip_current_tab", {"session_id": session}))
            saved = cli("template-show", hostile["id"])
            check("WI-23 actual hostile page is sanitized", "Real section" in saved["sections"] and "HIDDEN_SENTINEL" not in json.dumps(saved) and "ignore all previous" not in json.dumps(saved).lower())
            value(browser.call("browser_navigate", {"session_id": session, "url": base + "/#templates"}))
            wait_eval("location.origin", lambda result: result == base, "app-origin")
            value(browser.call("browser_eval",{"session_id":session,"js":"(()=>{sessionStorage.setItem('dmem.token',"+json.dumps(TOKEN)+");setTimeout(()=>location.reload(),0);return 'prepared';})()"}))
            wait_eval("Boolean(document.querySelector('details.web-import'))", lambda result: str(result).lower() == "true", "app-panel")
            value(browser.call("browser_select_tab",{"session_id":session,"tab_id":tab}))
            value(browser.call("browser_snapshot",{"session_id":session}))
            value(browser.call("browser_click",{"session_id":session,"selector":"details.web-import > summary"}))
            value(browser.call("browser_type",{"session_id":session,"selector":"input[aria-label='Document URL']","text":site+"/pages/resume-ko.html"}))
            wait_eval("document.querySelector('input[aria-label=\"Document URL\"]')?.value||''", lambda result: result == site+"/pages/resume-ko.html", "url-input")
            value(browser.call("browser_click",{"session_id":session,"selector":"details.web-import form:has(input[aria-label='Document URL']) button"}))
            wait_eval("Boolean(document.querySelector('.web-preview'))", lambda result: str(result).lower() == "true", "url-preview")
            value(browser.call("browser_type",{"session_id":session,"selector":"input[aria-label='Import title']","text":"Arise web UI structure"}))
            value(browser.call("browser_click",{"session_id":session,"selector":"details.web-import button.primary"}))
            for _ in range(60):
                ready=value(browser.call("browser_eval",{"session_id":session,"js":"document.querySelector('.web-content [role=status]')?.textContent||''"}))
                if "Saved to your private library" in ready.get("result",""):break
                time.sleep(.15)
            status, records=http("/v1/templates?q=Arise%20web%20UI%20structure")
            check("WI-18 actual Arise native form saves through the app",status==200 and any(t["title"]=="Arise web UI structure" and t["form"]["region"]=="KR" for t in records["items"]))
            shot=browser.call("browser_screenshot",{"session_id":session})
            for block in shot.raw.get("content",[]):
                if block.get("type")=="image":(out/"arise-web-ui.png").write_bytes(base64.b64decode(block["data"]))
        finally:
            if tab is not None:
                value(browser.call("browser_close_tab", {"session_id": session, "tab_id": tab}))
                # The native close response acknowledges dispatch. A foreground CEF
                # tab can remain in browser_tabs briefly; verify removal before release.
                for _ in range(40):
                    closed=value(browser.call("browser_tabs",{"session_id":session}))
                    if not any(t["tab_id"]==tab for t in closed.get("tabs",[])):break
                    time.sleep(.075)
            value(browser.call("browser_release", {"session_id": session}))
            after = value(browser.call("browser_tabs", {"session_id": session}))
            user_after = {t["tab_id"]: (t.get("url"), t.get("title")) for t in after.get("tabs", []) if not t.get("owner")}
            check("WI-23 user tabs remain unchanged; own tab closed", user_before == user_after and not any(t["tab_id"] == tab for t in after.get("tabs", [])))


if __name__ == "__main__":
    main()
