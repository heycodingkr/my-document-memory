"""Persistent state of the test double: a JSON snapshot guarded by an exclusive flock and replaced atomically.

Two stores exist: the local store ($DMEM_HOME/state.json, the user's own library) and, in server mode, one shared
server store ($DMEM_TEST_SERVER_STATE) holding every linked identity's library. Files are 0600, directories 0700,
symlinked store paths are refused, and a corrupt file surfaces as the fixed `internal` error (LIB-13).
"""
import contextlib
import fcntl
import hashlib
import json
import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path

from .errors import DmemError


def now():
    return time.time() + float(os.environ.get("DMEM_TEST_CLOCK_OFFSET", "0") or 0)


def iso(ts=None):
    return datetime.fromtimestamp(now() if ts is None else ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(text):
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def sha256_hex(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode("utf-8")).hexdigest()


def new_id(prefix):
    return f"{prefix}_{secrets.token_hex(4)}"


def default_state():
    return {"schema": 1, "memories": {}, "workspaces": {}, "receipts": {}, "outcomes": {}, "consents": [],
            "takedowns": {"hashes": [], "memory_ids": []}, "publish_log": {}, "reviews": {}}


class Store:
    def __init__(self, path, library_key_dir=None):
        self.path = Path(path)
        self.lock_path = Path(str(path) + ".lock")

    def _guard(self):
        parent = self.path.parent
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.path.islink(self.path) or os.path.islink(self.lock_path):
            raise DmemError("internal")  # never follow a symlink out of the data directory

    def exists(self):
        return self.path.exists() and not os.path.islink(self.path)

    def _read(self):
        if not self.path.exists():
            return default_state()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or "memories" not in data:
                raise ValueError("shape")
            return data
        except (ValueError, OSError):
            raise DmemError("internal")

    def read(self):
        """Read-only snapshot (shared lock)."""
        if not self.path.exists():
            return default_state()
        self._guard()
        with open(self.lock_path, "a") as lock:
            fcntl.flock(lock, fcntl.LOCK_SH)
            try:
                return self._read()
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    @contextlib.contextmanager
    def txn(self):
        """Exclusive read-modify-write. The state is saved only when the block exits without an exception."""
        self._guard()
        fd = os.open(self.lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        with os.fdopen(fd, "a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                state = self._read()
                yield state
                tmp = self.path.with_name(self.path.name + f".tmp{os.getpid()}")
                with open(os.open(tmp, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600), "w", encoding="utf-8") as handle:
                    json.dump(state, handle, ensure_ascii=False)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(tmp, self.path)
                os.chmod(self.path, 0o600)
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)


def library_key(home):
    """32 random bytes created on first use, readable only by the owner (core.md section 4)."""
    path = Path(home) / "library.key"
    Path(home).mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.path.islink(path):
        raise DmemError("internal")
    if not path.exists():
        fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(secrets.token_bytes(32))
    return path.read_bytes()


def save_original(home, data):
    """Preserve an uploaded file at originals/<sha256> (0600). Returns the sha256 hex."""
    digest = sha256_hex(data)
    folder = Path(home) / "originals"
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = folder / digest
    if os.path.islink(target):
        raise DmemError("internal")
    if not target.exists():
        fd = os.open(target, os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
    return digest


def delete_original_if_unreferenced(home, digest, referenced):
    target = Path(home) / "originals" / digest
    if digest not in referenced and target.exists() and not os.path.islink(target):
        target.unlink()


def request_log(op, write, body_keys):
    """Append one record per REMOTE operation (server mode only) for the zero-request / minimal-transmission checks."""
    path = os.environ.get("DMEM_TEST_REQUEST_LOG")
    if not path:
        return
    line = json.dumps({"ts": iso(), "op": op, "write": bool(write), "body_keys": sorted(body_keys)}, ensure_ascii=False)
    fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")
