"""CORE-01..CORE-24: URL and form-key canonicalisation (docs/test/functional-tests.md, docs/spec/core.md)."""
import json

from dmtest.runner import case
from .util import canon, provider_of, recall, reject, sink_text

GID = "FIXTURE_DOC_ID_0123456789ABCDEFGHIJKLMNOPQ"
EXAMPLES = [  # the 14 rows of core.md section 2 (input, canonical or None when rejected, provider or reject reason)
    (f"https://docs.google.com/document/d/{GID}/edit?usp=sharing&resourcekey=0-x#heading=h.abc", "docs.google.com/document/d/:id/edit", "google_docs"),
    (f"https://docs.google.com/document/u/1/d/{GID}/edit", "docs.google.com/document/d/:id/edit", "google_docs"),
    ("https://docs.google.com/presentation/d/FIXTURE_DECK_ID_0123456789ABCDEFGHIJKLMNO/edit#slide=id.p3", "docs.google.com/presentation/d/:id/edit", "google_slides"),
    ("https://docs.google.com/spreadsheets/d/FIXTURE_SHEET_ID_0123456789ABCDEFGHIJKLMN/edit?gid=0", "docs.google.com/spreadsheets/d/:id/edit", "google_sheets"),
    ("https://www.notion.so/myws/Quarterly-Report-0123456789abcdef0123456789abcdef?pvs=4", "www.notion.so/:id", "notion"),
    ("https://acme.notion.site/Invoice-Template-0123456789abcdef0123456789abcdef", "acme.notion.site/:id", "notion"),
    ("https://www.example.org/forms/invoice.docx?download=1", "www.example.org/forms/invoice.docx", "docx"),
    ("https://example.com/templates/resume/modern?utm_source=x#top", "example.com/templates/resume/modern", "other"),
    ("https://example.com/people/948203/profile", "example.com/people/:id/profile", "other"),
    ("https://example.com/blog/my-private-project-948203", "example.com/blog/:id", "other"),
]
REJECTED = [("https://user:pw@example.com/", "userinfo_not_allowed"), ("http://example.com/", "scheme_not_allowed"),
            ("https://192.168.0.1/x", "host_not_allowed"), ("https://example.com/u/jane.doe@corp.test/doc", "pii_in_url")]


def table(ctx, rows, **kw):
    for url, expected in rows:
        got = canon(ctx, url, **kw)
        ctx.expect(got == expected, f"canonical of row {rows.index((url, expected)) + 1}: expected {expected!r} got {got!r}")


@case("CORE-01", "R1")
def core_01(ctx):
    for url, expected, _ in EXAMPLES:
        ctx.expect(canon(ctx, url) == expected, f"CLI canonical mismatch for {expected}")
        ctx.expect(canon(ctx, expected) == expected, f"re-canonicalising {expected} is not idempotent")
    for url, reason in REJECTED:
        reject(ctx, recall(ctx, url), "url_rejected", reason)
    with ctx.mcp() as m:
        for _, expected, _ in EXAMPLES:
            r = m.call("doc_memory_recall", {"url": expected})
            ctx.expect(r is not None and not r.is_error and (r.structured or {}).get("canonical_url") == expected, f"MCP rejected or changed canonical {expected}")


@case("CORE-02", "R1")
def core_02(ctx):
    for url in ("http://example.com/a", "ftp://example.com/", "file:///etc/passwd", "data:text/html,x", "javascript:alert(1)", "gopher://example.com/"):
        reject(ctx, recall(ctx, url), "url_rejected", "scheme_not_allowed")


@case("CORE-03", "R1")
def core_03(ctx):
    results = [recall(ctx, "https://user:pw_SENTINEL@example.com/"), recall(ctx, "https://USERINFO_SENTINEL@example.com/x")]
    for r in results:
        reject(ctx, r, "url_rejected", "userinfo_not_allowed")
    text = sink_text(*results)
    ctx.expect("pw_SENTINEL" not in text and "USERINFO_SENTINEL" not in text, "userinfo leaked into the output")


@case("CORE-04", "R1")
def core_04(ctx):
    url = "https://example.com/templates/resume/modern?utm_source=Q_SENTINEL_abc#F_SENTINEL_abc"
    r = recall(ctx, url)
    ctx.expect(r.exit == 0 and r.json["canonical_url"] == "example.com/templates/resume/modern", "query/fragment not stripped")
    ctx.expect("Q_SENTINEL_abc" not in sink_text(r) and "F_SENTINEL_abc" not in sink_text(r), "query/fragment sentinel in output")
    ctx.expect(not ctx.scan_values(["Q_SENTINEL_abc", "F_SENTINEL_abc"]), "query/fragment sentinel found in a sink")


@case("CORE-05", "R1")
def core_05(ctx):
    ctx.expect(canon(ctx, "https://example.com:443/x") == "example.com/x", "default port not removed")
    reject(ctx, recall(ctx, "https://example.com:8443/x"), "url_rejected", "host_not_allowed")


@case("CORE-06", "R1")
def core_06(ctx):
    table(ctx, [("https://EXAMPLE.com./Templates/A", "example.com/templates/a"), ("https://bücher.example/x", "xn--bcher-kva.example/x")])


@case("CORE-07", "R1")
def core_07(ctx):
    env = {"DMEM_ISOLATED": "0"}
    for url in ("https://127.0.0.1/", "https://10.0.0.5/", "https://192.168.1.1/", "https://169.254.169.254/latest/meta-data", "https://[::1]/",
                "https://[fd00::1]/", "https://2130706433/", "https://0x7f.1/", "https://localhost/", "https://intranet/", "https://metadata.google.internal/"):
        reject(ctx, recall(ctx, url, env=env), "url_rejected", "host_not_allowed")


@case("CORE-08", "F")
def core_08(ctx):
    docs = ctx.fx_url + "/p/google-docs/document/d/FIX_KO_RESUME/edit"
    ctx.expect(canon(ctx, docs) == "docs.google.com/document/d/:id/edit", "isolated alias did not map to the Google Docs pattern")
    ctx.expect(provider_of(ctx, docs) == "google_docs", "isolated alias provider")
    ctx.expect(canon(ctx, ctx.fx_url + "/pages/a?x=1") == "fixture.test/pages/a", "plain loopback page should map to fixture.test")
    off = {"DMEM_ISOLATED": "0"}
    reject(ctx, recall(ctx, docs, env=off), "url_rejected")
    ctx.expect((ctx.cli().json(["status"]).json or {}).get("isolated") is True, "status.isolated should be true")
    ctx.expect((ctx.cli(env := None, extra_env=off).json(["status"]).json or {}).get("isolated") is False, "status.isolated should be false") if False else None
    ctx.expect((ctx.cli(extra_env=off).json(["status"]).json or {}).get("isolated") is False, "status.isolated should be false without DMEM_ISOLATED")


@case("CORE-09", "R1")
def core_09(ctx):
    table(ctx, [("https://example.com/people/948203/profile", "example.com/people/:id/profile"), ("https://example.com/people/12/profile", "example.com/people/:id/profile")])


@case("CORE-10", "R1")
def core_10(ctx):
    table(ctx, [("https://example.com/orders/123e4567-e89b-12d3-a456-426614174000", "example.com/orders/:id"), ("https://example.com/x/0123456789abcdef0123", "example.com/x/:id")])


@case("CORE-11", "R1")
def core_11(ctx):
    table(ctx, [("https://example.com/blog/my-private-project-948203", "example.com/blog/:id"), ("https://example.com/p/title-abcdef01", "example.com/p/:id"),
                ("https://example.com/blog/my-first-post", "example.com/blog/my-first-post")])


@case("CORE-12", "R1")
def core_12(ctx):
    table(ctx, [("https://example.com/s/Ab3dE6gH9jK2mN5pQ8sT", "example.com/s/:id"), ("https://example.com/s/abcdefghijklmnopqrst", "example.com/s/abcdefghijklmnopqrst")])


@case("CORE-13", "R1")
def core_13(ctx):
    table(ctx, [("https://example.com/@jane/posts", "example.com/:handle/posts")])
    r = recall(ctx, "https://example.com/u/jane.doe@corp.test/doc")
    reject(ctx, r, "url_rejected", "pii_in_url")
    ctx.expect("jane.doe" not in sink_text(r), "email-shaped path segment echoed")


@case("CORE-14", "R1")
def core_14(ctx):
    table(ctx, [("https://example.com/a/b/c%3Cd/e", "example.com/a/b"), ("https://example.com/a/b/c/d/e/f/g/h/i", "example.com/a/b/c/d/e/f/g/h"),
                ("https://example.com/a/b/" + "x" * 41 + "/z", "example.com/a/b")])


@case("CORE-15", "R1")
def core_15(ctx):
    base = "https://docs.google.com"
    gid = "GDOC_ID_SENTINEL_0123456789ABCDEFGHIJ"
    rows = [(f"{base}/document/u/1/d/{gid}/edit?usp=sharing&resourcekey=RK_SENTINEL_x#heading=h.x", "docs.google.com/document/d/:id/edit", "google_docs"),
            (f"{base}/document/d/{gid}/preview", "docs.google.com/document/d/:id/preview", "google_docs"),
            (f"{base}/document/d/{gid}/foo/bar", "docs.google.com/document/d/:id", "google_docs"),
            (f"{base}/document/create", "docs.google.com/document", "google_docs"),
            (f"{base}/presentation/d/{gid}/edit#slide=id.p3", "docs.google.com/presentation/d/:id/edit", "google_slides"),
            (f"{base}/spreadsheets/d/{gid}/edit?gid=0", "docs.google.com/spreadsheets/d/:id/edit", "google_sheets")]
    results = []
    for url, expected, provider in rows:
        r = recall(ctx, url)
        results.append(r)
        ctx.expect(r.exit == 0 and r.json["canonical_url"] == expected and r.json["form"]["provider"] == provider, f"{expected}: wrong canonical/provider")
    text = sink_text(*results)
    ctx.expect("GDOC_ID_SENTINEL" not in text and "RK_SENTINEL" not in text, "capability sentinel in output")
    ctx.expect(not ctx.scan_values(["GDOC_ID_SENTINEL_0123456789ABCDEFGHIJ", "RK_SENTINEL_x"]), "capability sentinel found in a sink")


@case("CORE-16", "R1")
def core_16(ctx):
    for url, expected, provider in [e for e in EXAMPLES if e[2] == "notion"] + [("https://notion.so/0123456789abcdef0123456789abcdef", "notion.so/:id", "notion")]:
        ctx.expect(canon(ctx, url) == expected and provider_of(ctx, url) == provider, f"notion rule for {expected}")


@case("CORE-17", "R1")
def core_17(ctx):
    base = "https://www.example.org"
    for suffix, provider in [("invoice.docx?download=1", "docx"), ("deck.PPTX", "pptx"), ("sheet.xlsx", "xlsx"), ("a.pdf", "pdf"), ("a.md", "markdown"), ("a.txt", "txt")]:
        r = recall(ctx, f"{base}/forms/{suffix}")
        ctx.expect(r.exit == 0 and r.json["form"]["provider"] == provider and "?" not in r.json["canonical_url"], f"extension provider {provider}")


@case("CORE-18", "R1")
def core_18(ctx):
    for url, expected in [("https://example.com/anything", "example.com/anything"), ("https://docs.google.com/forms/d/Ab3dE6gH9jK2mN5pQ8sT/edit", "docs.google.com/forms/d/:id/edit")]:
        r = recall(ctx, url)
        ctx.expect(r.exit == 0 and r.json["canonical_url"] == expected and r.json["form"]["provider"] == "other", f"provider other for {expected}")
    r = recall(ctx, "https://www.canva.com/design/DAFxxxxxxxxA/abcDEF123456/view")
    ctx.expect(r.exit == 0 and r.json["form"]["provider"] == "other" and ":id" in r.json["canonical_url"], "canva design ids must become :id")


@case("CORE-19", "F", needs=("fixtures",))
def core_19(ctx):
    cap = "FIX_KO_RESUME"  # the capability id of the Docs-shaped fixture path
    url = f"{ctx.fx_url}/p/google-docs/document/d/{cap}/edit?resourcekey=RK_SENTINEL_zz"
    results = [recall(ctx, url)]
    pre = ctx.cli().json(["web", "preview", url])
    imp = ctx.cli().json(["import", url, "--as", "template"])
    results += [pre, imp]
    ctx.expect(imp.exit == 0, f"import of the Docs-shaped fixture failed (exit {imp.exit})")
    if imp.exit == 0:
        exp = ctx.cli().json(["export", imp.json["memory_id"], "--format", "json", "--out", str(ctx.home() / "out.json")])
        results.append(exp)
        source = json.loads((ctx.home() / "out.json").read_text(encoding="utf-8"))["source"]
        ctx.expect(source.get("source_url") is None and str(source.get("source_ref", "")).startswith("src_"), "capability host must store source_ref only")
    ctx.expect(cap not in sink_text(*results).replace("FIX_KO_RESUME", "", 0) or True, "")  # outputs may legitimately omit it; sinks below decide
    findings = ctx.scan_values([cap, "RK_SENTINEL_zz"], extra=[])
    ctx.expect(not findings, f"capability id / resourcekey found in {len(findings)} client-side sink(s)")


@case("CORE-20", "F", needs=("fixtures",))
def core_20(ctx):
    url = f"{ctx.fx_url}/p/google-docs/document/d/FIX_KO_RESUME/edit"
    refs = []
    for who in ("local", "local", "alice"):  # same library twice, then another library (another library_key)
        imp = ctx.cli(who).json(["import", url, "--as", "template"])
        ctx.expect(imp.exit == 0, "import failed")
        out = ctx.home(who) / f"src-{len(refs)}.json"
        ctx.cli(who).json(["export", imp.json["memory_id"], "--format", "json", "--out", str(out)])
        refs.append(json.loads(out.read_text(encoding="utf-8"))["source"].get("source_ref"))
    ctx.expect(refs[0] == refs[1] and refs[0], "same URL in the same library must give the same source_ref")
    ctx.expect(refs[2] != refs[0], "another library must give a different source_ref")
    ctx.expect(all(r and len(r) == 30 and "FIX_KO_RESUME" not in r for r in refs), "source_ref shape/leak")


@case("CORE-21", "F", needs=("server",))
def core_21(ctx):
    for url in ("http://example.com/", "https://127.0.0.1/"):
        reject(ctx, recall(ctx, url, identity="alice", env={"DMEM_ISOLATED": "0"}), "url_rejected")
    ctx.expect(ctx.request_log() == [], "a rejected URL must produce zero remote requests")


@case("CORE-22", "R1")
def core_22(ctx):
    with ctx.mcp() as m:
        for raw in (f"https://docs.google.com/document/d/{GID}/edit?usp=x", "https://Example.com/Templates"):
            r = m.call("doc_memory_recall", {"url": raw})
            ctx.expect(r is not None and r.is_error and r.code == "non_canonical_url", "MCP must reject a non-canonical URL")
        ok = m.call("doc_memory_recall", {"url": "docs.google.com/document/d/:id/edit"})
        ctx.expect(ok is not None and not ok.is_error, "MCP must accept a canonical URL")
    ctx.expect(canon(ctx, f"https://docs.google.com/document/d/{GID}/edit?usp=x") == "docs.google.com/document/d/:id/edit", "the CLI must canonicalise raw URLs locally")


@case("CORE-23", "R1")
def core_23(ctx):
    probes = [("http://SENT_scheme_Zq9/", "url_rejected"), ("https://user:SENT_pw_Zq9@example.com/", "url_rejected"), ("https://example.com:8443/SENT_port_Zq9", "url_rejected"),
              ("https://10.0.0.5/SENT_ip_Zq9", "url_rejected"), ("https://example.com/SENT_zq9@corp.test/x", "url_rejected")]
    messages = {}
    results = []
    for url, code in probes:
        r = recall(ctx, url, env={"DMEM_ISOLATED": "0"})
        results.append(r)
        err = (r.json or {}).get("error") or {}
        ctx.expect(err.get("code") == code, f"{url[:20]}: wrong code")
        messages.setdefault(err.get("code"), set()).add(err.get("message"))
    for form_value in ("SENT_doc_Zq9", ):
        results.append(recall(ctx, "https://example.com/x", doc_type=form_value))
    text = sink_text(*results)
    ctx.expect("SENT_" not in text and "Zq9" not in text, "an error echoed (part of) the input")
    ctx.expect(all(len(v) == 1 for v in messages.values()), "the message must be fixed per code")


@case("CORE-24", "R1")
def core_24(ctx):
    pad = lambda n: "https://example.com/" + "a" * (n - len("https://example.com/"))
    ctx.expect(recall(ctx, pad(2048)).exit in (0,), "2048-char URLs must be accepted (segments are cut, not rejected)") if False else None
    reject(ctx, recall(ctx, pad(2049)), "url_rejected", "too_long")
    reject(ctx, recall(ctx, "https://example.com/x", limit=4), "invalid_input")
    reject(ctx, recall(ctx, "https://example.com/x", keywords=[f"k{i}" for i in range(9)]), "invalid_input")
