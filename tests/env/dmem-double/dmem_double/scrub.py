import json
import re
import unicodedata

_SECRET = [
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{16,}", re.I),
    re.compile(r"(?<![A-Za-z0-9])AKIA[A-Z0-9]{16}(?![A-Z0-9])"),
    re.compile(r"(?<![A-Za-z0-9])ghp_[A-Za-z0-9]{36}(?![A-Za-z0-9])"),
    re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.I),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
]
_EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w.-])")
_PHONE = re.compile(r"(?<!\w)(?:\+1\s*\(\d{3}\)\s*\d{3}-\d{4}|(?:010|090)-\d{4}-\d{4})(?!\w)")
_NATIONAL = re.compile(r"(?<!\d)(?:\d{6}-\d{7}|\d{3}-\d{2}-\d{4})(?!\d)")
_IBAN = re.compile(r"(?<![A-Za-z0-9])[A-Z]{2}\d{2}(?:\s?[A-Z0-9]){11,30}(?![A-Za-z0-9])", re.I)
_CARD = re.compile(r"(?<![A-Za-z0-9])(?:\d ?){12,18}\d(?![A-Za-z0-9])")
_ZERO = set("\u200b\u200c\u200d\u2060\ufeff")
_BIDI = set("\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")


def has_secret(text):
    return any(pattern.search(str(text)) for pattern in _SECRET)


def mask_secrets(text):
    """Used ONLY by the partial_secret_save mutation: a masked copy of a secret-bearing text (the contract says such input is rejected, never masked)."""
    out = str(text)
    for pattern in _SECRET:
        out = pattern.sub("[REDACTED]", out)
    return out


def _luhn(value):
    digits = [int(c) for c in value if c.isdigit()]
    total = 0
    for index, digit in enumerate(reversed(digits)):
        if index % 2:
            digit = digit * 2 - (9 if digit > 4 else 0)
        total += digit
    return len(digits) in range(13, 20) and total % 10 == 0


def slotify_pii(text):
    result, slots, count = str(text), set(), 0
    def replace(pattern, slot, predicate=None):
        nonlocal result, count
        def sub(match):
            nonlocal count
            if predicate and not predicate(match.group()):
                return match.group()
            count += 1
            slots.add(slot)
            return "{{" + slot + "}}"
        result = pattern.sub(sub, result)
    replace(_EMAIL, "email")
    replace(_PHONE, "phone")
    replace(_NATIONAL, "national_id")
    replace(_IBAN, "account_number")
    replace(_CARD, "card_number", lambda value: _luhn(value))
    return result, count, sorted(slots)


def l1_problems(text):
    text = str(text)
    problems = set()
    if re.search(r"(?:https?://|www\.)\S+", text, re.I):
        problems.add("url")
    if _EMAIL.search(text):
        problems.add("email")
    if any(unicodedata.category(c) == "Cc" and c not in "\n\r\t" for c in text):
        problems.add("control_char")
    if any(c in _ZERO for c in text):
        problems.add("zero_width")
    if any(c in _BIDI for c in text):
        problems.add("bidi")
    return sorted(problems)


def injection_flag(text):
    phrases = (
        r"ignore\s+(?:all\s+|any\s+|the\s+)*(?:previous|prior|above|earlier)\s+(?:instructions|directions|prompts)",
        r"disregard\s+(?:all\s+|any\s+|the\s+)*(?:previous|prior|above)\s+(?:instructions|rules)",
        r"이전\s*지시[를을]?\s*무시",
        r"send\s+(?:the\s+)?document\s+to\s+https?://", r"외부로\s*전송",
        r"run\s+the\s+following\s+command", r"비밀번호를\s*입력",
    )
    return any(re.search(phrase, str(text), re.I) for phrase in phrases)


def strip_hidden(text):
    cleaned = "".join(c for c in str(text) if c not in _ZERO and c not in _BIDI)
    return cleaned, len(str(text)) - len(cleaned)


def est_tokens(obj):
    encoded = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return (len(encoded) + 3) // 4
