"""`dmem` test double (docs/spec/cli.md). Thin front-end over engine.dispatch; never prints stack traces or input values."""
import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__, engine, mutation, vocab
from .errors import DmemError, EXIT_CODES, MESSAGES
from .mcp import INSTRUCTIONS

COMMAND_NAMES = ["recall", "search", "list", "expand", "save", "web", "import", "copy", "publish", "delete", "outcome", "export", "status", "vocab",
                 "leaderboard", "rank", "usage", "link", "unlink", "cache", "doctor", "install", "uninstall", "guide", "browser-mcp"]
MARK_BEGIN, MARK_END = "<!-- dmem:begin -->", "<!-- dmem:end -->"
HELP = """usage: dmem [--json] [--yes] [--home DIR] [--endpoint URL] <command> [options]

commands:
  recall <url> [keywords...] [--doc-type --locale --provider --kind --scope --limit] | --stdin
  search [query] [--scope --kind --doc-type --locale --provider --license --limit --cursor]
  list [filters]                 alias of: search --scope mine
  expand <memory_id> [--version N] [--level 1|2] [--cursor C]
  save --kind K --title T --doc-type D --locale L [--provider P] (--file F | --stdin --format FMT | --from-preview ID) [--dry-run]
  web search <query> | web preview <url>
  import (<url> | --preview ID) --as template|reference [--copy-mode M] [--license L]
  copy <memory_id> [--version N] [--title T] [--copy-mode M]
  publish <memory_id> --visibility team|public|private [--license L] [--consent]
  delete <memory_id> --yes
  outcome <receipt_id> success|partial|failed [--used MEMORY@VERSION]...
  export <memory_id> --format md|html|docx|pptx|json --out ABS_PATH
  status | vocab | doctor | cache status|clear | guide print [--host H] [--write]
  leaderboard | rank | usage | link | unlink | install | uninstall | browser-mcp   (not available in the test double)
  --version | --help
"""


class Usage(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):  # never echo the offending text
        raise Usage()


def _split_globals(argv):
    json_mode, yes, out = False, False, []
    it = iter(argv)
    for a in it:
        if a == "--json":
            json_mode = True
        elif a == "--yes":
            yes = True
        elif a == "--no-color":
            continue
        elif a in ("--home", "--endpoint"):
            value = next(it, None)
            if value is None:
                raise Usage()
            if a == "--home":
                os.environ["DMEM_HOME"] = value
        else:
            out.append(a)
    return json_mode, yes, out


def _build():
    p = Parser(prog="dmem", add_help=False)
    sub = p.add_subparsers(dest="cmd")
    r = sub.add_parser("recall", add_help=False)
    r.add_argument("url", nargs="?")
    r.add_argument("keywords", nargs="*")
    r.add_argument("--stdin", action="store_true")
    for o in ("doc-type", "locale", "provider", "kind", "scope"):
        r.add_argument(f"--{o}")
    r.add_argument("--limit", type=int)
    for name in ("search", "list"):
        s = sub.add_parser(name, add_help=False)
        s.add_argument("query", nargs="?")
        for o in ("scope", "kind", "doc-type", "locale", "provider", "license", "cursor"):
            s.add_argument(f"--{o}")
        s.add_argument("--limit", type=int)
    e = sub.add_parser("expand", add_help=False)
    e.add_argument("memory_id")
    e.add_argument("--level", type=int, default=1)
    e.add_argument("--version", type=int)
    e.add_argument("--cursor")
    sv = sub.add_parser("save", add_help=False)
    for o in ("kind", "title", "doc-type", "locale", "provider", "variant", "file", "format", "from-preview", "memory", "summary"):
        sv.add_argument(f"--{o}")
    sv.add_argument("--base-version", type=int)
    sv.add_argument("--url-pattern", action="append")
    sv.add_argument("--keyword", action="append")
    sv.add_argument("--key-point", action="append")
    sv.add_argument("--stdin", action="store_true")
    sv.add_argument("--dry-run", action="store_true")
    w = sub.add_parser("web", add_help=False)
    w.add_argument("sub", choices=["search", "preview"])
    w.add_argument("target")
    for o in ("locale", "doc-type", "provider"):
        w.add_argument(f"--{o}")
    w.add_argument("--limit", type=int)
    im = sub.add_parser("import", add_help=False)
    im.add_argument("url", nargs="?")
    for o in ("preview", "as", "title", "doc-type", "locale", "provider", "copy-mode", "license"):
        im.add_argument(f"--{o}")
    im.add_argument("--keyword", action="append")
    c = sub.add_parser("copy", add_help=False)
    c.add_argument("memory_id")
    c.add_argument("--version", type=int)
    c.add_argument("--title")
    c.add_argument("--copy-mode")
    pu = sub.add_parser("publish", add_help=False)
    pu.add_argument("memory_id")
    pu.add_argument("--visibility", required=True)
    pu.add_argument("--version", type=int)
    pu.add_argument("--license")
    pu.add_argument("--consent", action="store_true")
    d = sub.add_parser("delete", add_help=False)
    d.add_argument("memory_id")
    o = sub.add_parser("outcome", add_help=False)
    o.add_argument("receipt_id")
    o.add_argument("outcome")
    o.add_argument("--used", action="append")
    ex = sub.add_parser("export", add_help=False)
    ex.add_argument("memory_id")
    ex.add_argument("--format", required=True)
    ex.add_argument("--out", required=True)
    ex.add_argument("--version", type=int)
    for name in ("status", "vocab", "doctor", "leaderboard", "rank", "usage", "link", "unlink", "install", "uninstall", "browser-mcp"):
        sub.add_parser(name, add_help=False, parse_known_args=True) if False else sub.add_parser(name, add_help=False).add_argument("rest", nargs="*")
    ca = sub.add_parser("cache", add_help=False)
    ca.add_argument("action", choices=["status", "clear"])
    g = sub.add_parser("guide", add_help=False)
    g.add_argument("action", choices=["print"])
    g.add_argument("--host", default="codex")
    g.add_argument("--write", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    t = sub.add_parser("__test", add_help=False)
    t.add_argument("action")
    t.add_argument("rest", nargs="*")
    return p


def _read_stdin_json():
    raw = sys.stdin.buffer.read(65 * 1024 + 1)
    if len(raw) > 64 * 1024:
        raise DmemError("payload_too_large")
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise DmemError("invalid_input")
    if not isinstance(obj, dict):
        raise DmemError("invalid_input")
    return obj


def _form(ns):
    form = {k: getattr(ns, a) for k, a in (("doc_type", "doc_type"), ("locale", "locale"), ("provider", "provider"), ("variant", "variant"))
            if getattr(ns, a, None) is not None}
    return form


def _file_content(path, form):
    from . import ooxml
    p = Path(path)
    if not p.is_file():
        raise DmemError("invalid_input")
    data = p.read_bytes()
    if len(data) > engine.MAX_FILE:
        raise DmemError("payload_too_large")
    fmt = ooxml.detect_format(p.name, data)
    if fmt in ("markdown", "text", "html"):
        return {"format": fmt, "data": data.decode("utf-8", "replace")}, data
    if fmt in ("docx", "pptx", "xlsx", "pdf"):
        extract = {"docx": ooxml.extract_docx, "pptx": ooxml.extract_pptx, "xlsx": ooxml.extract_xlsx_meta, "pdf": ooxml.extract_pdf}[fmt]
        doc, _ = extract(data)
        form.setdefault("provider", fmt)
        return {"format": "stddoc", "data": json.dumps(doc, ensure_ascii=False)}, data
    raise DmemError("unsupported_format")


def _snippet():
    return f"{MARK_BEGIN}\n## Document Memory (dmem)\n\n{INSTRUCTIONS}\n{MARK_END}\n"


def _guide(ns):
    target = Path.cwd() / ("CLAUDE.md" if ns.host == "claude-code" else "AGENTS.md")
    block = _snippet()
    if not ns.write:
        return {"schema_version": 1, "host": ns.host, "snippet": block, "written": False}
    old = target.read_text(encoding="utf-8") if target.exists() else ""
    if MARK_BEGIN in old and MARK_END in old:
        head, rest = old.split(MARK_BEGIN, 1)
        tail = rest.split(MARK_END, 1)[1].lstrip("\n")
        new = head + block + tail
    else:
        new = old + ("\n" if old and not old.endswith("\n\n") else "") + block
    if not ns.dry_run:
        target.write_text(new, encoding="utf-8")
    return {"schema_version": 1, "host": ns.host, "file": target.name, "written": not ns.dry_run, "changed": new != old}


def _run(ns, yes):
    ctx = engine.Ctx(require_canonical=False)
    cmd = ns.cmd
    if cmd == "recall":
        args = {}
        if ns.stdin:
            args = _read_stdin_json()
        else:
            if not ns.url:
                raise Usage()
            args["url"] = ns.url
            if ns.keywords:
                args["keywords"] = ns.keywords
            for key in ("doc_type", "locale", "provider", "kind", "scope", "limit"):
                if getattr(ns, key, None) is not None:
                    args[key] = getattr(ns, key)
        if ctx.mode == "server" and args.get("scope", "all") != "mine" and isinstance(args.get("keywords"), list):
            dropped = sum(1 for w in args["keywords"] if isinstance(w, str) and not vocab.keyword_canonical(w))
            if dropped:
                print(f"note: {dropped} keyword(s) outside the public vocabulary were not sent", file=sys.stderr)
        return engine.dispatch("doc_memory_recall", args, ctx)
    if cmd in ("search", "list"):
        args = {k: getattr(ns, k) for k in ("scope", "kind", "doc_type", "locale", "provider", "license", "cursor", "limit") if getattr(ns, k, None) is not None}
        if ns.query:
            args["query"] = ns.query
        if cmd == "list":
            args.setdefault("scope", "mine")
        return engine.dispatch("doc_memory_search", args, ctx)
    if cmd == "expand":
        args = {"memory_id": ns.memory_id, "level": ns.level}
        for key in ("version", "cursor"):
            if getattr(ns, key) is not None:
                args[key] = getattr(ns, key)
        return engine.dispatch("doc_memory_expand", args, ctx)
    if cmd == "save":
        form = _form(ns)
        args = {"kind": ns.kind, "title": ns.title, "form": form}
        if not (ns.kind and ns.title and ns.doc_type and ns.locale):
            raise Usage()
        for key, flag in (("url_patterns", ns.url_pattern), ("keywords", ns.keyword), ("key_points", ns.key_point)):
            if flag:
                args[key] = flag
        if ns.summary is not None:
            args["summary"] = ns.summary
        if ns.memory:
            args["memory_id"] = ns.memory
        if ns.base_version is not None:
            args["base_version"] = ns.base_version
        if ns.dry_run:
            args["dry_run"] = True
        original = None
        if ns.file:
            args["content"], original = _file_content(ns.file, form)
        elif ns.stdin:
            if not ns.format:
                raise Usage()
            raw = sys.stdin.buffer.read(engine.MAX_FILE + 1)
            if len(raw) > engine.MAX_INLINE:
                raise DmemError("payload_too_large")
            args["content"] = {"format": ns.format, "data": raw.decode("utf-8", "replace")}
        elif ns.from_preview:
            args["from_preview_id"] = ns.from_preview
        else:
            raise Usage()
        return engine.dispatch("doc_memory_save", args, ctx, original=original)
    if cmd == "web":
        if ns.sub == "search":
            args = {"query": ns.target}
            for key in ("locale", "doc_type", "provider", "limit"):
                if getattr(ns, key, None) is not None:
                    args[key] = getattr(ns, key)
            return engine.dispatch("doc_memory_web_search", args, ctx)
        return engine.dispatch("doc_memory_web_preview", {"url": ns.target}, ctx)
    if cmd == "import":
        args = {"as": getattr(ns, "as")}
        if getattr(ns, "as") is None:
            raise Usage()
        if ns.preview:
            args["preview_id"] = ns.preview
        elif ns.url:
            args["url"] = ns.url
        else:
            raise Usage()
        form = _form(ns)
        if form:
            args["form"] = form
        for key, flag in (("title", ns.title), ("copy_mode", ns.copy_mode), ("license", ns.license), ("keywords", ns.keyword)):
            if flag:
                args[key] = flag
        return engine.dispatch("doc_memory_import", args, ctx)
    if cmd == "copy":
        args = {"memory_id": ns.memory_id}
        for key in ("version", "title", "copy_mode"):
            if getattr(ns, key) is not None:
                args[key] = getattr(ns, key)
        return engine.dispatch("doc_memory_copy", args, ctx)
    if cmd == "publish":
        args = {"memory_id": ns.memory_id, "visibility": ns.visibility}
        if ns.version is not None:
            args["version"] = ns.version
        if ns.license:
            args["license"] = ns.license
        if ns.consent:
            args.update({"consent": True, "consent_version": engine.CONSENT_VERSION})
        return engine.dispatch("doc_memory_publish", args, ctx)
    if cmd == "delete":
        if not yes:
            raise DmemError("invalid_input")  # never prompt; a missing --yes is a usage error (cli.md section 4)
        return engine.dispatch("doc_memory_delete", {"memory_id": ns.memory_id, "confirm": True}, ctx)
    if cmd == "outcome":
        used = []
        for item in ns.used or []:
            mid, _, ver = item.rpartition("@")
            if not mid or not ver.isdigit():
                raise DmemError("invalid_input")
            used.append({"memory_id": mid, "version": int(ver)})
        args = {"receipt_id": ns.receipt_id, "outcome": ns.outcome}
        if used:
            args["used"] = used
        return engine.dispatch("doc_memory_outcome", args, ctx)
    if cmd == "export":
        args = {"memory_id": ns.memory_id, "format": ns.format, "out": ns.out}
        if ns.version is not None:
            args["version"] = ns.version
        return engine.op_export(ctx, args)
    if cmd == "status":
        return engine.dispatch("doc_memory_status", {}, ctx)
    if cmd == "vocab":
        return engine.op_vocab(ctx, {})
    if cmd == "doctor":
        status = engine.op_status(ctx, {})
        return {"schema_version": 1, "checks": [{"name": "mode", "ok": True, "detail": status["mode"]}, {"name": "vocab", "ok": True, "detail": status["vocab"]["doc_types"]}]}
    if cmd == "cache":
        return {"schema_version": 1, "entries": 0, "bytes": 0, "max_entries": 0, "max_bytes": 0} if ns.action == "status" else {"schema_version": 1, "cleared": True}
    if cmd == "guide":
        return _guide(ns)
    if cmd == "__test":
        args = {"action": ns.action}
        rest = ns.rest
        if ns.action == "load-fixture":
            args["path"] = rest[0]
            args["owner_map"] = dict(item.split("=", 1) for item in rest[1:])
        elif ns.action == "takedown":
            args["memory_id"] = rest[0]
        elif ns.action == "patch":
            args["memory_id"], args["patch"] = rest[0], json.loads(rest[1])
        return engine.op_test(ctx, args)
    raise DmemError("invalid_input")  # leaderboard, rank, usage, link, unlink, install, uninstall, browser-mcp


def _exit_code(err):
    if mutation() == "exit_code_wrong" and err.code == "not_found":
        return 1
    return err.exit_code


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    json_mode = "--json" in argv
    try:
        json_mode, yes, rest = _split_globals(argv)
        if rest in (["--version"], ["-V"]):
            print(f"dmem {__version__}")
            return 0
        if not rest or rest in (["--help"], ["-h"], ["help"]):
            print(HELP)
            return 0
        ns = _build().parse_args(rest)
        if ns.cmd is None:
            raise Usage()
        result = _run(ns, yes)
        print(json.dumps(result, ensure_ascii=False) if json_mode else json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Usage:
        err = DmemError("invalid_input")
        if json_mode:
            print(json.dumps(err.envelope(), ensure_ascii=False))
        else:
            print("usage: dmem <command> [options]   (run `dmem --help`)", file=sys.stderr)
        return 2
    except DmemError as err:
        if json_mode:
            print(json.dumps(err.envelope(), ensure_ascii=False))
        else:
            print(f"error: {err.code}" + (f" ({err.reason})" if err.reason else "") + f" - {MESSAGES[err.code]}", file=sys.stderr)
        return _exit_code(err)
    except Exception:  # internal failure: fixed text, no traceback, no input
        err = DmemError("internal")
        if json_mode:
            print(json.dumps(err.envelope(), ensure_ascii=False))
        else:
            print("error: internal - Internal error.", file=sys.stderr)
        return 1
