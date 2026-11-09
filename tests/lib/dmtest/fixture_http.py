"""Owned-process client for the loopback fixture HTTP server."""
import json
import os
import select
import signal
import subprocess
import sys
import urllib.request
from pathlib import Path


class FixtureServer:
    def __init__(self, log_dir):
        self.log_dir = Path(log_dir).resolve()
        self.process = None
        self.base_url = None
        self.script = Path(__file__).resolve().parents[2] / "env" / "fixture-sites" / "fixture_server.py"

    def start(self):
        if self.process is not None and self.process.poll() is None:
            return self.base_url
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.process = subprocess.Popen(
            [sys.executable, "-B", str(self.script), "--log-dir", str(self.log_dir), "--port", "0"],
            cwd=str(self.script.parents[3]), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1,
            start_new_session=True,
        )
        ready, _, _ = select.select([self.process.stdout], [], [], 10)
        if not ready:
            self.stop()
            raise RuntimeError("fixture server did not announce its address")
        line = self.process.stdout.readline()
        try:
            self.base_url = json.loads(line)["base_url"]
        except (ValueError, KeyError, TypeError):
            detail = line.strip()[:200]
            self.stop()
            raise RuntimeError("fixture server returned an invalid startup line: " + detail)
        return self.base_url

    def stop(self):
        proc = self.process
        if proc is None:
            return
        try:
            if proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait(timeout=3)
            else:
                proc.wait()
        finally:
            if proc.stdout:
                proc.stdout.close()
            self.process = None

    def log(self):
        path = self.log_dir / "requests.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

    def reset(self):
        if not self.base_url or self.process is None or self.process.poll() is not None:
            raise RuntimeError("fixture server is not running")
        request = urllib.request.Request(self.base_url + "/__reset", data=b"", method="POST")
        with urllib.request.urlopen(request, timeout=3) as response:
            response.read()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_exc):
        self.stop()
        return False
