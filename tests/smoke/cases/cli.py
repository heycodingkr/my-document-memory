"""CLI-04..CLI-17: dmem command surface cases from docs/test/tool-forms/cli-form.md."""
import json

from dmtest.builders import tpl01
from dmtest.runner import case
from .util import save_md


@case("CLI-04", "R1", needs=())
def cli_04(ctx):
    version = ctx.cli().run(["--version"])
    help_result = ctx.cli().run(["--help"])
    output = (version.stdout or "") + (version.stderr or "") + (help_result.stdout or "") + (help_result.stderr or "")
    commands = (
        "recall", "search", "list", "expand", "save", "web search", "web preview", "import", "copy",
        "publish", "delete", "outcome", "export", "status", "vocab", "leaderboard", "rank", "usage",
        "link", "unlink", "cache", "doctor", "install", "uninstall", "guide print", "browser-mcp",
    )
    ctx.expect(version.exit == 0 and "dmem " in (version.stdout or "").lower(), "--version exits 0 and prints the CLI version")
    ctx.expect(help_result.exit == 0 and all(name in (help_result.stdout or "") for name in commands),
               "--help exits 0 and names every command from cli.md section 2")
    ctx.expect(all(secret not in output for secret in ("DMEM_TOKEN=", "Bearer ", "sk-")),
               "version and help output must not contain a secret value")


def _schema_result(ctx, tool, result):
    body = result.json or {}
    ctx.expect(result.exit == 0 and isinstance(result.json, dict), f"{tool} CLI JSON call succeeds")
    ctx.schema_ok(body, tool)
    return body


@case("CLI-05", "R1", needs=("server", "hooks", "fixtures"))
def cli_05(ctx):
    ctx.load_library("shr-cat", identity="alice")
    ctx.search_provider("fixture")

    status = ctx.cli("anon").json(["status"])
    _schema_result(ctx, "doc_memory_status", status)

    recall = ctx.cli("alice").json(["recall", "https://www.example.org/pages/resume-ko.html"])
    _schema_result(ctx, "doc_memory_recall", recall)

    search = ctx.cli("anon").json(["search", "--scope", "public"])
    _schema_result(ctx, "doc_memory_search", search)

    expanded = ctx.cli("anon").json(["expand", "fx_s1", "--level", "1"])
    _schema_result(ctx, "doc_memory_expand", expanded)

    saved = ctx.cli("alice").json(
        ["save", "--kind", "template", "--title", "CLI schema save", "--doc-type", "resume", "--locale", "ko-KR",
         "--provider", "markdown", "--stdin", "--format", "markdown"],
        stdin="# CLI schema save\n\n## Experience\nSchema fixture content.",
    )
    save_body = _schema_result(ctx, "doc_memory_save", saved)
    saved_id = save_body.get("memory_id") or "missing"

    preview_url = ctx.fx_url + "/pages/resume-ko.html"
    preview = ctx.cli("alice").json(["web", "preview", preview_url])
    preview_body = _schema_result(ctx, "doc_memory_web_preview", preview)

    imported = ctx.cli("alice").json(["import", "--preview", preview_body.get("preview_id", "missing"), "--as", "template"])
    _schema_result(ctx, "doc_memory_import", imported)

    copied = ctx.cli("bob").json(["copy", "fx_s1"])
    copy_body = _schema_result(ctx, "doc_memory_copy", copied)
    copied_id = copy_body.get("memory_id") or "missing"

    published = ctx.cli("alice").json(["publish", "fx_s5", "--visibility", "public", "--license", "CC-BY-4.0", "--consent"])
    _schema_result(ctx, "doc_memory_publish", published)

    deleted = ctx.cli("bob").json(["delete", copied_id, "--yes"])
    _schema_result(ctx, "doc_memory_delete", deleted)

    receipt_id = next((hint.get("receipt_id") for hint in (recall.json or {}).get("hints", []) if hint.get("receipt_id")), None)
    outcome = ctx.cli("alice").json(["outcome", receipt_id or "missing", "success"])
    _schema_result(ctx, "doc_memory_outcome", outcome)

    web_search = ctx.cli("anon").json(["web", "search", "resume"])
    _schema_result(ctx, "doc_memory_web_search", web_search)


@case("CLI-06", "R1", needs=())
def cli_06(ctx):
    bad_option = ctx.cli().run(["recall", "--definitely-not-an-option"])
    unknown_command = ctx.cli().run(["unknown-command"])
    ctx.expect(bad_option.exit == 2 and "usage" in (bad_option.stderr or "").lower(),
               "an invalid option exits 2 with usage text")
    ctx.expect(unknown_command.exit == 2 and "usage" in (unknown_command.stderr or "").lower(),
               "an unknown subcommand exits 2 with usage text")
    ctx.expect(ctx.request_log() == [], "invalid CLI input must make zero API or server requests")


@case("CLI-07", "R1", needs=())
def cli_07(ctx):
    from pathlib import Path

    markdown = Path(ctx.home()).parent / "cli-save.md"
    docx = Path(ctx.home()).parent / "cli-save.docx"
    markdown.parent.mkdir(parents=True, exist_ok=True)
    markdown.write_text("# CLI resume\n\n## Experience\nA Markdown file for the CLI case.\n", encoding="utf-8")
    docx.write_bytes(tpl01())

    def file_args(title, provider, path, *extra):
        return ["save", "--kind", "template", "--title", title, "--doc-type", "resume", "--locale", "ko-KR",
                "--provider", provider, "--file", str(path), *extra]

    before = ctx.cli().json(["list"])
    dry = ctx.cli().json(file_args("CLI markdown", "markdown", markdown, "--dry-run"))
    after_dry = ctx.cli().json(["list"])
    saved = ctx.cli().json(file_args("CLI markdown", "markdown", markdown))
    saved_body = saved.json or {}
    saved_id = saved_body.get("memory_id") or "missing"
    repeat = ctx.cli().json(file_args("CLI markdown", "markdown", markdown))
    docx_saved = ctx.cli().json(file_args("CLI docx", "docx", docx))
    conflict = ctx.cli().json(file_args("CLI markdown", "markdown", markdown, "--memory", saved_id, "--base-version", "2"))

    before_rows = (before.json or {}).get("results", [])
    after_rows = (after_dry.json or {}).get("results", [])
    ctx.expect(dry.exit == 0 and (dry.json or {}).get("dry_run") is True and (dry.json or {}).get("memory_id") is None,
               "--dry-run reports success without allocating a memory")
    ctx.expect(before.exit == 0 and after_dry.exit == 0 and len(before_rows) == len(after_rows),
               "--dry-run leaves the local library unchanged")
    ctx.expect(saved.exit == 0 and saved_body.get("visibility") == "private" and saved_body.get("version") == 1,
               "a Markdown file is saved privately as version 1")
    ctx.expect(docx_saved.exit == 0 and (docx_saved.json or {}).get("visibility") == "private",
               "a DOCX file is saved privately")
    ctx.expect(repeat.exit == 0 and (repeat.json or {}).get("created") is False and
               (repeat.json or {}).get("memory_id") == saved_id,
               "saving the same file again returns created=false for the same memory")
    ctx.expect(conflict.exit == 4 and (conflict.json or {}).get("error", {}).get("code") == "version_conflict",
               "a stale --memory plus --base-version update exits 4 with version_conflict")
