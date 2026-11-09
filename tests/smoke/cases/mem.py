"""MEM-01..MEM-16: memory layers, kinds, slots, provenance and limits (docs/spec/memory.md)."""
import json
import math

from dmtest.runner import case
from .util import recall, save_md


EXAMPLE = "example.com/*"


def payload(kind="template", title="memory", *, variant=None, doc_type="resume", body="# Heading\n\nBody text.",
            summary=None, key_points=None, keywords=None, url_patterns=None):
    form = {"doc_type": doc_type, "locale": "ko-KR", "provider": "markdown"}
    if variant is not None:
        form["variant"] = variant
    obj = {"kind": kind, "title": title, "form": form,
           "content": {"format": "markdown", "data": body}}
    if summary is not None:
        obj["summary"] = summary
    if key_points is not None:
        obj["key_points"] = key_points
    if keywords is not None:
        obj["keywords"] = keywords
    if url_patterns is not None:
        obj["url_patterns"] = url_patterns
    else:
        obj["url_patterns"] = [EXAMPLE]
    return obj


def mixed_text(length):
    seed = "환불 policy 기억을 확인합니다 "
    return (seed * (length // len(seed) + 1))[:length]


@case("MEM-01", "R1", needs=())
def mem_01(ctx):
    refund = "환불은 미개봉 상품에 한해 구매 후 7일 이내 신청 가능"
    shipping = "배송은 영업일 기준 3일 이내"
    a = save_md(ctx, refund, kind="reference", title="M6 refund", doc_type="other", locale="ko-KR",
                extra=["--url-pattern", EXAMPLE, "--variant", "m6_refund", "--keyword", "refund"])
    b = save_md(ctx, shipping, kind="reference", title="M6b shipping", doc_type="other", locale="ko-KR",
                extra=["--url-pattern", EXAMPLE, "--variant", "m6b_shipping", "--keyword", "shipping"])
    ctx.expect(a.exit == 0 and b.exit == 0, "M6 and M6b reference saves must succeed")

    r = recall(ctx, "https://example.com/", doc_type="other", kind="reference", keywords=["refund"])
    hints = (r.json or {}).get("hints", [])
    first = hints[0] if hints else None
    ctx.expect(r.exit == 0 and first is not None, "refund recall must return a first hint")
    ctx.expect(first is not None and first.get("title") == "M6 refund", "M6 must be the first hint")
    ctx.expect(first is not None and shipping not in json.dumps(first, ensure_ascii=False),
               "M6b shipping text must not be mixed into the first hint")
    memory_id = first.get("memory_id", "missing") if first else "missing"
    expanded = ctx.cli().json(["expand", memory_id, "--level", "2"])
    spans = ((expanded.json or {}).get("l2") or {}).get("spans", [])
    first_span = spans[0] if spans else {}
    ctx.expect(expanded.exit == 0 and first_span.get("text") == refund and first_span.get("locator") == "p:1",
               "M6 L2 spans[0] must equal the refund fact at p:1")


@case("MEM-02", "R1", needs=())
def mem_02(ctx):
    valid = [
        ("title", payload(title="T" * 120, variant="mem02_title_ok")),
        ("summary", payload(title="summary-ok", variant="mem02_summary_ok", summary="S" * 600)),
        ("key_points", payload(title="points-ok", variant="mem02_points_ok", key_points=[f"point {i}" for i in range(6)])),
        ("keyword_length", payload(title="keyword-length-ok", variant="mem02_kwlen_ok", keywords=["k" * 32])),
        ("keyword_count", payload(title="keyword-count-ok", variant="mem02_kwcount_ok", keywords=[f"key {i}" for i in range(8)])),
        ("url_pattern_count", payload(title="pattern-count-ok", variant="mem02_patterns_ok",
                                       url_patterns=[f"example.com/path-{i}" for i in range(4)])),
    ]
    invalid = [
        ("title", payload(title="T" * 121, variant="mem02_title_bad")),
        ("summary", payload(title="summary-bad", variant="mem02_summary_bad", summary="S" * 601)),
        ("key_points", payload(title="points-bad", variant="mem02_points_bad", key_points=[f"point {i}" for i in range(7)])),
        ("keyword_length", payload(title="keyword-length-bad", variant="mem02_kwlen_bad", keywords=["k" * 33])),
        ("keyword_count", payload(title="keyword-count-bad", variant="mem02_kwcount_bad", keywords=[f"key {i}" for i in range(9)])),
        ("url_pattern_count", payload(title="pattern-count-bad", variant="mem02_patterns_bad",
                                       url_patterns=[f"example.com/path-{i}" for i in range(5)])),
    ]
    with ctx.mcp() as m:
        for label, obj in valid:
            result = m.call("doc_memory_save", obj)
            ctx.expect(result is not None and not result.is_error, f"{label} at its documented limit must save")
        for label, obj in invalid:
            result = m.call("doc_memory_save", obj)
            ctx.expect(result is not None and result.is_error and result.code == "invalid_input",
                       f"{label} above its documented limit must return invalid_input")
            listed = ctx.cli().json(["list"])
            rows = (listed.json or {}).get("results", [])
            ctx.expect(listed.exit == 0 and len(rows) == len(valid), f"{label} rejection must leave the saved count unchanged")


@case("MEM-03", "R1", needs=())
def mem_03(ctx):
    empty_template = save_md(ctx, "", title="empty-template", extra=["--variant", "mem03_template"])
    empty_reference = save_md(ctx, "", kind="reference", title="empty-reference", doc_type="other",
                              extra=["--variant", "mem03_reference"])
    empty_rules = save_md(ctx, "", kind="style_rule", title="empty-rules", doc_type="other",
                          extra=["--variant", "mem03_rules"])
    for label, result in (("template", empty_template), ("reference", empty_reference), ("style_rule", empty_rules)):
        ctx.expect(result.exit == 2 and result.code in ("extract_empty", "invalid_input"),
                   f"empty {label} must be rejected as extract_empty or invalid_input")
        listed = ctx.cli().json(["list"])
        rows = (listed.json or {}).get("results", [])
        ctx.expect(listed.exit == 0 and rows == [], f"rejected empty {label} must leave the library empty")


@case("MEM-04", "R1", needs=())
def mem_04(ctx):
    sentinel = ctx.sentinels.value("prose", 6)
    saved = save_md(ctx, f"# L2 template\n\n{sentinel}", title="L2-only template",
                    extra=["--url-pattern", EXAMPLE, "--variant", "mem04_l2"])
    ctx.expect(saved.exit == 0, "template containing prose-06 must save")
    r = recall(ctx, "https://example.com/", doc_type="resume", locale="ko-KR", kind="template")
    recall_text = json.dumps(r.json or {}, ensure_ascii=False)
    ctx.expect(r.exit == 0 and sentinel not in recall_text, "prose-06 must not appear in recall L1")
    hints = (r.json or {}).get("hints", [])
    memory_id = hints[0].get("memory_id", "missing") if hints else "missing"
    l1 = ctx.cli().json(["expand", memory_id, "--level", "1"])
    ctx.expect(l1.exit == 0 and sentinel not in json.dumps(l1.json or {}, ensure_ascii=False),
               "prose-06 must not appear in expand level 1")
    l2 = ctx.cli().json(["expand", memory_id, "--level", "2"])
    ctx.expect(l2.exit == 0 and sentinel in json.dumps(l2.json or {}, ensure_ascii=False),
               "prose-06 must appear in expand level 2")


@case("MEM-05", "F", needs=())
def mem_05(ctx):
    title = mixed_text(120)
    summary = mixed_text(600)
    key_points = [mixed_text(160) for _ in range(6)]
    headings = "\n".join(f"## {mixed_text(58)}" for _ in range(12))
    with ctx.mcp() as m:
        saves = [m.call("doc_memory_save", payload(title=title, variant=f"mem05_v{i}", body=headings,
                                                    summary=summary, key_points=key_points)) for i in range(5)]
    ctx.expect(all(r is not None and not r.is_error for r in saves), "five maximum-length mixed Korean/English L1 memories must save")
    r = recall(ctx, "https://example.com/", doc_type="resume", locale="ko-KR", kind="template")
    hints = (r.json or {}).get("hints", [])
    ctx.expect(r.exit == 0 and len(hints) <= 3, "recall must return at most three hints")
    sizes = [math.ceil(len(json.dumps(h, ensure_ascii=False).encode("utf-8")) / 4) for h in hints]
    ctx.expect(all(size <= 400 for size in sizes), f"every hint must be at most 400 estimated tokens (observed {sizes})")
