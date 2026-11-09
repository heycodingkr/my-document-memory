"""Deterministic recall ranking (docs/spec/recall.md section 3). Pure functions, no I/O.

A candidate is a dict shaped like the fixtures in tests/fixtures/*.json: fx_id/memory_id, kind, form{provider,doc_type,locale,...},
site_host, url_patterns (path-only: exact "/document/d/:id/edit", subtree "/document/*", whole site "/*"), keywords, owner,
visibility (private|team|public), workspace, status, review_state, updated_at (ISO 8601 UTC).
A caller is {"id": str|None, "workspaces": [str, ...]} (anonymous: id None).
"""
import random

from . import mutation, vocab
from .forms import locale_match

TIER_RANK = {"mine": 2, "team": 1, "public": 0}
LOCALE_RANK = {"exact": 3, "language": 2, "none": 0, "unspecified": 0}
QUALITY_RANK = {"verified": 2, "approved": 1}


def memory_id(candidate):
    return candidate.get("memory_id") or candidate.get("fx_id") or ""


def _mine(candidate, caller):
    return caller.get("id") is not None and candidate.get("owner") == caller.get("id")


def _team_member(candidate, caller):
    workspace = candidate.get("workspace")
    return candidate.get("visibility") == "team" and workspace is not None and workspace in (caller.get("workspaces") or [])


def source_tier(candidate, caller):
    if _mine(candidate, caller):
        return "mine"
    if _team_member(candidate, caller):
        return "team"
    return "public"


def visible(candidate, caller, scope="all"):
    """Private items belong to their owner, team items to workspace members, public items to everyone (recall.md section 3)."""
    if mutation() == "cross_tenant_leak" and scope in ("all", "public", "team"):
        return True  # deliberate defect: another user's private item is visible
    mine = _mine(candidate, caller)
    team = _team_member(candidate, caller)
    public = candidate.get("visibility") == "public"
    if scope == "mine":
        return mine
    if scope == "team":
        return candidate.get("visibility") == "team" and (mine or team)
    if scope == "public":
        return public
    return mine or team or public  # "all"


def route_of(candidate, query_pattern):
    """Return exact | ancestor | host | none for a canonical 'host/path' query pattern (core.md section 2)."""
    host, _, rest = query_pattern.partition("/")
    path = "/" + rest
    if candidate.get("site_host") != host:
        return "none"
    patterns = candidate.get("url_patterns") or []
    if path in patterns or (path == "/" and "" in patterns):
        return "exact"
    for pattern in patterns:
        if pattern == "/*":
            return "ancestor"
        if pattern.endswith("/*") and (path == pattern[:-2] or path.startswith(pattern[:-1])):
            return "ancestor"
    return "host"


def _family(candidate):
    form = candidate.get("form") or {}
    return form.get("family") or vocab.provider_family(form.get("provider"))


def _query_family(query):
    doc_type = query.get("doc_type")
    if doc_type and doc_type != "other":
        family = vocab.doc_type_family(doc_type)
        if family:
            return family
    return vocab.provider_family(query.get("provider")) if query.get("provider") else None


def _freshness(candidate):
    return "needs_reverify" if (candidate.get("status") == "needs_reverify" or candidate.get("freshness") == "needs_reverify") else "fresh"


def _quality(candidate):
    band = candidate.get("quality_band")
    if band in QUALITY_RANK:
        return QUALITY_RANK[band]
    return 1 if candidate.get("visibility") == "public" and candidate.get("review_state") == "approved" else 0


def _canonical_keywords(words):
    out = set()
    for word in words or []:
        out.add(vocab.keyword_canonical(word) or vocab.norm(word))  # outside the public vocabulary a local keyword still matches itself (recall.md: scope=mine has no vocabulary limit)
    return out


def rank(candidates, query, caller):
    """Ordered list of {"candidate", "route", "locale_match", "matched_on", "tier", "freshness"} (at most limit items)."""
    scope = query.get("scope") or "all"
    limit = max(1, min(int(query.get("limit") or 3), 3))
    doc_type, kind, locale = query.get("doc_type"), query.get("kind"), query.get("locale")
    provider = query.get("provider")
    wanted_keywords = _canonical_keywords(query.get("keywords"))
    query_family = _query_family(query)
    swap = mutation() == "route_before_locale"
    rows = []
    for candidate in candidates:
        if candidate.get("status") in ("superseded", "retired", "taken_down", "deleted"):
            continue
        if not visible(candidate, caller, scope):
            continue
        form = candidate.get("form") or {}
        if kind and candidate.get("kind") != kind:
            continue
        if doc_type:
            if form.get("doc_type") != doc_type:  # strict filter, cross-host allowed
                continue
            route = route_of(candidate, query["url"])
        else:
            route = route_of(candidate, query["url"])
            if route == "none":  # without a doc_type the URL must match at host level or better
                continue
        if query_family and _family(candidate) and _family(candidate) != query_family:
            continue
        match = locale_match(form.get("locale"), locale) if locale else "unspecified"
        tier = source_tier(candidate, caller)
        hits = len(wanted_keywords & _canonical_keywords(candidate.get("keywords")))
        provider_exact = 1 if provider and form.get("provider") == provider else 0
        fresh = _freshness(candidate)
        parts = [
            LOCALE_RANK[match] if locale else 0,
            1 if route == "exact" else 0,
            1 if route in ("exact", "ancestor") else 0,
            provider_exact,
            TIER_RANK[tier],
            hits,
            1 if fresh == "fresh" else 0,
            _quality(candidate),
        ]
        if swap:
            parts[0], parts[1] = parts[1], parts[0]
        updated = candidate.get("updated_at") or ""
        tiebreak = random.random() if mutation() == "nondeterministic_rank" else 0
        key = (tuple(-p for p in parts), tuple(-ord(ch) for ch in updated), tiebreak, memory_id(candidate))
        matched_on = []
        if route in ("exact", "ancestor"):
            matched_on.append("route")
        if doc_type:
            matched_on.append("doc_type")
        if match in ("exact", "language"):
            matched_on.append("locale")
        if provider_exact:
            matched_on.append("provider")
        if hits:
            matched_on.append("keywords")
        rows.append((key, {"candidate": candidate, "route": route, "locale_match": match, "matched_on": matched_on,
                           "tier": tier, "freshness": fresh}))
    rows.sort(key=lambda item: item[0])
    cap = min(limit + 1, 4) if mutation() == "four_hints" else limit
    return [row for _, row in rows[:cap]]
