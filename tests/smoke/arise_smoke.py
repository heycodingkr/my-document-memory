#!/usr/bin/env python3
"""Arise browser environment smoke (HARN-05, HARN-06, SMK-14 partial).

Drives the INSTALLED Arise through its public stdio MCP (`agent_browser --mcp-server`), never CDP and never the
private control socket. It opens ONE session-owned background tab on the loopback fixture server, checks that the
provider-shaped, license and hostile fixture pages render with the expected landmarks, handles the JavaScript dialog the
active hostile page raises (explicit inspect -> dismiss, nothing is auto-approved), then closes ONLY its own tab and
proves that every tab it did not own is still there. It never calls the global `browser_close`.

    python3 -B tests/smoke/arise_smoke.py [--browser-mcp PATH] [--out DIR] [--no-shots]

Exit code 0 = all checks passed, 1 = a check failed, 2 = environment problem (Arise missing, no window).
Evidence: target/e2e-logs/arise/<run-id>/ (meta.json, cases.jsonl, trace.jsonl, shots/, summary.md).
"""
import argparse
import base64
import json
import os
import plistlib
import selectors
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "lib"))
from dmtest.fixture_http import FixtureServer  # noqa: E402

DEFAULT_BIN = "/Applications/Arise.app/Contents/MacOS/agent_browser"
REQUIRED_TOOLS = ["browser_tabs", "browser_new_tab", "browser_navigate", "browser_eval", "browser_wait_for",
                  "browser_close_tab", "browser_release", "browser_dialog", "browser_screenshot", "browser_snapshot"]


class Evidence:
    def __init__(self, base):
        run_id = time.strftime("%Y%m%d-%H%M%S") + f"-{os.getpid() % 10000:04d}"
        self.path = Path(base) / "arise" / run_id
        (self.path / "shots").mkdir(parents=True, exist_ok=True)
        self.cases, self.failures = [], 0

    def trace(self, event, **fields):
        with open(self.path / "trace.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": round(time.time(), 3), "event": event, **fields}, ensure_ascii=False) + "\n")

    def case(self, case_id, check, ok, detail=""):
        verdict = "PASS" if ok else "FAIL"
        self.failures += 0 if ok else 1
        row = {"id": case_id, "check": check, "verdict": verdict, "detail": detail}
        self.cases.append(row)
        with open(self.path / "cases.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"  [{verdict}] {case_id} {check}" + (f" — {detail}" if detail and not ok else ""))
        return ok

    def finish(self, meta):
        (self.path / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        lines = ["# Arise environment smoke", "", f"checks: {len(self.cases)}  failures: {self.failures}", ""]
        lines += [f"- {c['verdict']} `{c['id']}` {c['check']}" + (f" ({c['detail']})" if c["detail"] else "") for c in self.cases]
        (self.path / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


class McpChild:
    """Newline-delimited JSON-RPC over the child's stdio (MCP stdio transport)."""

    def __init__(self, program, client):
        self.p = subprocess.Popen([program, "--mcp-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1, env=dict(os.environ))
        self.n = 0
        self.called = []  # (tool name, arguments) of every tools/call this run made
        self.rpc("initialize", {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": client, "version": "1"}})
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self.p.stdin.flush()

    def rpc(self, method, params, timeout=25):
        self.n += 1
        ident = self.n
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": ident, "method": method, "params": params}) + "\n")
        self.p.stdin.flush()
        sel = selectors.DefaultSelector()
        sel.register(self.p.stdout, selectors.EVENT_READ)
        deadline = time.time() + timeout
        try:
            while time.time() < deadline:
                if not sel.select(max(0.05, deadline - time.time())):
                    continue
                line = self.p.stdout.readline()
                if not line:
                    raise RuntimeError("browser MCP exited")
                try:
                    msg = json.loads(line)
                except ValueError:
                    continue
                if msg.get("id") == ident:
                    if "error" in msg:
                        raise RuntimeError(f"protocol error {msg['error'].get('code')}")
                    return msg["result"]
            raise RuntimeError(f"timeout waiting for {method}")
        finally:
            sel.close()

    def call(self, name, args):
        """Returns (ok, value, raw_text). value is the parsed `reply` object when the tool returned JSON."""
        self.called.append((name, dict(args)))
        result = self.rpc("tools/call", {"name": name, "arguments": args})
        texts = [c.get("text", "") for c in result.get("content", []) if c.get("type") == "text"]
        text = texts[0] if texts else ""
        value = None
        try:
            parsed = json.loads(text)
            value = parsed.get("reply", parsed) if isinstance(parsed, dict) else parsed
        except ValueError:
            pass
        images = [c for c in result.get("content", []) if c.get("type") == "image"]
        return (not result.get("isError", False)), value, text, images

    def close(self):
        try:
            self.p.stdin.close()
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()
            self.p.wait(timeout=3)


def arise_version(binary):
    try:
        plist = Path(binary).resolve().parents[1] / "Info.plist"
        return plistlib.loads(plist.read_bytes()).get("CFBundleShortVersionString")
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--browser-mcp", default=DEFAULT_BIN)
    ap.add_argument("--out", default=str(ROOT / "target" / "e2e-logs"))
    ap.add_argument("--no-shots", action="store_true")
    args = ap.parse_args()

    ev = Evidence(args.out)
    print(f"evidence: {ev.path}")
    if not os.access(args.browser_mcp, os.X_OK):
        print(f"SKIP(env): Arise MCP binary not found at {args.browser_mcp}")
        ev.finish({"status": "skipped", "reason": "arise_binary_missing"})
        return 2

    session = f"dmem-arise-smoke-{time.time_ns()}"
    own_tab, mcp, fixture = None, None, None
    before_user = {}
    try:
        fixture = FixtureServer(str(ev.path / "fixture"))
        base = fixture.start()
        ev.trace("fixture_started", base=base)
        mcp = McpChild(args.browser_mcp, "dmem-arise-smoke")
        tools = [t["name"] for t in mcp.rpc("tools/list", {}).get("tools", [])]
        missing = [t for t in REQUIRED_TOOLS if t not in tools]
        ev.case("HARN-06", "required browser MCP tools are exposed", not missing, f"missing={missing}")
        if missing:
            return 2

        ok, tabs, _, _ = mcp.call("browser_tabs", {"session_id": session})
        windows = (tabs or {}).get("windows", [])
        if not ok or not windows:
            print("SKIP(env): Arise has no browser window; activate Arise and open File > New Window, then retry")
            ev.finish({"status": "skipped", "reason": "no_window"})
            return 2
        window_id = windows[0]["window_id"]
        before_user = {t["tab_id"]: (t["url"], t["title"]) for t in tabs["tabs"] if not t.get("owner")}
        before_ids = {t["tab_id"] for t in tabs["tabs"]}
        ev.trace("tabs_before", user_tabs=len(before_user), all_tabs=len(before_ids))

        def goto(path, first=False, wait_selector="body", timeout=10):
            nonlocal own_tab
            url = base + path
            if first:
                ok_, val, text, _ = mcp.call("browser_new_tab", {"session_id": session, "url": url, "window_id": window_id, "activate": False})
                if not ok_ or not val:
                    raise RuntimeError("browser_new_tab failed")
                own_tab = val.get("tab_id")
            else:
                mcp.call("browser_navigate", {"session_id": session, "url": url})
            deadline = time.time() + timeout
            while time.time() < deadline:  # `ready` alone does not prove navigation finished: wait for the target path
                ok_, val, text, _ = mcp.call("browser_eval", {"session_id": session, "js": "location.pathname"})
                if "javascript_dialog_pending" in text:
                    return "dialog"
                if ok_ and val and path.split("?")[0] in json.dumps(val, ensure_ascii=False):
                    return "ok"
                time.sleep(0.15)
            return "timeout"

        def landmarks(js):
            ok_, val, text, _ = mcp.call("browser_eval", {"session_id": session, "js": f"JSON.stringify({js})"})
            if not ok_ or not isinstance(val, dict) or "result" not in val:
                return None
            try:
                return json.loads(val["result"])
            except (ValueError, TypeError):
                return None

        # 1) Korean resume (CC-BY, table, headings, prose sentinels, lang) — also the first page, which creates our tab
        state = goto("/pages/resume-ko.html?Q_SENTINEL_arise=1#F_SENTINEL_arise", first=True)
        ev.case("HARN-06", "session-owned tab opened and target page loaded", state == "ok" and own_tab is not None, f"state={state}")
        lm = landmarks("{href: location.href, title: document.title, h2: Array.from(document.querySelectorAll('h2')).map(h=>h.textContent),"
                       " license: (document.querySelector('link[rel=license]')||{}).href||null, tables: document.querySelectorAll('table').length,"
                       " prose: (document.body.innerText.match(/PROSE_SENTINEL_\\d/g)||[]).length, lang: document.documentElement.lang}")
        ev.case("HARN-06", "resume-ko landmarks (title, 4 headings, CC-BY link, 1 table, 5 prose sentinels, lang=ko)",
                bool(lm) and lm["title"] == "한국어 이력서 양식" and lm["h2"] == ["인적사항", "경력", "학력", "기술"]
                and lm["license"] == "https://creativecommons.org/licenses/by/4.0/" and lm["tables"] == 1 and lm["prose"] == 5 and lm["lang"] == "ko",
                json.dumps(lm, ensure_ascii=False))
        ev.case("HARN-06", "browser keeps the raw query/fragment (the clip adapter, not the browser, must canonicalize)",
                bool(lm) and "Q_SENTINEL_arise" in lm["href"] and "F_SENTINEL_arise" in lm["href"])
        if not args.no_shots:
            ok_, _, _, images = mcp.call("browser_screenshot", {"session_id": session})
            if images:
                (ev.path / "shots" / "resume-ko.png").write_bytes(base64.b64decode(images[0].get("data", "")))
                ev.trace("screenshot", file="shots/resume-ko.png")

        # 2) license variants
        for page, expect in [("/pages/license-cc0.html", "zero/1.0"), ("/pages/license-by-sa.html", "by-sa/4.0"), ("/pages/license-nc.html", "by-nc/4.0")]:
            goto(page)
            lm = landmarks("{link: (document.querySelector('link[rel=license]')||{}).href||null}")
            ev.case("HARN-06", f"{page} exposes the expected license link", bool(lm) and expect in (lm["link"] or ""))
        goto("/pages/license-mit.html")
        lm = landmarks("{meta: (document.querySelector('meta[name=license]')||{}).content||null}")
        ev.case("HARN-06", "license-mit.html exposes meta license MIT", bool(lm) and lm["meta"] == "MIT")

        # 3) provider-shaped pages
        goto("/p/google-docs/document/d/FIX_KO_RESUME/edit")
        lm = landmarks("{path: location.pathname, title: document.title}")
        ev.case("HARN-06", "google-docs shaped fixture path renders", bool(lm) and lm["path"].startswith("/p/google-docs/document/d/"), json.dumps(lm, ensure_ascii=False))
        goto("/p/notion/Quarterly-Report-0123456789abcdef0123456789abcdef")
        lm = landmarks("{h: document.querySelectorAll('h1,h2').length, lists: document.querySelectorAll('ul,ol').length, tables: document.querySelectorAll('table').length}")
        ev.case("HARN-06", "notion shaped fixture renders headings, list and table", bool(lm) and lm["h"] >= 1 and lm["lists"] >= 1 and lm["tables"] >= 1, json.dumps(lm))

        # 4) static hostile page: text-level attacks visible to DOM readers, no active content
        goto("/pages/hostile-static.html")
        lm = landmarks("{visible_injection: /ignore all previous instructions/i.test(document.body.innerText), visible_ko: /이전 지시를 무시/.test(document.body.innerText),"
                       " in_inner: [1,2,3].map(n => document.body.innerText.includes('HIDDEN_SENTINEL_'+n)),"
                       " dom_hidden: (document.body.textContent.match(/HIDDEN_SENTINEL_\\d/g)||[]).length,"
                       " zero_width: /[\\u200b-\\u200f\\u202a-\\u202e\\u2066-\\u2069]/.test(document.body.textContent), scripts: document.scripts.length}")
        # Measured on Arise 0.1.76: display:none text is NOT in innerText, but zero-size and same-colour text IS. A clip adapter that reads
        # innerText would therefore capture sentinels 2 and 3 (invisible to people) - the sanitiser must remove them (IMP-17, IMP-19).
        ev.case("HARN-06", "hostile-static: injection phrases visible; display:none text absent from innerText; zero-size and same-colour text still exposed to text readers; zero-width present; no script",
                bool(lm) and lm["visible_injection"] and lm["visible_ko"] and lm["in_inner"] == [False, True, True] and lm["dom_hidden"] == 3
                and lm["zero_width"] and lm["scripts"] == 0, json.dumps(lm))

        # 5) active hostile page: the browser runs the payload and raises a dialog; Arise must refuse further tools until it is answered
        state = goto("/pages/hostile-inject.html", timeout=6)
        ok_, _, text, _ = mcp.call("browser_eval", {"session_id": session, "js": "1"})
        pending = "javascript_dialog_pending" in text
        ev.case("HARN-06", "active hostile page raises a dialog and Arise blocks other tools until it is handled (nothing auto-approved)", pending, f"nav={state}")
        if pending:
            ok_, dialog, text, _ = mcp.call("browser_dialog", {"session_id": session, "action": "inspect"})
            dialog_obj = (dialog or {}).get("dialog", dialog or {})
            dialog_id = dialog_obj.get("id") or dialog_obj.get("dialog_id")
            ev.case("HARN-06", "dialog is inspected before it is answered (message is the fixture's, treated as untrusted)",
                    bool(dialog_id) and dialog_obj.get("message") == "injected", json.dumps(dialog_obj, ensure_ascii=False)[:200])
            ok_, _, _, _ = mcp.call("browser_dialog", {"session_id": session, "action": "dismiss", "dialog_id": dialog_id})
            ev.case("HARN-06", "dialog dismissed explicitly", ok_)
            ok_, _, text, _ = mcp.call("browser_eval", {"session_id": session, "js": "document.body.textContent.slice(0,20)"})
            ev.case("HARN-06", "tools work again after the dialog is answered", ok_ and "dialog_pending" not in text)

        # 6) cleanup: close ONLY our tab, release, and prove every other tab is untouched
        ok_, closed, _, _ = mcp.call("browser_close_tab", {"session_id": session, "tab_id": own_tab})
        ev.case("SMK-14", "own tab closed (tab id is the one this session created)", ok_)
        mcp.call("browser_release", {"session_id": session})
        time.sleep(0.4)
        ok_, tabs2, _, _ = mcp.call("browser_tabs", {"session_id": session})
        after_ids = {t["tab_id"] for t in (tabs2 or {}).get("tabs", [])}
        after_user = {t["tab_id"]: (t["url"], t["title"]) for t in (tabs2 or {}).get("tabs", []) if not t.get("owner")}
        ev.case("HARN-05", "our tab is gone", own_tab not in after_ids)
        ev.case("HARN-05", "user tabs (no owner session) are unchanged: same ids, urls and titles", after_user == before_user,
                f"before={len(before_user)} after={len(after_user)}")
        names = [n for n, _ in mcp.called]
        foreign = [(n, a.get("tab_id")) for n, a in mcp.called if "tab_id" in a and a.get("tab_id") != own_tab]
        ev.case("HARN-05", "every tool call that names a tab targeted our own tab (no foreign tab was read, selected or closed)", not foreign, f"foreign={foreign}")
        ev.case("HARN-05", "the global browser_close tool was never called", "browser_close" not in names, f"calls={len(names)}")
        ev.case("HARN-05", "browser_close_tab was called exactly once, for our own tab", [a.get("tab_id") for n, a in mcp.called if n == "browser_close_tab"] == [own_tab])
        meta = {"status": "done", "arise_version": arise_version(args.browser_mcp), "browser_mcp": args.browser_mcp, "tools_exposed": len(tools),
                "session": session, "python": sys.version.split()[0], "platform": sys.platform, "fixture_requests": len(fixture.log())}
        ev.finish(meta)
        print(f"{len(ev.cases)} checks, {ev.failures} failures; evidence {ev.path}")
        return 1 if ev.failures else 0
    except Exception as exc:  # environment trouble must not leave our tab behind
        ev.trace("exception", error=type(exc).__name__)
        print(f"ERROR: {type(exc).__name__}: {exc}")
        if mcp and own_tab is not None:
            try:
                mcp.call("browser_close_tab", {"session_id": session, "tab_id": own_tab})
                mcp.call("browser_release", {"session_id": session})
            except Exception:
                pass
        ev.finish({"status": "error", "error": type(exc).__name__})
        return 2
    finally:
        if mcp:
            mcp.close()
        if fixture:
            fixture.stop()


if __name__ == "__main__":
    sys.exit(main())
