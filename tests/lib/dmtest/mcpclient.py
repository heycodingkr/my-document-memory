"""A stdio MCP client for black-box tests. Messages are newline-delimited JSON-RPC; any non-JSON line on stdout is counted as noise (MCP-06)."""
import json
import queue
import threading
import time

from .procs import Owned


class McpResult:
    def __init__(self, result):
        self.raw = result
        self.is_error = bool(result.get("isError"))
        content = result.get("content") or []
        self.text = content[0].get("text", "") if content else ""
        self.structured = result.get("structuredContent")
        try:
            self.json = json.loads(self.text)
        except ValueError:
            self.json = None

    @property
    def code(self):
        return ((self.structured or self.json or {}).get("error") or {}).get("code")


class McpSession:
    def __init__(self, cmd, env):
        self.proc = Owned(cmd if isinstance(cmd, list) else [cmd], env).start()
        self.messages = queue.Queue()
        self.noise_bytes = 0
        self.stderr_bytes = 0
        self._id = 0
        self.version = None
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    # -- reading
    def _read_stdout(self):
        for line in self.proc.p.stdout:
            text = line.decode("utf-8", "replace").strip()
            if not text:
                continue
            try:
                msg = json.loads(text)
                if not (isinstance(msg, dict) and msg.get("jsonrpc") == "2.0"):
                    raise ValueError
                self.messages.put(msg)
            except ValueError:
                self.noise_bytes += len(line)

    def _read_stderr(self):
        for line in self.proc.p.stderr:
            self.stderr_bytes += len(line)

    def read(self, timeout=15.0, ident=None):
        deadline = time.monotonic() + timeout
        stash = []
        try:
            while time.monotonic() < deadline:
                try:
                    msg = self.messages.get(timeout=max(0.05, min(0.5, deadline - time.monotonic())))
                except queue.Empty:
                    if self.proc.p.poll() is not None and self.messages.empty():
                        return None  # the server exited: nothing more will arrive
                    continue
                if ident is None or msg.get("id") == ident:
                    return msg
                stash.append(msg)
            return None
        finally:
            for m in stash:
                self.messages.put(m)

    # -- writing
    def send(self, obj):
        self.proc.p.stdin.write((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))
        self.proc.p.stdin.flush()

    def send_raw(self, data):
        self.proc.p.stdin.write(data)
        self.proc.p.stdin.flush()

    def rpc(self, method, params=None, timeout=20.0):
        self._id += 1
        ident = self._id
        self.send({"jsonrpc": "2.0", "id": ident, "method": method, "params": params or {}})
        return self.read(timeout, ident)

    def notify(self, method, params=None):
        self.send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    # -- MCP
    def initialize(self, version="2025-11-25"):
        reply = self.rpc("initialize", {"protocolVersion": version, "capabilities": {}, "clientInfo": {"name": "dmtest", "version": "1"}})
        if reply and "result" in reply:
            self.version = reply["result"].get("protocolVersion")
            self.notify("notifications/initialized")
        return reply

    def list_tools(self):
        reply = self.rpc("tools/list")
        return (reply or {}).get("result", {}).get("tools", [])

    def call(self, name, arguments=None, timeout=30.0):
        reply = self.rpc("tools/call", {"name": name, "arguments": arguments or {}}, timeout)
        if reply is None:
            return None
        if "error" in reply:
            return McpResult({"isError": True, "content": [{"type": "text", "text": json.dumps({"rpc_error": reply["error"]["code"]})}]})
        return McpResult(reply["result"])

    def ping(self, timeout=5.0):
        reply = self.rpc("ping", timeout=timeout)
        return reply is not None and "result" in reply

    def close(self):
        self.proc.stop()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
