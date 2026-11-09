"""Helpers shared by the case modules."""
import json


def recall(ctx, url, identity="local", env=None, **fields):
    """recall through the CLI with the URL on stdin (so sentinel-bearing URLs never appear in argv)."""
    return ctx.cli(identity, env).json(["recall", "--stdin"], stdin=json.dumps({"url": url, **fields}))


def canon(ctx, url, **kw):
    r = recall(ctx, url, **kw)
    return (r.json or {}).get("canonical_url") if r.exit == 0 else None


def provider_of(ctx, url, **kw):
    r = recall(ctx, url, **kw)
    return ((r.json or {}).get("form") or {}).get("provider") if r.exit == 0 else None


def reject(ctx, r, code, reason=None, exit_code=2):
    """The call must fail with this fixed error code (and reason) and exit code."""
    err = (r.json or {}).get("error") or {}
    ctx.expect(r.exit == exit_code and err.get("code") == code and (reason is None or err.get("reason") == reason),
               f"expected {code}/{reason} exit {exit_code}, got exit={r.exit} code={err.get('code')} reason={err.get('reason')}")


def save_md(ctx, text, kind="template", title="양식", doc_type="resume", locale="ko-KR", identity="local", extra=(), env=None, provider="markdown"):
    args = ["save", "--kind", kind, "--title", title, "--doc-type", doc_type, "--locale", locale, "--provider", provider, "--stdin", "--format", "markdown", *extra]
    return ctx.cli(identity, env).json(args, stdin=text)


def sink_text(*results):
    return "\n".join((getattr(r, "stdout", "") or "") + "\n" + (getattr(r, "stderr", "") or "") for r in results)
