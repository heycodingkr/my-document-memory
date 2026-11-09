"""LIB-01..LIB-16: private library storage, versions, deletion and export."""
import hashlib
import json
import os
import stat
import threading
import zipfile
from pathlib import Path

from dmtest.builders import tpl01
from dmtest.runner import case
from .util import reject, save_md, sink_text


def _snapshot(root):
    """Return library file paths, bytes and modes, excluding transient logs."""
    root = root.resolve()
    rows = []
    if not root.exists():
        return rows
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix not in (".log", ".jsonl"):
            rows.append((str(path.relative_to(root)), path.read_bytes(), stat.S_IMODE(path.stat().st_mode)))
    return rows


def _save_args(title, *, kind="template", doc_type="resume", locale="ko-KR", provider="markdown", memory=None, base=None, extra=()):
    args = ["save", "--kind", kind, "--title", title, "--doc-type", doc_type, "--locale", locale, "--provider", provider]
    if memory is not None:
        args += ["--memory", memory]
    if base is not None:
        args += ["--base-version", str(base)]
    args += list(extra)
    return args


@case("LIB-01", "R1", needs=())
def lib_01(ctx):
    source = ctx.home().parent / "resume-ko.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# 이력서\n\n## 경력\n경력과 성과를 기록합니다.\n\n## 학력\n학력을 기록합니다.\n", encoding="utf-8")
    dry = ctx.cli().json(_save_args("resume-ko", extra=["--file", str(source), "--dry-run"]))
    saved = ctx.cli().json(_save_args("resume-ko", extra=["--file", str(source)]))
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    original = Path(ctx.home()) / "originals" / digest
    ctx.expect(dry.exit == 0 and (dry.json or {}).get("dry_run") is True and (dry.json or {}).get("memory_id") is None,
               "dry-run must preview without allocating a memory")
    ctx.expect(saved.exit == 0 and (saved.json or {}).get("visibility") == "private" and (saved.json or {}).get("version") == 1,
               "uploaded template must be private version 1")
    ctx.expect(original.is_file() and stat.S_IMODE(original.stat().st_mode) == 0o600 if original.exists() else False,
               "the original must be preserved with mode 0600")


@case("LIB-02", "R1", needs=())
def lib_02(ctx):
    source = ctx.home().parent / "tpl01-monthly-report.docx"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(tpl01())
    saved = ctx.cli().json(_save_args("monthly-report", doc_type="report", provider="docx", extra=["--file", str(source)]))
    memory_id = (saved.json or {}).get("memory_id")
    expanded = ctx.cli().json(["expand", memory_id or "missing", "--level", "2"]) if memory_id else None
    content = (expanded.json or {}) if expanded else {}
    structure = ((content.get("l2") or {}).get("structure") or {})
    blocks = structure.get("blocks") or []
    headings = [b.get("text") for b in blocks if b.get("type") == "heading" and b.get("text") != "월간 운영 보고서"]  # the document title is not a section
    tables = [b for b in blocks if b.get("type") == "table"]
    table = tables[0] if tables else {}
    rows = table.get("rows") or []
    ctx.expect(saved.exit == 0 and memory_id is not None and expanded is not None and expanded.exit == 0,
               "TPL-01 must save and expand at level 2")
    ctx.expect(headings == ["요약", "지표", "위험", "요청"], "TPL-01 section order must be 요약, 지표, 위험, 요청")
    ctx.expect(len(tables) == 1 and len(rows) == 2 and all(len(row) == 3 for row in rows),
               "TPL-01 must preserve one 2x3 table")
    listed = ctx.cli().json(["list", "--kind", "template", "--doc-type", "report"])
    results = (listed.json or {}).get("results") or []
    ctx.expect(listed.exit == 0 and any(m.get("memory_id") == memory_id for m in results),
               "TPL-01 must appear in the personal template list")


@case("LIB-03", "R1", needs=())
def lib_03(ctx):
    home = ctx.home()
    before_list = ctx.cli().json(["list"])
    before_rows = (before_list.json or {}).get("results") or []
    before_files = _snapshot(home)
    dry = save_md(ctx, "# dry-run\n\nNo changes should be stored.", title="dry-run", extra=["--dry-run"])
    after_list = ctx.cli().json(["list"])
    after_rows = (after_list.json or {}).get("results") or []
    after_files = _snapshot(home)
    ctx.expect(dry.exit == 0 and (dry.json or {}).get("dry_run") is True and (dry.json or {}).get("memory_id") is None,
               "dry-run must return dry_run=true and no memory_id")
    ctx.expect(before_list.exit == 0 and after_list.exit == 0 and len(before_rows) == len(after_rows),
               "dry-run must not change the library list count")
    ctx.expect(before_files == after_files, "dry-run must not change DMEM_HOME files")


@case("LIB-04", "R1", needs=())
def lib_04(ctx):
    text = "# Same template\n\nA repeat save must be idempotent."
    first = save_md(ctx, text, title="same-template")
    second = save_md(ctx, text, title="same-template")
    a, b = first.json or {}, second.json or {}
    listed = ctx.cli().json(["list"])
    rows = (listed.json or {}).get("results") or []
    versions = [ctx.cli().json(["expand", a.get("memory_id", "missing"), "--version", str(n), "--level", "1"])
                for n in (1, 2)]
    ctx.expect(first.exit == 0 and second.exit == 0 and b.get("created") is False,
               "saving identical content in the same scope must reuse the memory")
    ctx.expect(a.get("memory_id") is not None and b.get("memory_id") == a.get("memory_id") and b.get("version") == a.get("version"),
               "repeat save must return the same memory and version")
    ctx.expect(listed.exit == 0 and sum(m.get("memory_id") == a.get("memory_id") for m in rows) == 1 and all(v.exit != 0 for v in versions[1:]),
               "idempotent save must leave only version 1")


@case("LIB-05", "R1", needs=())
def lib_05(ctx):
    first = save_md(ctx, "# Versioned\n\nOriginal content.", title="versioned")
    memory_id = (first.json or {}).get("memory_id")
    changed = ctx.cli().json(_save_args("versioned", memory=memory_id, base=1, extra=["--stdin", "--format", "markdown"]),
                             stdin="# Versioned\n\nSecond version.") if memory_id else None
    conflict = ctx.cli().json(_save_args("versioned", memory=memory_id, base=1, extra=["--stdin", "--format", "markdown"]),
                              stdin="# Versioned\n\nConflicting stale write.") if memory_id else None
    after_conflict = ctx.cli().json(["expand", memory_id or "missing", "--level", "1"]) if memory_id else None
    final = ctx.cli().json(_save_args("versioned", memory=memory_id, base=2, extra=["--stdin", "--format", "markdown"]),
                           stdin="# Versioned\n\nThird version.") if memory_id else None
    ctx.expect(first.exit == 0 and memory_id is not None, "initial save must create version 1")
    ctx.expect(changed is not None and changed.exit == 0 and (changed.json or {}).get("version") == 2,
               "base_version 1 update must create version 2")
    reject(ctx, conflict, "version_conflict", exit_code=4) if conflict is not None else ctx.expect(False, "stale update must be rejected")
    ctx.expect(after_conflict is not None and after_conflict.exit == 0 and (after_conflict.json or {}).get("version") == 2,
               "version conflict must leave the current version unchanged")
    ctx.expect(final is not None and final.exit == 0 and (final.json or {}).get("version") == 3,
               "base_version 2 update must create version 3")


@case("LIB-06", "R1", needs=())
def lib_06(ctx):
    saved = save_md(ctx, "# Version lookup\n\nFirst version body.", title="version-lookup")
    memory_id = (saved.json or {}).get("memory_id")
    v1 = ctx.cli().json(["expand", memory_id or "missing", "--version", "1", "--level", "2"])
    absent = ctx.cli().json(["expand", memory_id or "missing", "--version", "99", "--level", "2"])
    l2 = ((v1.json or {}).get("l2") or {})
    reject(ctx, absent, "not_found", exit_code=7)
    ctx.expect(saved.exit == 0 and v1.exit == 0 and (v1.json or {}).get("version") == 1 and
               "First version body." in json.dumps(l2, ensure_ascii=False), "version 1 must return its original content")


@case("LIB-07", "R1", needs=())
def lib_07(ctx):
    docs, locales = ("resume", "quote", "report", "memo", "invoice"), ("ko-KR", "en-US", "ja-JP", "zh-CN", "de-DE")
    for doc in docs:
        for locale in locales:
            save_md(ctx, f"# {doc} {locale}\n\nUnique page {doc}-{locale}.", doc_type=doc, locale=locale, title=f"{doc}-{locale}")
    ids, cursor, pages, page_rows = [], None, [], []
    while True:
        args = ["search", "--scope", "mine", "--limit", "10"] + (["--cursor", cursor] if cursor else [])
        r = ctx.cli().json(args)
        rows = (r.json or {}).get("results") or []
        pages.append(len(rows)); page_rows.extend(rows); ids.extend(m.get("memory_id") for m in rows)
        cursor = (r.json or {}).get("next_cursor")
        if not cursor or r.exit != 0: break
    sorted_rows = sorted(sorted(page_rows, key=lambda m: m.get("memory_id", "")), key=lambda m: m.get("updated_at", ""), reverse=True)
    ctx.expect(pages == [10, 10, 5] and len(ids) == len(set(ids)) == 25, "25 records must page as 10/10/5 with no duplicates or omissions")
    ctx.expect(cursor is None and [m.get("memory_id") for m in page_rows] == [m.get("memory_id") for m in sorted_rows],
               "last cursor must be null and order updated_at descending then memory_id")
    for flag, expected in (("--kind", "template"), ("--doc-type", "resume"), ("--locale", "ko-KR"), ("--provider", "markdown")):
        filtered = ctx.cli().json(["search", "--scope", "mine", flag, expected, "--limit", "20"])
        rows = (filtered.json or {}).get("results") or []
        key = {"--kind": "kind", "--doc-type": "doc_type", "--locale": "locale", "--provider": "provider"}[flag]
        ctx.expect(filtered.exit == 0 and all((m.get("form") or {}).get(key) == expected if key != "kind" else m.get(key) == expected for m in rows),
                   f"{flag} filter must return only matching records")


@case("LIB-08", "R1", needs=("fixtures",))
def lib_08(ctx):
    ctx.search_provider("fixture")
    secrets = [ctx.sentinels.value(family, 1) for family in ("api_key", "jwt", "bearer", "private_key")]
    before = _snapshot(ctx.home())
    results = []
    for index, secret in enumerate(secrets):
        results.append(save_md(ctx, f"# secret {index}\n\n{secret}", title=f"secret-{index}"))
        results.append(ctx.cli().json(["search", secret]))
        results.append(ctx.cli().json(["web", "search", secret]))
    for r in results:
        reject(ctx, r, "secret_detected")
    text = sink_text(*results)
    ctx.expect(all(value not in text for value in secrets), "secret values must not appear in CLI output")
    ctx.expect(before == _snapshot(ctx.home()), "secret rejection must leave the library unchanged")
    ctx.expect(not ctx.scan_values(secrets), "secret values must not appear in library or logs")


@case("LIB-09", "F", needs=())
def lib_09(ctx):
    values = [ctx.sentinels.value("email", 1), *(ctx.sentinels.value("phone", i) for i in range(1, 4)),
              *(ctx.sentinels.value("national_id", i) for i in range(1, 3)), ctx.sentinels.value("card"), ctx.sentinels.value("account")]
    saved = save_md(ctx, "# Template\n\n" + "\n\n".join(f"Contact {i}: {value}" for i, value in enumerate(values)), title="pii-template")
    memory_id = (saved.json or {}).get("memory_id")
    path = ctx.home().parent / "pii-template.json"
    exported = ctx.cli().json(["export", memory_id or "missing", "--format", "json", "--out", str(path)])
    data = path.read_text(encoding="utf-8") if path.is_file() else ""
    scrub = (saved.json or {}).get("scrub") or {}
    ctx.expect(saved.exit == 0 and memory_id is not None and scrub.get("pii_slotified", 0) >= len(values), "template PII must be slotified and counted")
    ctx.expect(exported.exit == 0 and all(value not in data for value in values), "exported template must contain none of the original PII")


@case("LIB-10", "F", needs=())
def lib_10(ctx):
    value = ctx.sentinels.value("email", 2)
    saved = save_md(ctx, f"Contact record: {value}", kind="reference", doc_type="other", title="private-reference")
    memory_id = (saved.json or {}).get("memory_id")
    path = ctx.home().parent / "reference.json"
    exported = ctx.cli().json(["export", memory_id or "missing", "--format", "json", "--out", str(path)])
    data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    ctx.expect(saved.exit == 0 and memory_id is not None and (saved.json or {}).get("visibility") == "private", "reference with PII must remain private")
    ctx.expect(exported.exit == 0 and data.get("contains_personal_data") is True and value in json.dumps(data, ensure_ascii=False),
               "reference PII must be preserved and marked in export JSON")


@case("LIB-11", "R1", needs=())
def lib_11(ctx):
    marker = "LIB_DELETE_SENTINEL_01"
    saved = save_md(ctx, f"# Delete me\n\n{marker}", title="delete-me")
    memory_id = (saved.json or {}).get("memory_id")
    before = _snapshot(ctx.home())
    no_confirm = ctx.cli().json(["delete", memory_id or "missing"])
    after_no_confirm = _snapshot(ctx.home())
    still_there = ctx.cli().json(["expand", memory_id or "missing", "--level", "2"])
    deleted = ctx.cli().json(["delete", memory_id or "missing", "--yes"])
    expanded = ctx.cli().json(["expand", memory_id or "missing", "--level", "2"])
    ctx.expect(saved.exit == 0 and no_confirm.exit == 2 and before == after_no_confirm and still_there.exit == 0,
               "delete without --yes must fail without changing the memory")
    ctx.expect(deleted.exit == 0 and (deleted.json or {}).get("deleted") is True, "confirmed delete must report deleted=true")
    reject(ctx, expanded, "not_found", exit_code=7)
    ctx.expect(not ctx.scan_values([marker]), "deleted memory content must be absent from DMEM_HOME")


@case("LIB-12", "R1", needs=())
def lib_12(ctx):
    from dmtest.builders import deck5

    body = "# Quarterly\n\n## Summary\nQuarterly update.\n\n## Actions\nOwner and due date.\n\n| Item | Due |\n| --- | --- |\n| Report | Friday |"
    doc = save_md(ctx, body, title="export-document")
    deck_file = ctx.home().parent / "export-deck.pptx"
    deck_file.parent.mkdir(parents=True, exist_ok=True); deck_file.write_bytes(deck5())
    deck = ctx.cli().json(_save_args("export-deck", doc_type="pitch_deck", provider="pptx", extra=["--file", str(deck_file)]))
    targets = {"md": (doc.json or {}).get("memory_id"), "html": (doc.json or {}).get("memory_id"),
               "docx": (doc.json or {}).get("memory_id"), "json": (doc.json or {}).get("memory_id"), "pptx": (deck.json or {}).get("memory_id")}
    for fmt, memory_id in targets.items():
        path = ctx.home().parent / f"export-{fmt}.out"
        result = ctx.cli().json(["export", memory_id or "missing", "--format", fmt, "--out", str(path)])
        data = path.read_bytes() if path.is_file() else b""
        mode_ok = path.is_file() and stat.S_IMODE(path.stat().st_mode) == 0o600
        if fmt == "md": content_ok = b"Quarterly" in data and b"Summary" in data and b"Report" in data
        elif fmt == "html": content_ok = b"Quarterly" in data and b"<script" not in data.lower()
        elif fmt in ("docx", "pptx"):
            if path.is_file():
                try:
                    with zipfile.ZipFile(path) as archive: content_ok = any(n.endswith(("document.xml", "slide1.xml")) and archive.read(n) for n in archive.namelist())
                except (OSError, zipfile.BadZipFile): content_ok = False
            else: content_ok = False
        else: content_ok = bool(data) and json.loads(data).get("memory_id") == memory_id
        second = ctx.cli().json(["export", memory_id or "missing", "--format", fmt, "--out", str(path)])
        ctx.expect(result.exit == 0 and mode_ok and content_ok, f"{fmt} export must create a private file with its structure")
        ctx.expect(second.exit == 2 and path.is_file() and path.read_bytes() == data, f"{fmt} export must reject overwrite and preserve the file")


@case("LIB-13", "R1", needs=())
def lib_13(ctx):
    home = ctx.home()
    saved = save_md(ctx, "# Storage\n\nInitial record.", title="storage")
    memory_id = (saved.json or {}).get("memory_id")
    state = home / "state.json"
    raw = state.read_bytes() if state.is_file() else b""
    target = home.parent / "outside-target"
    target.write_bytes(b"OUTSIDE_UNCHANGED"); target.chmod(0o600)
    state.unlink(missing_ok=True); os.symlink(target, state)
    blocked = ctx.cli().json(_save_args("storage", memory=memory_id, base=1, extra=["--stdin", "--format", "markdown"]), stdin="# Storage\n\nSymlink write.")
    unchanged = state.is_symlink() and target.read_bytes() == b"OUTSIDE_UNCHANGED"
    state.unlink(missing_ok=True); state.write_bytes(raw); state.chmod(0o600)
    state.write_text("CORRUPT_SENTINEL_LIB13", encoding="utf-8")
    corrupt = ctx.cli().json(["list"])
    output = sink_text(corrupt)
    modes = all(stat.S_IMODE(p.stat().st_mode) == 0o600 for p in home.iterdir() if p.is_file())
    ctx.expect(saved.exit == 0 and stat.S_IMODE(home.stat().st_mode) == 0o700 and modes, "DMEM_HOME must be 0700 and its files 0600")
    ctx.expect(blocked.exit != 0 and unchanged, "storage symlink must be rejected without writing through it")
    ctx.expect(corrupt.exit == 1 and (corrupt.json or {}).get("error", {}).get("code") == "internal" and
               "Traceback" not in output and str(home) not in output and "CORRUPT_SENTINEL_LIB13" not in output,
               "corruption must return a fixed internal error without stack, path, or input echo")


@case("LIB-14", "R1", needs=())
def lib_14(ctx):
    from dmtest.builders import docx

    root = ctx.home().parent; root.mkdir(parents=True, exist_ok=True)
    big_file = root / "too-large.txt"; big_file.write_bytes(b"x" * (10 * 1024 * 1024 + 1))
    empty = root / "empty.txt"; empty.write_bytes(b"")
    blank = root / "blank.txt"; blank.write_text("  \n\t", encoding="utf-8")
    exe = root / "unsupported.exe"; exe.write_bytes(b"MZ fixture")
    image = root / "image-only.docx"; image.write_bytes(docx([{"type": "image", "alt": ""}]))
    attempts = [ctx.cli().json(_save_args("large-file", extra=["--file", str(big_file)])),
                ctx.cli().json(_save_args("large-inline", extra=["--stdin", "--format", "markdown"], provider="markdown"), stdin="x" * (1024 * 1024 + 1)),
                ctx.cli().json(_save_args("empty-file", extra=["--file", str(empty)])),
                ctx.cli().json(_save_args("blank-file", extra=["--file", str(blank)])),
                ctx.cli().json(["save", "--kind", "template", "--title", "unsupported", "--doc-type", "resume", "--locale", "ko-KR", "--file", str(exe)]),
                ctx.cli().json(_save_args("image-only", provider="docx", extra=["--file", str(image)]))]
    for r, code in zip(attempts, ("payload_too_large", "payload_too_large", "extract_empty", "extract_empty", "unsupported_format", "extract_empty")):
        reject(ctx, r, code)
    listed = ctx.cli().json(["list"])
    ctx.expect(listed.exit == 0 and (listed.json or {}).get("results") == [], "all invalid or empty inputs must leave the library empty")


@case("LIB-15", "F", needs=())
def lib_15(ctx):
    source = ctx.home().parent / "shared-original.md"; source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# Shared original\n\nSame source for two independent forms.", encoding="utf-8")
    digest = hashlib.sha256(source.read_bytes()).hexdigest(); original = ctx.home() / "originals" / digest
    a = ctx.cli().json(_save_args("copy-a", extra=["--variant", "copy_a", "--file", str(source)]))
    b = ctx.cli().json(_save_args("copy-b", extra=["--variant", "copy_b", "--file", str(source)]))
    shared = original.is_file()  # while both references exist
    one = ctx.cli().json(["delete", (a.json or {}).get("memory_id", "missing"), "--yes"])
    remains = original.is_file()
    two = ctx.cli().json(["delete", (b.json or {}).get("memory_id", "missing"), "--yes"])
    ctx.expect(a.exit == 0 and b.exit == 0 and a.json.get("memory_id") != b.json.get("memory_id") and shared,
               "two scopes using the same file must share one original")
    ctx.expect(one.exit == 0 and remains, "deleting one of two references must preserve the original")
    ctx.expect(two.exit == 0 and not original.exists(), "deleting the last reference must remove the original")


@case("LIB-16", "F", needs=())
def lib_16(ctx):
    for iteration in range(10):
        base = save_md(ctx, f"# Race {iteration}\n\nBase content.", title="race")
        memory_id = (base.json or {}).get("memory_id")
        barrier, results = threading.Barrier(3), [None, None]
        def update(index):
            barrier.wait()
            results[index] = ctx.cli().json(_save_args("race", memory=memory_id, base=1, extra=["--stdin", "--format", "markdown"]),
                                            stdin=f"# Race {iteration}\n\nWriter {index}.")
        workers = [threading.Thread(target=update, args=(i,)) for i in range(2)]
        for worker in workers: worker.start()
        barrier.wait()
        for worker in workers: worker.join()
        winners = [r for r in results if r and r.exit == 0 and (r.json or {}).get("version") == 2]
        conflicts = [r for r in results if r and r.exit == 4 and (r.json or {}).get("error", {}).get("code") == "version_conflict"]
        listed = ctx.cli().json(["list"]); expanded = ctx.cli().json(["expand", memory_id or "missing", "--level", "2"])
        ctx.expect(base.exit == 0 and len(winners) == 1 and len(conflicts) == 1,
                   f"iteration {iteration}: concurrent updates must have one version-2 winner and one conflict")
        ctx.expect(listed.exit == 0 and expanded.exit == 0 and (expanded.json or {}).get("version") == 2,
                   f"iteration {iteration}: store must remain readable after the race")
        ctx.expect(ctx.cli().json(["delete", memory_id or "missing", "--yes"]).exit == 0,
                   f"iteration {iteration}: cleanup must succeed")
