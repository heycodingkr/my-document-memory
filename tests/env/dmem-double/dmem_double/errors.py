"""Fixed error codes, exit codes and messages (docs/spec/core.md section 7).

Messages are fixed per code and NEVER contain input values. The single exception is the deliberate
`echo_input` mutation (tests/README.md), used only to prove that the suite detects input echo.
"""
import os

EXIT_CODES = {
    "internal": 1,
    "invalid_input": 2, "non_canonical_url": 2, "url_rejected": 2, "invalid_form": 2, "secret_detected": 2,
    "payload_too_large": 2, "unsupported_format": 2, "extract_empty": 2, "fetch_blocked": 2,
    "auth_required": 3,
    "consent_required": 4, "scope_required": 4, "license_forbids": 4, "version_conflict": 4,
    "search_unavailable": 5, "fetch_failed": 5, "server_unavailable": 5,
    "rate_limited": 6,
    "not_found": 7,
}

HTTP_STATUS = {
    "invalid_input": 400, "non_canonical_url": 422, "url_rejected": 422, "invalid_form": 422, "secret_detected": 422,
    "payload_too_large": 413, "unsupported_format": 415, "extract_empty": 422, "fetch_blocked": 422,
    "auth_required": 401, "consent_required": 403, "scope_required": 403, "license_forbids": 403, "version_conflict": 409,
    "search_unavailable": 503, "fetch_failed": 502, "server_unavailable": 503, "rate_limited": 429,
    "not_found": 404, "internal": 500,
}

MESSAGES = {
    "invalid_input": "Invalid request.",
    "non_canonical_url": "URL is not a canonical pattern.",
    "url_rejected": "URL rejected.",
    "invalid_form": "Invalid form.",
    "secret_detected": "Secret-like content rejected.",
    "payload_too_large": "Payload too large.",
    "unsupported_format": "Unsupported format.",
    "extract_empty": "No text extracted.",
    "fetch_blocked": "Fetch blocked by policy.",
    "auth_required": "Authentication required.",
    "consent_required": "Consent required.",
    "scope_required": "Insufficient scope.",
    "license_forbids": "License does not allow this copy mode.",
    "version_conflict": "A newer version exists.",
    "search_unavailable": "Web search is unavailable.",
    "fetch_failed": "Remote site could not be fetched.",
    "server_unavailable": "Server unavailable.",
    "rate_limited": "Rate limited.",
    "not_found": "Resource not found.",
    "internal": "Internal error.",
}

# A few reasons carry a fixed, input-independent next step instead of the generic sentence (core.md section 7).
REASON_MESSAGES = {("fetch_blocked", "login_required"): "Login required. Download the file and import it with --file, or clip the current tab with the browser adapter."}

CODES = tuple(EXIT_CODES)
assert set(CODES) == set(MESSAGES) == set(HTTP_STATUS), "error tables out of sync"


class DmemError(Exception):
    """A contract error. `input_hint` is the offending input; it is kept ONLY so the echo_input mutation can leak it."""

    def __init__(self, code, reason=None, extra=None, input_hint=None, retry_after_seconds=None, trace_id=None):
        if code not in MESSAGES:
            raise ValueError("unknown error code")
        super().__init__(code)
        self.code = code
        self.reason = reason
        self.extra = dict(extra or {})
        self._input_hint = input_hint
        self.retry_after_seconds = retry_after_seconds
        self.trace_id = trace_id

    @property
    def exit_code(self):
        return EXIT_CODES[self.code]

    @property
    def http_status(self):
        return HTTP_STATUS[self.code]

    def error_object(self):
        message = REASON_MESSAGES.get((self.code, self.reason), MESSAGES[self.code])
        if os.environ.get("DMEM_DOUBLE_MUTATION") == "echo_input" and self._input_hint is not None:
            message = f"{message} input={self._input_hint}"  # deliberate defect for HARN-02
        obj = {"code": self.code, "message": message}
        if self.reason:
            obj["reason"] = self.reason
        if self.trace_id:
            obj["trace_id"] = self.trace_id
        if self.retry_after_seconds is not None:
            obj["retry_after_seconds"] = self.retry_after_seconds
        obj.update(self.extra)
        return obj

    def envelope(self):
        return {"schema_version": 1, "error": self.error_object()}


def envelope(err):
    return err.envelope()
