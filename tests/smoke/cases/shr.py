"""SHR-01..SHR-21: sharing, copying, licences and visibility (docs/test/functional-tests.md, docs/spec/sharing.md).

All cases run on the SHR-CAT fixture (docs/test/fixtures.md section 3) in server mode: S1 public CC-BY, S2 public CC-BY-SA, S3 public fetched/unknown (structure only),
S4 team acme, S5 private (alice), S6 private (bob), S7 public proprietary-structure-only, S8 private with personal data, S9 bob's private near-twin of S1.
Memory ids are `fx_s1`..`fx_s9`. `__test approve-all` stands for the fixture review worker.
"""
import json

from dmtest.runner import case
from .util import recall, reject

SERVER = ("server", "hooks")
PUBLIC = {"s1", "s2", "s3", "s7"}


def cat(ctx):
    ctx.load_library("shr-cat", identity="alice")


def short(memory_id):
    return memory_id.removeprefix("fx_")


def search(ctx, who, scope=None, **filters):
    args = ["search", "--limit", "20"]
    if scope:
        args += ["--scope", scope]
    for key, value in filters.items():
        args += [f"--{key.replace('_', '-')}", str(value)]
    return ctx.cli(who).json(args)


def found(r):
    return {short(item["memory_id"]) for item in (r.json or {}).get("results", [])}


def item(r, name):
    return next((x for x in (r.json or {}).get("results", []) if short(x["memory_id"]) == name), None)


def publish(ctx, who, memory_id, visibility="public", license=None, consent=True):
    args = ["publish", memory_id, "--visibility", visibility]
    if license:
        args += ["--license", license]
    if consent:
        args.append("--consent")
    return ctx.cli(who).json(args)


def approve(ctx):
    ctx.cli("alice").json(["__test", "approve-all"])


def copy(ctx, who, memory_id, *extra):
    return ctx.cli(who).json(["copy", memory_id, *extra])


def expand(ctx, who, memory_id, level=1):
    return ctx.cli(who).json(["expand", memory_id, "--level", str(level)])


def writes(ctx):
    return [entry for entry in ctx.request_log() if entry["write"]]


def has_prose(ctx, text):
    """A structure-only result must hold none of the fixtures' prose sentinels (PROSE_SENTINEL_S1/S3/S9 and the corpus's PROSE_SENTINEL_1..)."""
    return "PROSE_SENTINEL" in text


@case("SHR-01", "F", needs=SERVER)
def shr_01(ctx):
    cat(ctx)
    r = publish(ctx, "alice", "fx_s5", "public", "CC-BY-4.0")
    ctx.expect(r.exit == 0 and r.json["review_state"] == "queued", f"a public publish is queued first: {r.json and r.json.get('review_state')}")
    ctx.expect("s5" not in found(search(ctx, "anon", "public")), "a queued item must not be public yet")
    approve(ctx)
    pub = item(search(ctx, "anon", "public"), "s5")
    ctx.expect(pub is not None, "after approval anon finds S5 in the public search")
    source = (pub or {}).get("source", {})
    ctx.expect(source.get("author_handle") == "alice" and source.get("license") == "CC-BY-4.0" and isinstance((pub or {}).get("version"), int), f"author, licence and version are shown: {source}")
    consents = ctx.cli("alice").json(["__test", "consents"]).json["consents"]
    mine = [c for c in consents if c["memory_id"] == "fx_s5"]
    ctx.expect(len(mine) == 1 and mine[0]["consent_version"] == "share-v1" and mine[0]["visibility"] == "public" and mine[0].get("at") and mine[0].get("version") == 1,
               f"the server must keep one consent record (version, time, target): {mine}")


@case("SHR-02", "F", needs=SERVER)
def shr_02(ctx):
    cat(ctx)
    before = len(writes(ctx))
    reject(ctx, publish(ctx, "alice", "fx_s5", "public", "CC-BY-4.0", consent=False), "consent_required", exit_code=4)
    ctx.expect(len(writes(ctx)) == before, "a publish without consent must not send a write request")
    ctx.expect("s5" not in found(search(ctx, "anon", "public")), "nothing was published")


@case("SHR-03", "F", needs=SERVER)
def shr_03(ctx):
    cat(ctx)
    before = len(writes(ctx))
    reject(ctx, publish(ctx, "alice", "fx_s5", "public", None), "invalid_input")
    reject(ctx, publish(ctx, "alice", "fx_s5", "public", "GPL-3.0"), "invalid_input")
    ctx.expect(len(writes(ctx)) == before, "an invalid licence must not send a write request")


@case("SHR-04", "F", needs=SERVER)
def shr_04(ctx):
    cat(ctx)
    r = publish(ctx, "alice", "fx_s8", "public", "CC-BY-4.0")
    ctx.expect(r.exit == 0 and r.json["review_state"] == "rejected" and "personal_data" in r.json["reasons"], f"a reference with personal data is rejected: {r.json}")
    approve(ctx)
    ctx.expect("s8" not in found(search(ctx, "anon", "public")), "the rejected item must not appear in the public catalogue")


@case("SHR-05", "F", needs=SERVER)
def shr_05(ctx):
    cat(ctx)
    ctx.cli("alice").json(["__test", "patch", "fx_s5", json.dumps({"l2_text": ctx.sentinels.value("api_key", 1)})])  # a secret slipped into the stored template
    r = publish(ctx, "alice", "fx_s5", "public", "CC-BY-4.0")
    ctx.expect(r.exit == 0 and r.json["review_state"] == "rejected" and "secret" in r.json["reasons"], f"a secret in the template must reject the publication: {r.json}")
    approve(ctx)
    ctx.expect("s5" not in found(search(ctx, "anon", "public")), "no secret may reach the public catalogue")
    ctx.expect(not ctx.scan_sinks(("anon", "bob", "carol"), families=("api_key",), server=False), "the secret sentinel must not appear in any other identity's sink")


@case("SHR-06", "F", needs=SERVER)
def shr_06(ctx):
    cat(ctx)
    r = publish(ctx, "alice", "fx_s4", "team", "CC-BY-4.0")
    ctx.expect(r.exit == 0 and r.json["review_state"] == "approved" and r.json["visibility"] == "team", f"team sharing needs no public review: {r.json}")
    ctx.expect("s4" in found(search(ctx, "carol", "team")), "carol (acme) must see the team item")
    ctx.expect(expand(ctx, "carol", "fx_s4").exit == 0, "carol can expand it")
    ctx.expect(copy(ctx, "carol", "fx_s4").exit == 0, "carol can copy it")
    for who in ("bob", "anon"):
        ctx.expect("s4" not in found(search(ctx, who, "team")) and "s4" not in found(search(ctx, who, "all")), f"{who} must not see the team item in a search")
        reject(ctx, expand(ctx, who, "fx_s4"), "not_found", exit_code=7)
        reject(ctx, copy(ctx, who, "fx_s4"), "not_found", exit_code=7)
        hints = recall(ctx, "example.com/team/quote", identity=who, doc_type="quote", locale="ko-KR")
        ctx.expect("s4" not in {short(h["memory_id"]) for h in hints.json["hints"]}, f"{who} must not get the team item from recall")


@case("SHR-07", "F", needs=SERVER)
def shr_07(ctx):
    cat(ctx)
    expected = {("anon", "public"): PUBLIC, ("anon", "all"): PUBLIC,
                ("bob", "mine"): {"s6", "s9"}, ("bob", "team"): set(), ("bob", "public"): PUBLIC, ("bob", "all"): PUBLIC | {"s6", "s9"},
                ("carol", "mine"): set(), ("carol", "team"): {"s4"}, ("carol", "public"): PUBLIC, ("carol", "all"): PUBLIC | {"s4"},
                ("alice", "mine"): {"s1", "s2", "s3", "s4", "s5", "s7", "s8"}}
    for (who, scope), want in expected.items():
        r = search(ctx, who, scope)
        ctx.expect(r.exit == 0 and found(r) == want, f"{who}/{scope}: expected {sorted(want)}, got {sorted(found(r))}")
    box = ctx.target.sandbox(server=False)  # local mode
    try:
        saved = box.cli("local").json(["save", "--kind", "template", "--title", "mine", "--doc-type", "memo", "--locale", "ko-KR", "--provider", "markdown", "--stdin", "--format", "markdown"], stdin="# 메모\n\n본문입니다")
        ctx.expect(saved.exit == 0, "local save")
        local = box.cli("local").json(["search", "--scope", "mine"])
        ctx.expect(local.exit == 0 and len(local.json["results"]) == 1, "local mode searches its own library")
        for scope in ("team", "public"):
            r = box.cli("local").json(["search", "--scope", scope])
            ctx.expect(r.exit == 0 and r.json["results"] == [] and r.json["reason"] == "scope_unavailable_local", f"local/{scope}: expected scope_unavailable_local")
    finally:
        box.close()


@case("SHR-08", "F", needs=SERVER)
def shr_08(ctx):
    cat(ctx)
    ctx.expect(found(search(ctx, "bob", "public", license="CC-BY-4.0")) == {"s1"}, "licence filter")
    ctx.expect(found(search(ctx, "bob", "public", doc_type="quote")) == {"s3", "s7"}, "doc_type filter")
    ctx.expect(found(search(ctx, "bob", "public", provider="html")) == {"s1", "s3", "s7"}, "provider filter")
    ctx.expect(found(search(ctx, "bob", "public", locale="ko-KR")) == PUBLIC, "locale filter")
    first = search(ctx, "bob", "public")
    ctx.schema_ok(first.json, "doc_memory_search", "SearchResult")
    ctx.expect(first.json["remote"] is True and search(ctx, "alice", "team").json["remote"] is True and search(ctx, "alice", "mine").json["remote"] is False, "remote is true for public/team and false for mine")
    for entry in first.json["results"]:
        ctx.expect({"memory_id", "version", "kind", "title", "form", "source", "visibility"} <= set(entry), f"SearchItem fields missing in {sorted(entry)}")
    again = [short(x["memory_id"]) for x in search(ctx, "bob", "public").json["results"]]
    ctx.expect(again == [short(x["memory_id"]) for x in first.json["results"]] and len(again) == 4, "the same query must repeat in the same order")
    page1 = ctx.cli("bob").json(["search", "--scope", "public", "--limit", "2"])
    cursor = page1.json.get("next_cursor")
    ctx.expect(len(page1.json["results"]) == 2 and cursor, "the first page has 2 items and a cursor")
    page2 = ctx.cli("bob").json(["search", "--scope", "public", "--limit", "2", "--cursor", cursor or "x"])
    pages = [short(x["memory_id"]) for x in page1.json["results"] + page2.json.get("results", [])]
    ctx.expect(sorted(pages) == sorted(PUBLIC) and len(set(pages)) == 4, f"two pages must cover the four public items without repeats: {pages}")


@case("SHR-09", "F", needs=SERVER)
def shr_09(ctx):
    cat(ctx)
    secret = ctx.sentinels.value("api_key", 2)
    before = len(ctx.request_log())
    reject(ctx, ctx.cli("bob").json(["search", secret, "--scope", "public"]), "secret_detected")
    ctx.expect(len(ctx.request_log()) == before, "a secret in a remote query must never be sent")
    box = ctx.target.sandbox(server=False)
    try:
        r = box.cli("local").json(["search", secret, "--scope", "mine"])
        ctx.expect(r.exit == 0 or (r.json or {}).get("error", {}).get("code") == "secret_detected", "a local query is either searched locally or rejected, never sent")
        ctx.expect(box.request_log() == [], "local mode must make no network request")
    finally:
        box.close()


@case("SHR-10", "F", needs=SERVER)
def shr_10(ctx):
    cat(ctx)
    before = expand(ctx, "alice", "fx_s1", 2).stdout
    for memory, level in (("fx_s1", 1), ("fx_s1", 2), ("fx_s3", 2)):
        r = expand(ctx, "bob", memory, level)
        source = (r.json or {}).get("source", {})
        ctx.expect(r.exit == 0 and r.json["untrusted"] is True and source.get("author_handle") == "alice" and source.get("license") and isinstance(r.json.get("version"), int),
                   f"{memory} level {level}: author, licence, version and the untrusted flag are required")
        if memory == "fx_s3":
            ctx.expect(not has_prose(ctx, r.stdout), "a structure-only item must not expose body prose at level 2")
    ctx.expect(expand(ctx, "alice", "fx_s1", 2).stdout == before, "reading must not change the source memory (version, updated_at, content)")


@case("SHR-11", "F", needs=SERVER)
def shr_11(ctx):
    cat(ctx)
    before = expand(ctx, "alice", "fx_s1", 2).stdout
    r = copy(ctx, "bob", "fx_s1")
    ctx.expect(r.exit == 0 and r.json["derived_from"] == {"memory_id": "fx_s1", "version": 1, "author_handle": "alice", "license": "CC-BY-4.0"}, f"derived_from keeps id, version, author and licence: {r.json and r.json.get('derived_from')}")
    ctx.expect(r.json["copy_policy_applied"] == "full" and r.json["visibility"] == "private", "a CC-BY copy is full and private")
    mine = search(ctx, "bob", "mine")
    ctx.expect(r.json["memory_id"] in {x["memory_id"] for x in mine.json["results"]}, "the copy lives in bob's own library")
    ctx.expect(r.json["memory_id"] not in {x["memory_id"] for x in search(ctx, "anon", "public").json["results"]}, "the copy is not public")
    ctx.expect(expand(ctx, "alice", "fx_s1", 2).stdout == before, "copying must not change the source (version, updated_at, content)")


@case("SHR-12", "F", needs=SERVER)
def shr_12(ctx):
    cat(ctx)
    r = copy(ctx, "bob", "fx_s3", "--copy-mode", "full")
    reject(ctx, r, "license_forbids", exit_code=4)
    ctx.expect((r.json or {}).get("error", {}).get("allowed_modes") == ["structure_only"], f"allowed_modes must list the permitted modes: {(r.json or {}).get('error')}")
    ok = copy(ctx, "bob", "fx_s3")
    ctx.expect(ok.exit == 0 and ok.json["copy_policy_applied"] == "structure_only", "the default mode follows the licence ceiling")
    body = expand(ctx, "bob", ok.json["memory_id"], 2)
    ctx.expect(body.exit == 0 and not has_prose(ctx, body.stdout), "the structure-only copy must hold no prose")


@case("SHR-13", "F", needs=SERVER)
def shr_13(ctx):
    cat(ctx)
    copies = {name: copy(ctx, "bob", f"fx_{name}", "--title", f"변형 {name}").json["memory_id"] for name in ("s1", "s2", "s3", "s7")}  # a retitled copy is no duplicate of the public original
    ok = publish(ctx, "bob", copies["s1"], "public", "CC-BY-4.0")
    ctx.expect(ok.exit == 0 and ok.json["review_state"] == "queued", f"a CC-BY copy may be re-published as CC-BY: {ok.json}")
    reject(ctx, publish(ctx, "bob", copies["s2"], "public", "CC-BY-4.0"), "license_forbids", exit_code=4)
    sa = publish(ctx, "bob", copies["s2"], "public", "CC-BY-SA-4.0")
    ctx.expect(sa.exit == 0 and sa.json["review_state"] == "queued", f"a CC-BY-SA copy may be re-published as CC-BY-SA: {sa.json}")
    for name in ("s3", "s7"):
        for lic in ("CC-BY-4.0", "CC0-1.0"):
            reject(ctx, publish(ctx, "bob", copies[name], "public", lic), "license_forbids", exit_code=4)


@case("SHR-14", "F", needs=SERVER)
def shr_14(ctx):
    cat(ctx)
    mine = copy(ctx, "bob", "fx_s1").json["memory_id"]
    r = publish(ctx, "alice", "fx_s1", "private", None, consent=False)
    ctx.expect(r.exit == 0 and r.json["visibility"] == "private", "un-publishing needs no consent")
    ctx.expect("s1" not in found(search(ctx, "anon", "public")), "anon search must not list the withdrawn item")
    ctx.expect("s1" not in {short(h["memory_id"]) for h in recall(ctx, "www.example.org/pages/resume-ko.html", identity="anon", doc_type="resume", locale="ko-KR").json["hints"]}, "anon recall must not return it")
    reject(ctx, expand(ctx, "anon", "fx_s1"), "not_found", exit_code=7)
    reject(ctx, copy(ctx, "anon", "fx_s1"), "not_found", exit_code=7)
    kept = expand(ctx, "bob", mine, 2)
    ctx.expect(kept.exit == 0, "bob's earlier copy stays and stays readable")


@case("SHR-15", "F", needs=SERVER)
def shr_15(ctx):
    cat(ctx)
    first = copy(ctx, "bob", "fx_s2").json["memory_id"]
    second = copy(ctx, "bob", "fx_s2").json["memory_id"]
    ctx.cli("alice").json(["__test", "takedown", "fx_s2"])
    ctx.expect(all("s2" not in found(search(ctx, who, "all")) for who in ("anon", "bob", "carol")), "a taken-down item disappears from every other user's search")
    reject(ctx, expand(ctx, "bob", "fx_s2"), "not_found", exit_code=7)
    reject(ctx, copy(ctx, "carol", "fx_s2"), "not_found", exit_code=7)
    codes = {w["code"] if isinstance(w, dict) else w for w in expand(ctx, "bob", first, 1).json.get("warnings", [])}
    ctx.expect("origin_taken_down" in codes, f"the copy must warn that its origin was taken down: {sorted(codes)}")
    again = publish(ctx, "bob", second, "public", "CC-BY-SA-4.0")
    blocked = (again.json or {}).get("error", {}).get("code") == "license_forbids" or (again.json or {}).get("reasons") == ["takedown_match"] or "takedown_match" in (again.json or {}).get("reasons", [])
    ctx.expect(blocked, f"re-publishing a derivative of a taken-down item must be refused: {again.json}")


@case("SHR-16", "F", needs=SERVER)
def shr_16(ctx):
    cat(ctx)
    operations = {
        "expand": lambda mid: ctx.cli("bob").json(["expand", mid]),
        "copy": lambda mid: ctx.cli("bob").json(["copy", mid]),
        "publish": lambda mid: ctx.cli("bob").json(["publish", mid, "--visibility", "private"]),
        "delete": lambda mid: ctx.cli("bob").json(["delete", mid, "--yes"]),
        "outcome": lambda mid: ctx.cli("bob").json(["outcome", mid, "success"]),
    }
    for name, call in operations.items():
        private, missing = call("fx_s5"), call("fx_does_not_exist_zz")
        reject(ctx, private, "not_found", exit_code=7)
        reject(ctx, missing, "not_found", exit_code=7)
        ctx.expect(private.stdout == missing.stdout, f"{name}: a private item and a missing id must answer byte for byte alike")
        ctx.expect("fx_s5" not in private.stdout + private.stderr and "fx_does_not_exist_zz" not in missing.stdout + missing.stderr, f"{name}: the id must not be echoed")


@case("SHR-17", "F", needs=SERVER)
def shr_17(ctx):
    cat(ctx)
    before = expand(ctx, "alice", "fx_s1", 2).stdout
    reject(ctx, ctx.cli("bob").json(["publish", "fx_s1", "--visibility", "private"]), "not_found", exit_code=7)
    reject(ctx, ctx.cli("bob").json(["delete", "fx_s1", "--yes"]), "not_found", exit_code=7)
    ctx.expect(expand(ctx, "alice", "fx_s1", 2).stdout == before and "s1" in found(search(ctx, "anon", "public")), "bob's attempts must leave S1 untouched and public")


@case("SHR-18", "F", needs=SERVER)
def shr_18(ctx):
    cat(ctx)
    before = len(writes(ctx))
    reject(ctx, ctx.cli("anon").json(["publish", "fx_s1", "--visibility", "private"]), "auth_required", exit_code=3)
    reject(ctx, ctx.cli("anon").json(["outcome", "rcpt_x", "success"]), "auth_required", exit_code=3)
    ctx.expect(len(writes(ctx)) == before, "anonymous calls must send no write request")
    r = copy(ctx, "anon", "fx_s1")
    ctx.expect(r.exit == 0 and "receipt_id" not in r.json and r.json["derived_from"]["author_handle"] == "alice", f"an anonymous copy goes to the local library without a receipt: {r.json}")
    ctx.expect(len(ctx.cli("anon").json(["list"]).json["results"]) == 1, "the copy is in the anonymous caller's local library")


@case("SHR-19", "F", needs=SERVER)
def shr_19(ctx):
    cat(ctx)
    twin = copy(ctx, "alice", "fx_s1").json["memory_id"]  # identical content hash to the public S1
    first = publish(ctx, "alice", twin, "public", "CC-BY-4.0")
    ctx.expect(first.exit == 0 and first.json["review_state"] == "rejected" and "duplicate" in first.json["reasons"], f"a copy of an already public item is a duplicate: {first.json}")
    for _ in range(9):  # 10 publishes in the hour
        publish(ctx, "alice", twin, "public", "CC-BY-4.0")
    reject(ctx, publish(ctx, "alice", twin, "public", "CC-BY-4.0"), "rate_limited", exit_code=6)


@case("SHR-20", "F", needs=SERVER)
def shr_20(ctx):
    cat(ctx)
    b = copy(ctx, "bob", "fx_s1", "--title", "밥의 변형").json["memory_id"]
    ctx.expect(publish(ctx, "bob", b, "public", "CC-BY-4.0").json["review_state"] == "queued", "bob publishes his derivative")
    approve(ctx)
    c = copy(ctx, "carol", b)
    ctx.expect(c.exit == 0 and c.json["derived_from"] == {"memory_id": b, "version": 1, "author_handle": "alice", "license": "CC-BY-4.0"},
               f"the chain keeps the immediate source and the ORIGINAL author and licence: {c.json}")
    cm = copy(ctx, "carol", b, "--title", "캐럴의 변형").json["memory_id"]  # retitled: a verbatim copy of a public item would be a duplicate
    ctx.expect(publish(ctx, "carol", cm, "public", "CC-BY-4.0").json["review_state"] == "queued", "carol publishes her derivative")
    approve(ctx)
    public = expand(ctx, "anon", cm, 1)
    source = (public.json or {}).get("source", {})
    ctx.expect(public.exit == 0 and source.get("author_handle") == "carol" and source.get("derived_from") == {"memory_id": b, "version": 1, "author_handle": "alice", "license": "CC-BY-4.0"},
               f"the public attribution must name the original author: {source}")


@case("SHR-21", "F", needs=SERVER)
def shr_21(ctx):
    cat(ctx)
    before = expand(ctx, "alice", "fx_s1", 2).stdout
    r = publish(ctx, "bob", "fx_s9", "public", "CC-BY-4.0")
    ctx.expect(r.exit == 0 and r.json["review_state"] == "queued", f"a different-content twin in the same catalog scope is a separate contribution: {r.json}")
    approve(ctx)
    pub = search(ctx, "anon", "public")
    s1, s9 = item(pub, "s1"), item(pub, "s9")
    ctx.expect(s1 is not None and s9 is not None and s1["memory_id"] != s9["memory_id"], "both contributions are searchable under different ids")
    ctx.expect((s1 or {}).get("source", {}).get("author_handle") == "alice" and (s9 or {}).get("source", {}).get("author_handle") == "bob", "each keeps its own author")
    ctx.expect(expand(ctx, "alice", "fx_s1", 2).stdout == before, "S1 must be untouched: no merge, no overwrite")
    c = copy(ctx, "carol", "fx_s9")
    ctx.expect(c.exit == 0 and c.json["derived_from"]["memory_id"] == "fx_s9" and c.json["derived_from"]["version"] == (s9 or {}).get("version"), f"a copy pins the published version of S9: {c.json}")
