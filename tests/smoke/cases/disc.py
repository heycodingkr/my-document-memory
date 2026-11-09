"""DISC-01..DISC-08: web search for related documents (docs/test/functional-tests.md, docs/spec/web-import.md section 7).

The loopback fixture server's /search route plays the search provider (docs/test/fixtures.md section 4). Special query texts switch its behaviour:
`__mode:429`, `__mode:500`, `__mode:slow`, `__mode:hostile`. Its request log keeps query KEY names, the filter values and a sha256 of the query, never the query text.
"""
from dmtest.runner import case
from .util import reject

QUERY = "이력서 양식"


def search_calls(ctx):
    return [e for e in ctx.fx_log() if e["path"] == "/search"]


def web_search(ctx, *args, who="local"):
    return ctx.cli(who).json(["web", "search", *args])


def library_size(ctx):
    return len(ctx.cli().json(["list"]).json["results"])


@case("DISC-01", "F", needs=("fixtures",))
def disc_01(ctx):
    r = web_search(ctx, QUERY)
    reject(ctx, r, "search_unavailable", exit_code=5)
    ctx.expect(search_calls(ctx) == [] and ctx.fx_log() == [], "with provider none no request may leave the machine")
    ctx.expect(ctx.cli().json(["status"]).json["search_provider"] == "none", "status must report the search provider")


@case("DISC-02", "F", needs=("fixtures",))
def disc_02(ctx):
    ctx.search_provider("fixture")
    r = web_search(ctx, QUERY, "--limit", "5")
    ctx.expect(r.exit == 0, f"search failed: {r.json}")
    body = r.json or {}
    candidates = body.get("candidates", [])
    ctx.expect(0 < len(candidates) <= 5, f"expected 1..5 candidates, got {len(candidates)}")
    ctx.expect(body.get("untrusted") is True and body.get("framing", "").startswith("UNTRUSTED REFERENCE DATA."), "search results are untrusted data with the fixed framing")
    ctx.expect(all("?" not in c["url"] and "#" not in c["url"] for c in candidates), "candidate URLs are canonical (no query or fragment)")
    ctx.expect(all(c.get("title") is not None and c.get("snippet") is not None for c in candidates), "every candidate has a title and snippet")
    ctx.schema_ok(body, "doc_memory_web_search", "WebSearchResult")
    ctx.expect(len(search_calls(ctx)) == 1, "one provider request per search")


@case("DISC-03", "F", needs=("fixtures",))
def disc_03(ctx):
    ctx.search_provider("fixture")
    plain = web_search(ctx, QUERY, "--limit", "10")
    ctx.expect(plain.exit == 0 and plain.json["candidates"][0]["detected"]["provider"] != "google_docs", "without filters the provider's own order stands (the Docs-shaped page is last)")
    filtered = web_search(ctx, QUERY, "--locale", "ko-KR", "--doc-type", "resume", "--provider", "google_docs", "--limit", "10")
    ctx.expect(filtered.exit == 0, f"filtered search failed: {filtered.json}")
    first = filtered.json["candidates"][0]
    ctx.expect(first["detected"]["provider"] == "google_docs" and first["detected"]["locale"] == "ko-KR", f"the Docs-shaped ko-KR candidate must come first: {first['detected']}")
    ko = web_search(ctx, QUERY, "--locale", "ko-KR", "--limit", "10").json["candidates"]
    leading = [c["detected"]["locale"] for c in ko[:2]]
    ctx.expect(leading == ["ko-KR", "ko-KR"], f"ko-KR candidates lead the list: {leading}")
    sent = [e["filters"] for e in search_calls(ctx)]
    ctx.expect({"locale": "ko-KR", "doc_type": "resume", "provider": "google_docs"} in sent, f"the provider must receive the filters; saw {sent}")


@case("DISC-04", "F", needs=("fixtures",))
def disc_04(ctx):
    ctx.search_provider("fixture")
    secret = ctx.sentinels.value("api_key", 3)
    reject(ctx, web_search(ctx, secret), "secret_detected")
    ctx.expect(search_calls(ctx) == [], "a secret-shaped query must never reach the provider")
    ok = web_search(ctx, QUERY)
    ctx.expect(ok.exit == 0 and len(search_calls(ctx)) == 1, "a normal query still works")
    logged = search_calls(ctx)[0]
    ctx.expect("q_sha256" in logged and QUERY not in str(logged), "the provider-side log of this harness holds only a hash of the query")
    ctx.expect(not ctx.scan_sinks(("local",), families=("api_key",)), "the secret must not appear in any client sink")
    leaked = ctx.scan_values([QUERY])
    ctx.expect(not leaked, f"the query text must not be written to client state or logs: {leaked}")


@case("DISC-05", "F", needs=("fixtures",))
def disc_05(ctx):
    ctx.search_provider("fixture")
    ctx.expect(web_search(ctx, "가" * 200).exit == 0, "a 200-character query is accepted")
    before = len(search_calls(ctx))
    reject(ctx, web_search(ctx, "가" * 201), "payload_too_large")
    ctx.expect(len(search_calls(ctx)) == before, "an over-long query must not be sent")


@case("DISC-06", "F", needs=("fixtures",))
def disc_06(ctx):
    ctx.search_provider("fixture")
    r = web_search(ctx, "__mode:hostile")
    ctx.expect(r.exit == 0, f"search failed: {r.json}")
    candidates = (r.json or {}).get("candidates", [])
    ctx.expect(len(candidates) == 2, "both hostile candidates are returned as data")
    for c in candidates:
        ctx.expect(len(c["title"]) <= 200 and len(c["snippet"]) <= 400, "fields stay inside their length limits")
        for field in ("title", "snippet"):
            text = c[field]
            ctx.expect("<" not in text and ">" not in text, f"{field}: markup must be stripped")
            ctx.expect(all(ord(ch) >= 32 and ch not in "\u200b‌‍⁠﻿\u202e" for ch in text), f"{field}: control and invisible characters must be removed")
    ctx.expect(r.json.get("untrusted") is True, "the result stays framed as untrusted data")
    ctx.expect(len(search_calls(ctx)) == 1 and not [e for e in ctx.fx_log() if e["path"] != "/search"], "nothing in the snippets may trigger a further request")


@case("DISC-07", "F", needs=("fixtures",))
def disc_07(ctx):
    ctx.search_provider("fixture")
    r = web_search(ctx, QUERY, "--limit", "10")
    urls = [c["url"] for c in (r.json or {}).get("candidates", [])]
    ctx.expect(r.exit == 0 and urls, "the search must still return its safe candidates")
    for bad in ("http://10.0.0.1/x", "file:///etc/passwd", "https://127.0.0.1/", "http://192.168.1.9/private"):
        ctx.expect(not any(u.startswith(bad.rstrip("/")) or u == bad for u in urls), f"unsafe candidate must be dropped: {bad}")
    ctx.expect((r.json or {}).get("filtered", 0) >= 3, f"the number of dropped candidates must be reported: {(r.json or {}).get('filtered')}")


@case("DISC-08", "F", needs=("fixtures",))
def disc_08(ctx):
    ctx.search_provider("fixture")
    limited = web_search(ctx, "__mode:429")
    reject(ctx, limited, "rate_limited", exit_code=6)
    ctx.expect((limited.json or {}).get("error", {}).get("retry_after_seconds") == 7, "the provider's Retry-After is passed on as retry_after_seconds")
    reject(ctx, web_search(ctx, "__mode:500"), "search_unavailable", exit_code=5)
    slow = web_search(ctx, "__mode:slow")
    reject(ctx, slow, "search_unavailable", exit_code=5)
    ctx.expect(slow.seconds < 12, f"a stalled provider must time out, took {slow.seconds:.1f}s")
    for r in (limited, slow):
        ctx.expect("candidates" not in (r.json or {}), "a failed search returns no partial results")
    ctx.expect(library_size(ctx) == 0, "a failed search changes nothing")
