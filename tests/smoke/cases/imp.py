"""IMP-01..IMP-20: web preview, import and clip (docs/test/functional-tests.md, docs/spec/web-import.md).

Every case runs against the loopback fixture server (docs/test/fixtures.md section 4) with DMEM_ISOLATED=1, and counts the requests the fixture saw.
The fixture's request log keeps header NAMES only, so "no credentials were sent" is a statement about names.
"""
import json
import resource
import sys
import threading
import urllib.request
from datetime import datetime, timezone

from dmtest.runner import case
from .util import reject

STRUCT_ONLY = ["structure_only"]
FIXTURE = ("fixtures",)


def page(ctx, name):
    return f"{ctx.fx_url}/pages/{name}"


def preview(ctx, url, who="local", env=None):
    return ctx.cli(who, env).json(["web", "preview", url])


def do_import(ctx, url, *extra, who="local", env=None, as_="template"):
    return ctx.cli(who, env).json(["import", url, "--as", as_, *extra])


def library(ctx, who="local"):
    return ctx.cli(who).json(["list"]).json["results"]


def fx_set(ctx, html):
    request = urllib.request.Request(ctx.fx_url + "/__set", data=json.dumps({"html": html}).encode("utf-8"), method="POST")
    urllib.request.urlopen(request, timeout=3).read()


def l2_text(ctx, memory_id, who="local"):
    r = ctx.cli(who).json(["expand", memory_id, "--level", "2"])
    ctx.expect(r.exit == 0, f"expand {memory_id} failed")
    return r.stdout


def peak_rss_mb():
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    return peak / (1024 * 1024) if sys.platform == "darwin" else peak / 1024


@case("IMP-01", "F", needs=FIXTURE)
def imp_01(ctx):
    r = preview(ctx, page(ctx, "resume-ko.html"))
    body = r.json or {}
    ctx.expect(r.exit == 0, f"preview failed: {body}")
    ctx.schema_ok(body, "doc_memory_web_preview", "WebPreviewResult")
    titles = [h["text"] for h in body.get("outline", [])]
    ctx.expect({"인적사항", "경력", "학력", "기술"} <= set(titles), f"the outline lists the headings: {titles}")
    ctx.expect(body.get("stats", {}).get("headings", 0) >= 4 and body.get("stats", {}).get("tables") == 1, f"stats: {body.get('stats')}")
    ctx.expect(body.get("license") == {"id": "CC-BY-4.0", "source": "detected"}, f"the rel=license link is detected: {body.get('license')}")
    ctx.expect(str(body.get("content_hash", "")).startswith("sha256:"), "a content_hash is returned")
    ttl = (datetime.fromisoformat(body["expires_at"].replace("Z", "+00:00")) - datetime.now(timezone.utc)).total_seconds()
    ctx.expect(0 < ttl <= 15 * 60 + 5, f"a preview lives at most 15 minutes: {ttl:.0f}s")
    ctx.expect(library(ctx) == [], "a preview must not change the library")


@case("IMP-02", "F", needs=FIXTURE)
def imp_02(ctx):
    url = page(ctx, "mutable.html")
    fx_set(ctx, "<html lang='ko'><body><h1>원본 제목</h1><h2>경력</h2><p>ORIGINAL_BODY_TEXT</p></body></html>")
    first = preview(ctx, url)
    ctx.expect(first.exit == 0, "preview failed")
    fx_set(ctx, "<html lang='ko'><body><h1>바뀐 제목</h1><h2>경력</h2><p>CHANGED_BODY_TEXT</p></body></html>")
    saved = ctx.cli().json(["import", "--preview", first.json["preview_id"], "--as", "template"])
    ctx.expect(saved.exit == 0 and saved.json["source"]["content_hash"] == first.json["content_hash"], "the stored hash is the previewed one, not the changed page's")
    text = l2_text(ctx, saved.json["memory_id"])
    ctx.expect("ORIGINAL_BODY_TEXT" in text or "원본 제목" in text, "the stored content is the previewed content")
    ctx.expect("CHANGED_BODY_TEXT" not in text and "바뀐 제목" not in text, "the changed page must not leak into the saved import")
    ctx.expect(len([e for e in ctx.fx_log() if e["path"] == "/pages/mutable.html"]) == 1, "importing a preview must not fetch the page again")
    second = preview(ctx, url)
    late = ctx.cli(extra_env={"DMEM_TEST_CLOCK_OFFSET": "960"}).json(["import", "--preview", second.json["preview_id"], "--as", "template"])
    reject(ctx, late, "not_found", exit_code=7)


@case("IMP-03", "F", needs=FIXTURE)
def imp_03(ctx):
    query, fragment = ctx.sentinels.value("url_parts", 1), ctx.sentinels.value("url_parts", 2)
    r = do_import(ctx, page(ctx, "resume-ko.html") + f"?k={query}#{fragment}")
    source = (r.json or {}).get("source", {})
    ctx.expect(r.exit == 0, f"import failed: {r.json}")
    ctx.expect(source.get("origin") == "fetched" and source.get("provenance") == "fetched" and source.get("source_host") == "fixture.test", f"origin block: {source}")
    ctx.expect(source.get("source_url") == "fixture.test/pages/resume-ko.html", f"the stored URL is canonical: {source.get('source_url')}")
    ctx.expect(source.get("retrieved_at") and str(source.get("content_hash", "")).startswith("sha256:"), "retrieved_at and content_hash are recorded")
    ctx.expect(all(not e["has_query"] for e in ctx.fx_log()), "the query must not even be sent to the site")
    ctx.expect(not ctx.scan_sinks(("local",), families=("url_parts",), server=False), "query and fragment sentinels must be absent from every sink")


@case("IMP-04", "F", needs=FIXTURE)
def imp_04(ctx):
    expected = {"license-cc0.html": "CC0-1.0", "resume-ko.html": "CC-BY-4.0", "license-mit.html": "MIT", "license-jsonld.html": "CC-BY-4.0", "license-by-sa.html": "CC-BY-SA-4.0"}
    for name, license_id in expected.items():
        p = preview(ctx, page(ctx, name))
        ctx.expect(p.exit == 0 and p.json["license"] == {"id": license_id, "source": "detected"}, f"{name}: expected {license_id} detected, got {(p.json or {}).get('license')}")
        r = do_import(ctx, page(ctx, name))
        source = (r.json or {}).get("source", {})
        ctx.expect(r.exit == 0 and source.get("license") == license_id and source.get("license_source") == "detected", f"{name}: stored licence {source.get('license')}/{source.get('license_source')}")
        ctx.expect((r.json or {}).get("copy_policy_applied", source.get("copy_policy")) == "full", f"{name}: a permissive licence allows a full copy")


@case("IMP-05", "F", needs=FIXTURE)
def imp_05(ctx):
    for name, license_id, sentinel, cell in (("license-none.html", "unknown", "PROSE_SENTINEL_U1", "BODYCELL_U1"), ("license-nc.html", "proprietary-structure-only", "PROSE_SENTINEL_N1", "BODYCELL_N1")):
        r = do_import(ctx, page(ctx, name))
        source = (r.json or {}).get("source", {})
        ctx.expect(r.exit == 0 and source.get("license") == license_id and source.get("copy_policy") == "structure_only", f"{name}: expected {license_id} and structure_only, got {source.get('license')}/{source.get('copy_policy')}")
        text = l2_text(ctx, r.json["memory_id"])
        ctx.expect(sentinel not in text and cell not in text, f"{name}: prose and table body cells must not be stored")
        ctx.expect(("Scope" in text or "Terms" in text) and "Item" in text, f"{name}: headings and table headers are kept")


@case("IMP-06", "F", needs=FIXTURE)
def imp_06(ctx):
    r = do_import(ctx, page(ctx, "license-none.html"), "--copy-mode", "full")
    reject(ctx, r, "license_forbids", exit_code=4)
    ctx.expect((r.json or {}).get("error", {}).get("allowed_modes") == STRUCT_ONLY, "allowed_modes lists structure_only")
    ctx.expect(library(ctx) == [], "a refused import stores nothing")


@case("IMP-07", "F", needs=("fixtures", "server"))
def imp_07(ctx):
    r = do_import(ctx, page(ctx, "license-none.html"), "--license", "CC0-1.0", who="alice")
    source = (r.json or {}).get("source", {})
    ctx.expect(r.exit == 0 and source.get("license") == "CC0-1.0" and source.get("license_source") == "user_asserted" and source.get("unverified") is True, f"a claimed licence without a detected one is kept as unverified: {source}")
    published = ctx.cli("alice").json(["publish", r.json["memory_id"], "--visibility", "public", "--license", "CC0-1.0", "--consent"])
    ctx.expect(published.exit == 0 and published.json["review_state"] == "rejected" and "license" in published.json["reasons"], f"an unverified source must not be publishable: {published.json}")
    before = len(library(ctx, "alice"))
    conflict = do_import(ctx, page(ctx, "license-nc.html"), "--license", "CC0-1.0", who="alice")
    reject(ctx, conflict, "license_forbids", exit_code=4)
    ctx.expect(len(library(ctx, "alice")) == before, "a conflicting claim stores nothing")


@case("IMP-08", "F", needs=("fixtures", "server"))
def imp_08(ctx):
    p = preview(ctx, page(ctx, "noai-meta.html"), who="alice")
    ctx.expect(p.exit == 0 and p.json["signals"]["noai"] is True, f"a noai meta tag is reported in the preview: {(p.json or {}).get('signals')}")
    r = do_import(ctx, page(ctx, "noai-meta.html"), who="alice")
    ctx.expect(r.exit == 0 and r.json["source"]["copy_policy"] == "structure_only", f"noai forces structure_only: {(r.json or {}).get('source')}")
    published = ctx.cli("alice").json(["publish", r.json["memory_id"], "--visibility", "public", "--license", "CC0-1.0", "--consent"])
    ctx.expect(published.exit == 0 and published.json["review_state"] == "rejected", f"a noai import must not be publishable: {published.json}")
    reject(ctx, preview(ctx, page(ctx, "noai-header.html"), who="alice"), "fetch_blocked", "signal_noai")
    reject(ctx, do_import(ctx, page(ctx, "noai-header.html"), who="alice"), "fetch_blocked", "signal_noai")


@case("IMP-09", "F", needs=FIXTURE)
def imp_09(ctx):
    for url in ("https://10.0.0.5/", "https://169.254.169.254/", "https://[fd00::1]/", "https://2130706433/"):
        r = preview(ctx, url)
        ctx.expect(r.exit == 2 and r.code in ("url_rejected", "fetch_blocked"), f"{url}: expected a rejection, got exit {r.exit} {r.code}")
    r = preview(ctx, page(ctx, "resume-ko.html"), env={"DMEM_ISOLATED": "0"})
    ctx.expect(r.exit == 2 and r.code in ("url_rejected", "fetch_blocked"), f"loopback outside isolated mode must be refused: {r.code}")
    ctx.expect(ctx.fx_log() == [], "a refused target must produce no request at all")


@case("IMP-10", "F", needs=FIXTURE)
def imp_10(ctx):
    env = {"DMEM_TEST_RESOLVE": "mixed.test=203.0.113.10,10.0.0.7;loop.test=127.0.0.1"}
    for host in ("mixed.test", "loop.test"):
        reject(ctx, preview(ctx, f"https://{host}/", env=env), "fetch_blocked", "private_address")
    ctx.expect(ctx.fx_log() == [], "no request may leave for a blocked name")


@case("IMP-11", "F", needs=FIXTURE)
def imp_11(ctx):
    ok = preview(ctx, f"{ctx.fx_url}/redirect/3")  # the query is dropped before fetching, so the fixture's default target (resume-us) is what ends the chain
    ctx.expect(ok.exit == 0 and ok.json["title"] == "US Resume", f"three redirects are followed and the final page is what is read: {ok.code} {(ok.json or {}).get('title')}")
    reject(ctx, preview(ctx, f"{ctx.fx_url}/redirect/4"), "fetch_blocked", "redirect_limit")
    reject(ctx, preview(ctx, f"{ctx.fx_url}/redirect/private"), "fetch_blocked", "private_address")
    ctx.expect(not [e for e in ctx.fx_log() if "10.255.255.1" in e["path"]], "no request may follow the redirect to a private address")


@case("IMP-12", "F", needs=FIXTURE)
def imp_12(ctx):
    for url in ("file:///etc/passwd", "ftp://example.com/a", "data:text/html,hello", "javascript:alert(1)", "https://example.com:8443/"):
        r = preview(ctx, url)
        ctx.expect(r.exit == 2 and r.code == "url_rejected" and (r.error or {}).get("reason") in ("scheme_not_allowed", "host_not_allowed"), f"{url}: expected url_rejected scheme/host, got {r.code} {(r.error or {}).get('reason')}")
    ctx.expect(ctx.fx_log() == [], "a refused scheme or port must produce no request")


@case("IMP-13", "F", needs=FIXTURE)
def imp_13(ctx):
    for path in ("/big", "/gzbomb"):
        before = peak_rss_mb()
        r = preview(ctx, ctx.fx_url + path)
        growth = peak_rss_mb() - before
        reject(ctx, r, "fetch_blocked", "size")
        ctx.expect(r.seconds < 8, f"{path}: stopped in {r.seconds:.1f}s")
        ctx.expect(growth < 40, f"{path}: the client's peak memory grew by {growth:.0f} MiB (limit 40)")
    ctx.expect(library(ctx) == [], "nothing is stored from an oversized response")


@case("IMP-14", "F", needs=FIXTURE)
def imp_14(ctx):
    r = preview(ctx, ctx.fx_url + "/slow")
    reject(ctx, r, "fetch_blocked", "timeout")
    ctx.expect(9 <= r.seconds <= 13, f"the deadline is about 10s, took {r.seconds:.1f}s")
    ctx.expect(library(ctx) == [], "a timed-out fetch stores nothing")


@case("IMP-15", "F", needs=FIXTURE)
def imp_15(ctx):
    for path in ("/type-mismatch.docx", "/binary"):
        reject(ctx, preview(ctx, ctx.fx_url + path), "fetch_blocked", "content_type")
    ctx.expect(library(ctx) == [], "nothing is stored from a disallowed type")


@case("IMP-16", "F", needs=FIXTURE)
def imp_16(ctx):
    for path in ("/pages/login-required", "/pages/unauthorized", "/pages/forbidden"):
        r = preview(ctx, ctx.fx_url + path)
        reject(ctx, r, "fetch_blocked", "login_required")
        message = (r.error or {}).get("message", "")
        ctx.expect("--file" in message and "clip" in message.lower(), f"{path}: the error must point at the alternatives (a downloaded --file, a clipped tab)")
    names = {n.lower() for e in ctx.fx_log() for n in e["header_names"]}
    ctx.expect(ctx.fx_log() and not ({"cookie", "authorization", "referer"} & names), f"no credential header may be sent, saw {sorted(names)}")


@case("IMP-17", "F", needs=FIXTURE)
def imp_17(ctx):
    for name in ("hostile-inject.html", "hostile-static.html"):
        r = do_import(ctx, page(ctx, name))
        ctx.expect(r.exit == 0, f"{name}: import failed: {(r.json or {}).get('error')}")
        codes = {w["code"] if isinstance(w, dict) else w for w in (r.json or {}).get("warnings", [])}
        ctx.expect({"hidden_text_removed", "injection_flagged"} <= codes, f"{name}: warnings {sorted(codes)}")
        stored = l2_text(ctx, r.json["memory_id"]) + ctx.cli().json(["expand", r.json["memory_id"], "--level", "1"]).stdout
        for needle in ("HIDDEN_SENTINEL_", "<script", "<iframe", "onerror", "\u200b", "\u202e", "‭", "⁦"):
            ctx.expect(needle not in stored, f"{name}: stored content must not contain {needle!r}")
        level1 = ctx.cli().json(["expand", r.json["memory_id"], "--level", "1"]).json
        summary = json.dumps({k: level1.get(k) for k in ("title", "summary", "key_points", "outline")}, ensure_ascii=False).lower()
        ctx.expect("ignore all previous" not in summary and "이전 지시를 무시" not in summary and "send the document" not in summary, f"{name}: L1 must not carry the injection text")


@case("IMP-18", "F", needs=FIXTURE)
def imp_18(ctx):
    shapes = [("/p/google-docs/document/d/FIX_KO_RESUME/edit", "google_docs", "document"), ("/p/google-slides/presentation/d/FIX_DECK/edit", "google_slides", "deck"),
              ("/p/notion/Quarterly-Report-0123456789abcdef0123456789abcdef", "notion", "document")]
    for path, provider, family in shapes:
        p = preview(ctx, ctx.fx_url + path)
        ctx.expect(p.exit == 0 and p.json["provider"] == provider, f"{path}: provider {(p.json or {}).get('provider')} (expected {provider}) {p.code}")
        r = do_import(ctx, ctx.fx_url + path)
        ctx.expect(r.exit == 0 and r.json["form"]["provider"] == provider and r.json["form"]["family"] == family, f"{path}: stored form {(r.json or {}).get('form')}")
        if r.exit == 0:
            structure = json.loads(ctx.cli().json(["expand", r.json["memory_id"], "--level", "2"]).stdout)["l2"]["structure"]
            ctx.expect(structure.get("type") == family, f"{path}: StandardDoc type {structure.get('type')} (expected {family})")
    docs = preview(ctx, ctx.fx_url + shapes[0][0])
    ctx.expect(docs.json["detected"]["doc_type"] == "resume" and docs.json["detected"]["locale"] == "ko-KR", f"doc_type and locale are suggested: {docs.json['detected']}")
    slide_formats = [e.get("format") for e in ctx.fx_log() if "/google-slides/" in e["path"] and "/export" in e["path"]]
    ctx.expect(slide_formats and set(slide_formats) == {"pptx"}, f"Slides must be fetched as pptx only, never as md: {slide_formats}")


@case("IMP-19", "F")
def imp_19(ctx):
    ctx.skip("needs the Arise host adapter (`doc_memory_clip_current_tab` / `dmem browser-mcp`), which the double does not have; "
             "the Arise side of this row (own tab, innerText exposure, login tab refusal) is exercised by tests/smoke/arise_smoke.py and docs/test/host-smoke.md SMK-10")


@case("IMP-20", "F", needs=FIXTURE)
def imp_20(ctx):
    outcomes = [preview(ctx, page(ctx, "resume-us.html"), who="rate") for _ in range(31)]
    codes = [r.code if r.exit else "ok" for r in outcomes]
    ctx.expect(codes[:30] == ["ok"] * 30 and codes[30] == "rate_limited" and outcomes[30].exit == 6, f"the 31st call within a minute is rate limited; got {codes[28:]}")
    ctx.expect(len([e for e in ctx.fx_log() if e["path"] == "/pages/resume-us.html"]) == 30, "a refused call must not fetch")
    ctx.expect(library(ctx, "rate") == [], "a refused call changes nothing")
    results = []

    def slow():
        results.append(ctx.cli("burst").json(["web", "preview", ctx.fx_url + "/slow"]))
    workers = [threading.Thread(target=slow) for _ in range(6)]
    for w in workers:
        w.start()
    for w in workers:
        w.join(30)
    limited = [r for r in results if r.code == "rate_limited"]
    timed_out = [r for r in results if r.code == "fetch_blocked"]
    ctx.expect(len(results) == 6 and len(limited) >= 1 and len(timed_out) >= 4, f"more than 4 concurrent fetches are refused while the first four proceed: limited={len(limited)} timed_out={len(timed_out)}")
    ctx.expect(all(r.exit == 6 for r in limited), "a refused concurrent call exits 6")
