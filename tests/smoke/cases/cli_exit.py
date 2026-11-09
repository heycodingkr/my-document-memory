"""CLI-26: the exit code table (docs/test/tool-forms/cli-form.md, docs/spec/cli.md section 3).

Every code that can be provoked from the outside is provoked and compared with the table: 0 success (an empty result is success), 2 usage/input,
3 authentication needed, 4 consent/licence/conflict, 5 network/server/search provider unavailable, 6 rate limited, 7 not found.
Code 1 (unexpected error) cannot be provoked on purpose and is not tested here.
"""
import json

from dmtest.runner import case


@case("CLI-26", "R1", needs=("server", "hooks", "fixtures"))
def cli_26(ctx):
    ctx.search_provider("fixture")
    ctx.load_library("shr-cat", identity="alice")
    unknown = ctx.cli("alice").json(["recall", "--stdin"], stdin=json.dumps({"url": "example.com/nothing-here", "doc_type": "proposal"}))
    ctx.expect(unknown.exit == 0 and unknown.json["hints"] == [], f"0: an empty result is a success (exit {unknown.exit})")
    usage = ctx.cli("alice").json(["recall"])
    ctx.expect(usage.exit == 2, f"2: a missing argument is a usage error (exit {usage.exit})")
    bad_enum = ctx.cli("alice").json(["publish", "fx_s5", "--visibility", "everyone"])
    ctx.expect(bad_enum.exit == 2 and bad_enum.code == "invalid_input", f"2: an out-of-vocabulary value is exit 2 (exit {bad_enum.exit})")
    anon_write = ctx.cli("anon").json(["publish", "fx_s1", "--visibility", "private"])
    ctx.expect(anon_write.exit == 3 and anon_write.code == "auth_required", f"3: an anonymous write needs authentication (exit {anon_write.exit})")
    no_consent = ctx.cli("alice").json(["publish", "fx_s5", "--visibility", "public", "--license", "CC-BY-4.0"])
    ctx.expect(no_consent.exit == 4 and no_consent.code == "consent_required", f"4: a publish without consent (exit {no_consent.exit})")
    forbidden = ctx.cli("bob").json(["copy", "fx_s3", "--copy-mode", "full"])
    ctx.expect(forbidden.exit == 4 and forbidden.code == "license_forbids", f"4: a copy mode above the licence ceiling (exit {forbidden.exit})")
    no_provider = ctx.cli("bob", {"DMEM_SEARCH_PROVIDER": "none"}).json(["web", "search", "이력서"])
    ctx.expect(no_provider.exit == 5 and no_provider.code == "search_unavailable", f"5: no search provider configured (exit {no_provider.exit})")
    limited = ctx.cli("bob").json(["web", "search", "__mode:429"])
    ctx.expect(limited.exit == 6 and limited.code == "rate_limited", f"6: the provider answers 429 (exit {limited.exit})")
    missing = ctx.cli("bob").json(["expand", "fx_does_not_exist", "--level", "1"])
    ctx.expect(missing.exit == 7 and missing.code == "not_found", f"7: a missing (or invisible) memory (exit {missing.exit})")
    private = ctx.cli("bob").json(["expand", "fx_s5", "--level", "1"])
    ctx.expect(private.exit == 7 and private.stdout == missing.stdout.replace("fx_does_not_exist", "fx_s5"), "7: another user's private memory answers like a missing one")
