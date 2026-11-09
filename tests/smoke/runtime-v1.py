#!/usr/bin/env python3
"""Exercise built binaries against a private temporary DB. Optional real-browser QA."""
import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "target/debug"
parser = argparse.ArgumentParser()
parser.add_argument("--browser", action="store_true")
parser.add_argument("--browser-spec", action="append", default=[], metavar="PATH",
                    help="Select a browser spec; repeat to run several. Defaults to all specs.")
args = parser.parse_args()
for name in ["dmem-server", "dmem", "dmem-mcp"]:
    if not (BIN / name).is_file():
        raise SystemExit("Run cargo build --workspace first.")
if args.browser and not (ROOT / "web/dist/index.html").is_file():
    raise SystemExit("Run pnpm --dir web build first.")

with tempfile.TemporaryDirectory(prefix="dmem-smoke-") as tmp:
    tmp = Path(tmp)
    token = secrets.token_urlsafe(32)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    env = {**os.environ, "DMEM_TOKEN": token, "DMEM_ADDR": f"127.0.0.1:{port}",
           "DMEM_URL": base, "DMEM_DATABASE": str(tmp / "library.sqlite3"),
           "DMEM_WEB_DIR": str(ROOT / "web/dist")}
    log = (tmp / "server.log").open("w")
    process = None

    def request(path, method="GET", data=None, authenticated=True):
        raw = None if data is None else json.dumps(data, ensure_ascii=False).encode()
        headers = {"Content-Type": "application/json"}
        if authenticated:
            headers["Authorization"] = "Bearer " + token
        req = urllib.request.Request(base + path, data=raw, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.read()

    def start():
        global process
        process = subprocess.Popen([str(BIN / "dmem-server")], cwd=ROOT, env=env,
                                   stdout=log, stderr=log)
        for _ in range(100):
            if process.poll() is not None:
                raise AssertionError("server exited before readiness")
            try:
                if request("/healthz", authenticated=False)[0] == 200:
                    return
            except OSError:
                pass
            time.sleep(.05)
        raise AssertionError("server readiness timeout")

    def stop():
        if process and process.poll() is None:
            process.terminate()
            process.wait(timeout=5)

    def cli(*arguments):
        result = subprocess.run([str(BIN / "dmem"), *arguments], env=env, cwd=ROOT,
                                text=True, capture_output=True, timeout=20)
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    try:
        start()
        assert request("/v1/templates", authenticated=False)[0] == 401
        assert cli("status")["service"] == "my-document-memory"
        starters = json.loads((ROOT / "contracts/starter-memories.v1.json").read_text())["entries"]
        assert len(cli("templates")["items"]) == min(20, 18 + len(starters))
        english = json.loads(request("/v1/templates?locale=en-US")[1])["items"]
        assert len(english) == min(20, 9 + sum(entry["locale"] == "en-US" for entry in starters))
        assert all(item["form"]["locale"] == "en-US" for item in english)
        fixture = tmp / "facts.md"
        fixture.write_text("# Project decisions\nThe beta review is on 15 November.\nSynthetic test data only.", encoding="utf-8")
        source = cli("import", str(fixture), "--title", "Synthetic Notes")
        assert request(f"/v1/sources/{source['id']}/file")[1] == fixture.read_bytes()
        copied = cli("copy", "meeting.minutes.en")
        assert copied["visibility"] == "private"
        assert copied["origin"]["license"] == "CC0-1.0"
        document = cli("create", copied["id"], "--title", "Integration Demo", "--source", source["id"])
        assert document["source_versions"][0]["source_id"] == source["id"]
        assert any("beta review" in b.get("text", "") for b in document["content"]["blocks"])
        saved = {"base_version": 1, "title": "Integration Demo v2", "content": document["content"]}
        endpoint = f"/v1/documents/{document['id']}"
        assert request(endpoint, "PUT", saved)[0] == 200
        assert request(endpoint, "PUT", saved)[0] == 409
        assert cli("show", document["id"])["version"] == 2

        output = tmp / "export.docx"
        assert cli("export", document["id"], "--format", "docx", "--output", str(output))["exported"]
        original = output.read_bytes()
        attempt = subprocess.run([str(BIN / "dmem"), "export", document["id"], "--format", "docx",
                                  "--output", str(output)], env=env, text=True, capture_output=True)
        assert attempt.returncode != 0 and output.read_bytes() == original
        with zipfile.ZipFile(output) as archive:
            for name in archive.namelist():
                if name.endswith((".xml", ".rels")):
                    ET.fromstring(archive.read(name))

        messages = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "document_source_search", "arguments": {"query": "beta"}}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "document_memory_get", "arguments": {"id": document["id"]}}},
            {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "missing", "arguments": {}}},
        ]
        lines = "\n".join(json.dumps(v, ensure_ascii=False) for v in messages) + "\n{invalid\n"
        mcp = subprocess.run([str(BIN / "dmem-mcp")], env=env, input=lines,
                             text=True, capture_output=True, timeout=20)
        assert mcp.returncode == 0 and not mcp.stderr
        replies = [json.loads(line) for line in mcp.stdout.splitlines()]
        assert len(replies) == 6
        names = {tool["name"] for tool in replies[1]["result"]["tools"]}
        assert {"document_memory_status", "document_memory_get", "document_template_save",
                "document_memory_save", "document_public_template_search",
                "document_contribution_submit", "document_contribution_check"} <= names
        source_hits = json.loads(replies[2]["result"]["content"][0]["text"])
        assert source_hits["items"][0]["id"] == source["id"]
        assert json.loads(replies[3]["result"]["content"][0]["text"])["version"] == 2
        assert replies[4]["result"]["isError"] is True
        assert replies[5]["error"]["code"] == -32700
        assert token not in mcp.stdout

        stop()
        start()
        assert json.loads(request(endpoint)[1])["version"] == 2
        history = json.loads(request(endpoint + "/revisions")[1])["items"]
        assert [v["version"] for v in history] == [2, 1]
        print("PASS: HTTP auth, CLI import/copy/create/export, MCP transport, conflicts, immutable history and restart persistence")
        if args.browser:
            browser_env = {**env, "DMEM_E2E_URL": base, "DMEM_E2E_TOKEN": token}
            subprocess.run(["pnpm", "test:e2e", *args.browser_spec], cwd=ROOT / "web", env=browser_env,
                           check=True, timeout=120)
    finally:
        stop()
        log.close()
