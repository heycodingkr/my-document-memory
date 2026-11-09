"""HARN-05 / HARN-15: isolated environments, owned process groups, hang handling."""
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dmtest.procs import Owned, free_port, isolated_env, leftover_check, run_with_timeout, short_tmp


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


class ProcsTests(unittest.TestCase):
    def test_isolated_env_is_disposable_and_inherits_nothing_private(self):
        with tempfile.TemporaryDirectory() as d:
            before = dict(os.environ)
            os.environ["SECRET_SHOULD_NOT_LEAK"] = "1"
            try:
                env = isolated_env(d, DMEM_HOME=str(Path(d) / "dmem"))
            finally:
                os.environ.clear()
                os.environ.update(before)
            self.assertNotIn("SECRET_SHOULD_NOT_LEAK", env)
            for key in ("HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "TMPDIR"):
                self.assertTrue(env[key].startswith(d), f"{key} must live in the disposable directory")
            self.assertNotEqual(env["HOME"], os.path.expanduser("~"))
            self.assertEqual(env["DMEM_TELEMETRY"], "off")

    def test_stop_kills_the_whole_process_group(self):
        child = Owned(["sh", "-c", "sleep 60 & echo $! ; wait"], dict(os.environ)).start()
        grandchild = int(child.p.stdout.readline().decode().strip())
        self.assertTrue(alive(grandchild))
        child.stop(timeout=1.0)
        time.sleep(0.3)
        self.assertFalse(alive(child.p.pid), "the child must be gone")
        self.assertFalse(alive(grandchild), "its descendants must be gone too (own process group)")

    def test_a_hung_child_is_killed_at_the_deadline(self):
        started = time.monotonic()
        code, out, err, seconds = run_with_timeout(["sh", "-c", "sleep 30"], dict(os.environ), timeout=1.0)
        self.assertIsNone(code, "a timeout is reported as exit None")
        self.assertLess(time.monotonic() - started, 6.0, "the harness must not wait for the hung child")

    def test_a_normal_child_reports_exit_stdout_and_stderr(self):
        code, out, err, _ = run_with_timeout(["sh", "-c", "echo out; echo err >&2; exit 3"], dict(os.environ), timeout=5.0)
        self.assertEqual((code, out.strip(), err.strip()), (3, b"out", b"err"))

    def test_stdin_is_delivered(self):
        code, out, _, _ = run_with_timeout(["cat"], dict(os.environ), stdin=b"hello", timeout=5.0)
        self.assertEqual((code, out), (0, b"hello"))

    def test_leftover_check_and_free_port_and_short_tmp(self):
        self.assertEqual(leftover_check([1, 2], [1, 2, 9]), [9])
        self.assertEqual(leftover_check([1], [1]), [])
        port = free_port()
        self.assertTrue(1024 < port < 65536)
        tmp = short_tmp()
        try:
            self.assertLess(len(str(tmp)), 40, "unix socket paths on macOS are length limited")
        finally:
            tmp.rmdir()


if __name__ == "__main__":
    unittest.main()
