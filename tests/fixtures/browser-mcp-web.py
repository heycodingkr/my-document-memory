"""Synthetic connection-local browser for WI-19/21/22; never a real browser."""
import json
import os
import sys
import time

client = ""
session = ""
mode = "normal"
url = os.environ.get("DMEM_FAKE_BROWSER_URL", "https://example.com/document")
html = '<title>Synthetic clip</title><link rel="license" href="https://creativecommons.org/licenses/by/4.0/"><h2>Fixture scope</h2><p>VISIBLE_CLIP_BODY</p>'
names = ["browser_tabs", "browser_eval", "browser_new_tab", "browser_close_tab", "browser_release", "browser_test_mode"]
for line in sys.stdin:
    msg = json.loads(line)
    if "id" not in msg:
        continue
    method = msg.get("method")
    if method == "initialize":
        client = msg["params"]["clientInfo"]["name"]
        result = {"protocolVersion": "2025-11-25", "capabilities": {"tools": {}}, "serverInfo": {"name": "synthetic-browser", "version": "1"}}
    elif method == "tools/list":
        result = {"tools": [{"name": n, "description": "Synthetic browser test hook", "inputSchema": {"type": "object"}} for n in names]}
    elif method == "tools/call":
        name = msg["params"]["name"]
        args = msg["params"].get("arguments", {})
        if name == "browser_new_tab":
            session = args["session_id"]
            url = args.get("url", url)
            value = {"tab_id": 7, "window_id": 3}
        elif name == "browser_test_mode":
            mode = args["mode"]
            value = {"mode": mode, "pid": os.getpid()}
        elif name == "browser_tabs":
            owner = {"session_id": session, "client_name": client, "is_mine": mode != "foreign", "tab_id": 7, "window_id": 3, "expires_at_ms": 1 if mode == "expired" else int(time.time() * 1000) + 120000}
            tab = {"tab_id": 7, "window_id": 3, "ready": True, "is_automation_target": True, "is_mine": mode != "foreign", "has_local_lease": mode != "no_lease", "url": url, "owner": owner}
            value = {"ok": True, "session_id": args["session_id"], "automation_target_tab": 7, "tabs": [tab]}
        elif name == "browser_eval":
            if mode == "eval_error":
                result = {"isError": True, "content": [{"type": "text", "text": "private lease unavailable"}]}
                print(json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": result}), flush=True)
                continue
            value = {"result": json.dumps({"url": url, "html": html, "blocked": mode == "sensitive"})}
            if mode == "changed":
                url += "/changed"
        else:
            value = {"ok": True}
        result = {"content": [{"type": "text", "text": json.dumps(value)}], "isError": False}
    else:
        result = {}
    print(json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": result}), flush=True)
