"""Run the CLI under test as a black box."""
import json

from .procs import run_with_timeout


class Result:
    def __init__(self, exit_code, stdout, stderr, seconds):
        self.exit = exit_code  # None means the harness killed it after the timeout
        self.stdout = stdout.decode("utf-8", "replace") if isinstance(stdout, bytes) else stdout
        self.stderr = stderr.decode("utf-8", "replace") if isinstance(stderr, bytes) else stderr
        self.seconds = seconds
        self.timed_out = exit_code is None
        self.json = None
        text = self.stdout.strip()
        if text:
            try:
                parsed = json.loads(text)
                self.json = parsed if isinstance(parsed, (dict, list)) else None
            except ValueError:
                self.json = None

    @property
    def error(self):
        return (self.json or {}).get("error") if isinstance(self.json, dict) else None

    @property
    def code(self):
        """The fixed error code of a failed --json call, else None."""
        return (self.error or {}).get("code")

    def __repr__(self):  # never print output: it may contain the very sentinels the case is looking for
        return f"Result(exit={self.exit}, stdout={len(self.stdout)}B, stderr={len(self.stderr)}B)"


class Cli:
    def __init__(self, argv0, env, cwd=None):
        self.argv0 = [argv0] if isinstance(argv0, str) else list(argv0)
        self.env, self.cwd = env, cwd
        self.calls = []  # (args, exit) of every call, for argv sink scans

    def run(self, args, stdin=None, timeout=30.0, env=None):
        data = stdin.encode("utf-8") if isinstance(stdin, str) else stdin
        merged = dict(self.env, **(env or {}))
        code, out, err, secs = run_with_timeout(self.argv0 + list(args), merged, stdin=data, timeout=timeout, cwd=self.cwd)
        self.calls.append((list(args), code))
        return Result(code, out, err, secs)

    def json(self, args, stdin=None, timeout=30.0, env=None):
        """Run with --json and return the Result (check .exit / .json / .code)."""
        return self.run(list(args) + ["--json"], stdin=stdin, timeout=timeout, env=env)
