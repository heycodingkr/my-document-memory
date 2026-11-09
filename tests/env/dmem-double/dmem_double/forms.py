import re
from . import vocab
from .errors import DmemError


def _fail(reason, value):
    raise DmemError("invalid_form", reason=reason, input_hint=value)


def _locale(value):
    if not isinstance(value, str) or not value: return None
    parts = value.replace("_", "-").split("-")
    if len(parts) not in (1, 2) or not parts[0].isalpha(): return None
    lang = parts[0].lower()
    candidate = lang if len(parts) == 1 else lang + "-" + parts[1].upper()
    locales = vocab.locales()
    if candidate in locales: return candidate
    if len(parts) == 1 and any(x.startswith(lang + "-") for x in locales): return lang
    return None


def normalize_form(raw: dict, for_save=False) -> dict:
    raw = raw if isinstance(raw, dict) else {}
    provider = raw.get("provider", "other" if not for_save else None)
    if provider not in vocab.provider_ids(): _fail("provider_unknown", provider)
    value = raw.get("doc_type")
    found = vocab.doc_type_lookup(value) if value is not None else None
    if value is not None and found is None: _fail("doc_type_unknown", value)
    if for_save and found is None: _fail("doc_type_unknown", value)
    doc, implied = found if found else (None, None)
    value = raw.get("locale")
    locale = _locale(value) if value is not None else None
    if value is not None and locale is None: _fail("locale_unknown", value)
    if for_save and locale is None: _fail("locale_unknown", value)
    value = raw.get("region")
    region = str(value).upper() if value is not None else (
        locale.split("-", 1)[1] if locale and "-" in locale else None)
    if region is not None and region not in vocab.regions(): _fail("locale_unknown", value)
    value = raw.get("variant")
    variant = value if value is not None else implied
    if variant is not None and (not isinstance(variant, str) or
            re.fullmatch(r"[a-z0-9_]{1,32}", variant) is None): _fail("variant_invalid", variant)
    family = vocab.provider_family(provider)
    doc_family = vocab.doc_type_family(doc) if doc else None
    if doc_family is not None and doc_family != family: _fail("family_mismatch", raw.get("doc_type"))
    page = raw.get("page")
    if page is not None:
        sizes = {"A4", "A3", "A5", "Letter", "Legal", "16:9", "4:3", "custom"}
        valid = isinstance(page, dict) and page.get("size") in sizes and page.get("orientation") in {"portrait", "landscape"}
        margins = page.get("margins_mm") if isinstance(page, dict) else None
        if margins is not None:
            valid = valid and isinstance(margins, (list, tuple)) and len(margins) == 4 and all(
                isinstance(n, int) and not isinstance(n, bool) and 0 <= n <= 100 for n in margins)
        size = page.get("size") if isinstance(page, dict) else None
        if not valid or (family == "deck" and size not in {"16:9", "4:3", "custom"}) or (
                family == "document" and size in {"16:9", "4:3"}): _fail("page_invalid", page)
    return dict(provider=provider, family=family, doc_type=doc, locale=locale, region=region,
                variant=variant, page=page)


def locale_match(memory_locale, query_locale):
    if query_locale is None: return "unspecified"
    memory, query = _locale(memory_locale), _locale(query_locale)
    if memory is None or query is None: return "none"
    ml, mr = memory.split("-", 1) if "-" in memory else (memory, None)
    ql, qr = query.split("-", 1) if "-" in query else (query, None)
    if ml != ql: return "none"
    return "exact" if mr is not None and mr == qr else "language"


def convention_warnings(memory_form, query_locale, query_provider):
    memory_form = memory_form or {}
    ml = _locale(memory_form.get("locale"))
    ql = _locale(query_locale) if query_locale is not None else None
    mr = memory_form.get("region") or (ml.split("-", 1)[1] if ml and "-" in ml else None)
    qr = ql.split("-", 1)[1] if ql and "-" in ql else None
    mp, qp, out = vocab.region_profile(mr), vocab.region_profile(qr), []
    if mp and qp:
        if (memory_form.get("page") or {}).get("size", mp["paper"]) != qp["paper"]: out.append({"code": "paper_mismatch"})
        if mp["date_order"] != qp["date_order"]: out.append({"code": "date_order_mismatch"})
        if mp["currency"] != qp["currency"]: out.append({"code": "currency_mismatch"})
        if mp["name_order"] != qp["name_order"]: out.append({"code": "name_order_mismatch"})
    if query_provider is not None and query_provider != memory_form.get("provider"):
        out.append({"code": "provider_mismatch"})
    return out
