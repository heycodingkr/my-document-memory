#!/usr/bin/env python3
"""Real CLI/MCP/community smoke against an owned temporary synthetic fixture."""
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "target/debug"
ALICE = "automated-smoke-token-not-production"
BOB = "automated-bob-token-not-production"
ADMIN = "synthetic-e2e-admin-token-at-least-32-characters"

def run():
    with tempfile.TemporaryDirectory(prefix="mdm-community-") as directory:
        tmp = Path(directory)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        env = {k: v for k, v in os.environ.items() if k not in ("DMEM_TOKEN", "DMEM_ADMIN_TOKEN", "DMEM_ORIGIN")}
        env.update(DMEM_URL=base, DMEM_E2E_ADDR=f"127.0.0.1:{port}",
                   DMEM_E2E_DATABASE=str(tmp / "library.sqlite3"),
                   DMEM_E2E_WEB_DIR=str(ROOT / "web/dist"), DMEM_E2E_MAILBOX=str(tmp / "mailbox.json"))
        def http(path, token="", method="GET", body=None):
            headers = {"Origin": base, "Content-Type": "application/json"}
            if token: headers["Authorization"] = "Bearer " + token
            data = None if body is None else json.dumps(body).encode()
            request = urllib.request.Request(base + path, data=data, method=method, headers=headers)
            try:
                with urllib.request.urlopen(request, timeout=5) as response:
                    return response.status, json.load(response)
            except urllib.error.HTTPError as error:
                return error.code, json.load(error)
        def cli(*args, token=ALICE, expected=0, admin=False):
            local = dict(env)
            if token: local["DMEM_TOKEN"] = token
            if admin: local["DMEM_ADMIN_TOKEN"] = ADMIN
            result = subprocess.run([str(BIN / "dmem"), *args], env=local, text=True, capture_output=True, timeout=20)
            assert result.returncode == expected, (args, result.returncode, result.stderr)
            assert ALICE not in result.stdout and ADMIN not in result.stdout
            return json.loads(result.stdout) if result.stdout else result.stderr
        def mcp(name, args=None, token=ALICE, error=None):
            local = dict(env)
            if token: local["DMEM_TOKEN"] = token
            messages = [
                {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25"}},
                {"jsonrpc":"2.0","method":"notifications/initialized"},
                {"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":name,"arguments":args or {}}}
            ]
            result = subprocess.run([str(BIN / "dmem-mcp")], env=local,
                input="".join(json.dumps(m)+"\n" for m in messages), text=True, capture_output=True, timeout=20)
            assert result.returncode == 0, result.stderr
            replies = [json.loads(line) for line in result.stdout.splitlines()]
            assert len(replies) == 2 and not result.stderr, replies
            reply = replies[1]["result"]
            data = json.loads(reply["content"][0]["text"])
            assert reply["isError"] == bool(error), data
            if error: assert data["code"] == error, data
            assert ALICE not in result.stdout and ADMIN not in result.stdout
            return data
        def fixture(name, body):
            path = tmp / name
            path.write_text(json.dumps(body), encoding="utf8")
            return str(path)
        log = (tmp / "server.log").open("w")
        process = subprocess.Popen([str(BIN / "examples/accounts_fixture")], env=env, cwd=ROOT, stdout=log, stderr=log)
        try:
            for _ in range(100):
                assert process.poll() is None, "fixture exited"
                try:
                    if http("/healthz")[0] == 200: break
                except OSError: pass
                time.sleep(.05)
            else: raise AssertionError("fixture not ready")
            inputs = {"title":"Synthetic community planning","summary":"Reusable synthetic structure",
                      "form":{"provider":"docx","doc_type":"report","locale":"en-US"},
                      "sections":["Novel scope assumptions","Independent verification","Decision rationale"],"tags":[]}
            a = cli("template-save", fixture("template.json", inputs))
            assert a["visibility"] == "private" and a["version"] == 1
            assert mcp("document_template_get", {"id":a["id"]}) == a
            inputs["title"] = "MCP saved private template"
            b = mcp("document_template_save", inputs)
            assert cli("template-show", b["id"]) == b
            mcp("document_template_get", {"id":a["id"]}, token=BOB, error="not_found")
            assert not any(t["id"] == a["id"] for t in http("/v1/templates", BOB)[1]["items"])
            print("PASS MC-01/02: CLI ↔ MCP private save/read and cross-owner denial")
            document = cli("create", a["id"], "--title", "Synthetic saved document")
            content = document["content"]
            content["blocks"].append({"type":"paragraph","text":"Synthetic revision two"})
            revision = mcp("document_memory_save", {"id":document["id"],"base_version":1,
                "title":"Edited via MCP","content":content})
            assert revision["version"] == 2 and cli("show", document["id"]) == revision
            mcp("document_memory_save", {"id":document["id"],"base_version":1,
                "title":"Stale edit","content":content}, error="version_conflict")
            content["blocks"].append({"type":"paragraph","text":"Synthetic CLI revision three"})
            third = cli("save", document["id"], fixture("revision.json",
                {"base_version":2,"title":"Edited via CLI","content":content}))
            assert third["version"] == 3
            history = http("/v1/documents/"+document["id"]+"/revisions", ALICE)[1]["items"]
            assert [x["version"] for x in history] == [3,2,1]
            assert not any(x.get("text") == "Synthetic revision two" for x in history[-1]["content"]["blocks"])
            print("PASS MC-03: private document save, immutable revisions and conflict")
            public = cli("public-templates", "Meeting", token="")
            assert public["items"]
            seed = public["items"][0]
            assert cli("public-template", seed["id"], token="") == mcp("document_public_template_get", {"id":seed["id"]}, token="")
            assert mcp("document_public_template_search", {"query":"Meeting"}, token="") == public
            mcp("document_template_get", {"id":a["id"]}, token="", error="auth_required")
            mcp("document_template_save", inputs, token="", error="auth_required")
            print("PASS MC-04: anonymous CLI/MCP public reads and private auth boundary")
            cli("contribute", a["id"], "--author", "Synthetic author", "--license", "CC-BY-4.0", expected=2)
            contribution = cli("contribute", a["id"], "--author", "Synthetic author", "--license", "CC-BY-4.0", "--rights-confirmed")
            cid = contribution["id"]
            pid = contribution["snapshot"]["id"]
            assert contribution["status"] == "pending" and http("/v1/public/templates/"+pid)[0] == 404
            assert any(x["id"] == cid for x in mcp("document_contribution_list")["items"])
            mcp("document_contribution_withdraw", {"id":cid}, token=BOB, error="not_found")
            assert http("/v1/admin/contributions", ALICE)[0] == 401
            assert http("/v1/admin/contributions/"+cid+"/review", ALICE)[0] == 401
            report = cli("review", cid, token="", admin=True)
            assert report["verdict"] == "ready" and [s["rule"] for s in report["stages"]] == ["R0","R1","R2","R3","R4","R5"]
            assert mcp("document_contribution_check", {"id":cid}) == report
            assert any(x["id"] == cid for x in cli("review-queue", token="", admin=True)["items"])
            approved = cli("decide", cid, "--decision", "approve", token="", admin=True)
            assert approved["status"] == "approved" and approved["review"]["decision"] == "approve"
            assert cli("public-template", pid, token="")["author"] == "Synthetic author"
            copy = cli("copy", pid, token=BOB)
            assert copy["visibility"] == "private" and copy["origin"]["template_id"] == pid
            assert copy["origin"]["license"] == "CC-BY-4.0"
            cli("decide", cid, "--decision", "approve", token="", admin=True, expected=1)
            print("PASS MC-05/07/08: explicit contribution, snapshot review, approval and attributed copy")
            # A copied/re-contributed structure is a human-review advisory, preserving existing derivative semantics.
            duplicate = mcp("document_contribution_submit", {"template_id":copy["id"],
                "author":"Synthetic second contributor","license":"CC-BY-4.0","rights_confirmed":True}, token=BOB)
            duplicate_report = cli("review", duplicate["id"], token="", admin=True)
            assert duplicate_report["verdict"] == "needs_review"
            assert any(x["code"] == "exact_duplicate" for x in duplicate_report["findings"])
            assert http("/v1/public/templates/"+duplicate["snapshot"]["id"])[0] == 404
            rejected = cli("decide", duplicate["id"], "--decision", "reject", token="", admin=True)
            assert rejected["status"] == "rejected"
            print("PASS MC-06/10: MCP contribution and duplicate advisory with explicit rejection")
            unsafe_inputs = dict(inputs, title="Unsafe synthetic structure", summary="synthetic-person@example.test")
            unsafe = mcp("document_template_save", unsafe_inputs)
            pending = mcp("document_contribution_submit", {"template_id":unsafe["id"],
                "author":"Synthetic author","license":"CC0-1.0","rights_confirmed":True})
            blocked = cli("review", pending["id"], token="", admin=True)
            assert blocked["verdict"] == "blocked" and "synthetic-person@example.test" not in json.dumps(blocked)
            assert "review_blocked" in cli("decide", pending["id"], "--decision", "approve", token="", admin=True, expected=1)
            assert http("/v1/public/templates/"+pending["snapshot"]["id"])[0] == 404
            mcp("document_contribution_withdraw", {"id":pending["id"]})
            withdrawn = cli("withdraw", cid)
            assert withdrawn["status"] == "withdrawn" and http("/v1/public/templates/"+pid)[0] == 404
            assert cli("template-show", copy["id"], token=BOB)["origin"]["author"] == "Synthetic author"
            assert http("/v1/templates/"+pid+"/copy", BOB, "POST", {})[0] == 404
            with sqlite3.connect(tmp / "library.sqlite3") as db:
                assert db.execute("SELECT owner FROM records WHERE id=?", (a["id"],)).fetchone()[0] == "local"
                assert db.execute("SELECT count(*) FROM contribution_reviews").fetchone()[0] == 2
            print("PASS MC-09/11: unsafe approval blocked; decision audit, withdrawal and existing copy preserved")
            mcp("document_template_get", {"id":"../private"}, error="invalid_input")
            for invalid_id in (".", ".."):
                mcp("document_template_get", {"id":invalid_id}, error="invalid_input")
                assert "invalid_input" in cli("template-show", invalid_id, expected=1)
            mcp("document_public_template_search", {"unexpected":True}, token="", error="invalid_input")
            print("PASS: community CLI/MCP smoke complete")
        finally:
            process.terminate()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            log.close()

if __name__ == "__main__":
    run()
