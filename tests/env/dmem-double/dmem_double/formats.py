"""Text-format parsing and export for the test double (docs/spec/formats.md sections 2, 4, 5). Pure functions, no I/O.

StandardDoc ("stddoc/1") block shapes follow contracts/memory.v1.json. Nested list items are encoded as plain strings with two
leading spaces per nesting level (the schema keeps list items as strings), which round-trips through Markdown indentation.
"""
import html as _html
import json
import re
from html.parser import HTMLParser

from .scrub import strip_hidden

SLOT = re.compile(r"\{\{([a-z][a-z0-9_]{0,39})\}\}")
CALLOUTS = {"NOTE": "note", "TIP": "tip", "IMPORTANT": "important", "WARNING": "warning", "CAUTION": "caution"}
SKIP_TAGS = {"script", "style", "iframe", "object", "embed", "noscript", "template", "form", "input", "button", "select", "textarea", "svg", "canvas", "head", "title"}
VOID_TAGS = {"br", "img", "hr", "input", "meta", "link", "area", "base", "col", "source", "track", "wbr"}
INLINE_TAGS = ("strong", "b", "em", "i", "code", "a", "span", "small", "u", "mark", "sub", "sup")


def sanitize_text(text):
    """Remove zero-width, bidi and control characters (keeps \\n and \\t)."""
    clean = strip_hidden(str(text))[0]
    return "".join(ch for ch in clean if ch in "\n\t" or (ch >= " " and ch != "\x7f"))


def _doc(blocks=None, slots=None, dtype="document"):
    return {"schema": "stddoc/1", "type": dtype, "page": None, "styles": {}, "blocks": blocks or [], "slots": slots or [], "rules": []}


def _finish(blocks, dtype="document"):
    texts = []
    for b in blocks:
        if isinstance(b.get("text"), str):
            texts.append(b["text"])
        texts += [i for i in b.get("items", []) if isinstance(i, str)]
        for row in ([b["header"]] if b.get("header") else []) + b.get("rows", []):
            texts += [c for c in row if isinstance(c, str)]
    names = sorted({m for t in texts for m in SLOT.findall(t)})
    return _doc(blocks, [{"name": n, "type": "text", "required": False} for n in names], dtype)


# ----------------------------------------------------------------------------- markdown
_INLINE = re.compile(r"(\*\*(?P<b>.+?)\*\*)|(?<![\w*])\*(?P<i1>[^*\s][^*]*?)\*(?![\w*])|(?<![\w_])_(?P<i2>[^_\s][^_]*?)_(?![\w_])|`(?P<c>[^`]+)`|\[(?P<lt>[^\]]+)\]\((?P<lh>[^)\s]*)\)")


def _safe_href(url):
    url = url.strip()
    return bool(re.match(r"(https?://|mailto:|/|#|\./|\.\./)", url, re.I)) or not re.match(r"[a-z][a-z0-9+.-]*:", url, re.I)


def _inline(text):
    """Return (plain_text, runs_or_None). Intra-word underscores and asterisks are NOT emphasis (PROSE_SENTINEL_1 stays intact)."""
    runs, pos, rich = [], 0, False
    for m in _INLINE.finditer(text):
        if m.start() > pos:
            runs.append({"text": text[pos:m.start()]})
        if m.group("b") is not None:
            runs.append({"text": m.group("b"), "bold": True})
            rich = True
        elif m.group("i1") is not None or m.group("i2") is not None:
            runs.append({"text": m.group("i1") or m.group("i2"), "italic": True})
            rich = True
        elif m.group("c") is not None:
            runs.append({"text": m.group("c"), "code": True})
            rich = True
        else:
            if _safe_href(m.group("lh")):
                runs.append({"text": m.group("lt"), "href": m.group("lh")})
                rich = True
            else:
                runs.append({"text": m.group("lt")})  # unsafe target (javascript:, data:, ...) is dropped, the label stays
        pos = m.end()
    if pos < len(text):
        runs.append({"text": text[pos:]})
    return "".join(r["text"] for r in runs), (runs if rich else None)


def _para(text):
    plain, runs = _inline(text)
    block = {"type": "paragraph", "text": plain}
    if runs:
        block["runs"] = runs
    return block


_ITEM = re.compile(r"^(\s*)([-*+]|\d+\.)\s+(.*)$")


def parse_markdown(text):
    lines = sanitize_text(text).replace("\r\n", "\n").split("\n")
    blocks, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            blocks.append({"type": "heading", "level": len(m.group(1)), "text": _inline(m.group(2))[0]})
            i += 1
            continue
        if line.lstrip().startswith("```"):
            i += 1
            code = []
            while i < len(lines) and not lines[i].lstrip().startswith("```"):
                if lines[i].strip():
                    code.append(lines[i].strip())
                i += 1
            i += 1
            if code:
                joined = " ".join(code)
                blocks.append({"type": "paragraph", "text": joined, "runs": [{"text": joined, "code": True}]})
            continue
        if line.lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            header = [_inline(c.strip())[0] for c in line.strip().strip("|").split("|")]
            rows = []
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append([_inline(c.strip())[0] for c in lines[i].strip().strip("|").split("|")])
                i += 1
            blocks.append({"type": "table", "header": header, "rows": rows})
            continue
        if line.lstrip().startswith(">"):
            quote = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                quote.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            tag = re.match(r"^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$", quote[0].strip(), re.I)
            if tag:
                blocks.append({"type": "callout", "tone": CALLOUTS[tag.group(1).upper()], "text": _inline(" ".join(q.strip() for q in quote[1:]).strip())[0]})
            else:
                blocks.append({"type": "quote", "text": _inline(" ".join(q.strip() for q in quote).strip())[0]})
            continue
        m = _ITEM.match(line)
        if m:
            ordered, base, items = m.group(2)[0].isdigit(), len(m.group(1)), []
            while i < len(lines):
                mm = _ITEM.match(lines[i])
                if not mm or mm.group(2)[0].isdigit() != ordered and len(mm.group(1)) <= base:
                    break
                items.append("  " * max(0, (len(mm.group(1)) - base) // 2) + _inline(mm.group(3))[0])
                i += 1
            blocks.append({"type": "list", "ordered": ordered, "items": items})
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)\s]*)\)\s*$", line.strip())
        if m:
            blocks.append({"type": "image", "alt": m.group(1), "ref": m.group(2)})
            i += 1
            continue
        para = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,6}\s|\s*[-*+]\s|\s*\d+\.\s|\s*>|\s*\||\s*```|!\[)", lines[i]):
            para.append(lines[i].strip())
            i += 1
        blocks.append(_para(" ".join(para)))
    return _finish(blocks)


def parse_text(text):
    chunks = [re.sub(r"\s+", " ", c).strip() for c in re.split(r"\n\s*\n", sanitize_text(text))]
    return _finish([{"type": "paragraph", "text": c} for c in chunks if c])


# ----------------------------------------------------------------------------- html
class _Node:
    def __init__(self, tag, attrs):
        self.tag, self.attrs, self.kids = tag, dict(attrs), []


class _Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node("#root", [])
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, attrs)
        self.stack[-1].kids.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].kids.append(_Node(tag, attrs))

    def handle_endtag(self, tag):
        for n in range(len(self.stack) - 1, 0, -1):
            if self.stack[n].tag == tag:
                del self.stack[n:]
                return

    def handle_data(self, data):
        self.stack[-1].kids.append(data)


def _style(attrs):
    out = {}
    for part in (attrs.get("style") or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip().lower()] = v.strip().lower().replace(" ", "")
    return out


_WHITE = {"#fff", "#ffffff", "white", "rgb(255,255,255)"}


def _is_hidden(node):
    a, s = node.attrs, _style(node.attrs)
    if "hidden" in a or a.get("aria-hidden") == "true":
        return True
    if s.get("display") == "none" or s.get("visibility") == "hidden":
        return True
    if any(re.fullmatch(r"0(px|em|rem|pt)?", s.get(k, "x")) for k in ("width", "height", "font-size")):
        return True
    return s.get("color") in _WHITE and s.get("background-color", s.get("background")) in _WHITE


def _clean(text):
    return re.sub(r"\s+", " ", sanitize_text(text)).strip()


def _text_of(node, state):
    parts = []
    for k in node.kids:
        if isinstance(k, str):
            parts.append(k)
        elif k.tag in SKIP_TAGS:
            state["unsupported"] = state["unsupported"] or k.tag in ("iframe", "object", "embed")
        elif _is_hidden(k):
            state["hidden"] = True
        elif k.tag == "br":
            parts.append(" ")
        else:
            parts.append(_text_of(k, state))
    return "".join(parts)


def _runs(node, state, flags=None):
    out, flags = [], flags or {}
    for k in node.kids:
        if isinstance(k, str):
            if k:
                out.append(dict({"text": k}, **flags))
        elif k.tag in SKIP_TAGS:
            state["unsupported"] = state["unsupported"] or k.tag in ("iframe", "object", "embed")
        elif _is_hidden(k):
            state["hidden"] = True
        elif k.tag in ("strong", "b"):
            out += _runs(k, state, dict(flags, bold=True))
        elif k.tag in ("em", "i"):
            out += _runs(k, state, dict(flags, italic=True))
        elif k.tag == "code":
            out += _runs(k, state, dict(flags, code=True))
        elif k.tag == "a":
            href = k.attrs.get("href", "")
            out += _runs(k, state, dict(flags, href=href) if _safe_href(href) else flags)
        elif k.tag == "br":
            out.append(dict({"text": " "}, **flags))
        else:
            out += _runs(k, state, flags)
    return out


def _runs_block(runs, kind="paragraph"):
    text = _clean("".join(r["text"] for r in runs))
    if not text:
        return None
    block = {"type": kind, "text": text}
    if any(k in r for r in runs for k in ("bold", "italic", "code", "href")):
        block["runs"] = [dict(r, text=re.sub(r"\s+", " ", sanitize_text(r["text"]))) for r in runs if r["text"].strip()]
    return block


def _find(node, tag):
    for k in node.kids:
        if not isinstance(k, str):
            if k.tag == tag:
                return k
            found = _find(k, tag)
            if found is not None:
                return found
    return None


def parse_html(html_text):
    """Return (StandardDoc, warnings, meta). Active, hidden and unsafe content is removed and reported."""
    tree = _Tree()
    tree.feed(str(html_text))
    tree.close()
    state = {"hidden": False, "unsupported": False, "images": False}
    meta = {"title": None, "lang": None}
    htm, title = _find(tree.root, "html"), _find(tree.root, "title")
    if htm is not None:
        meta["lang"] = htm.attrs.get("lang")
    if title is not None:
        meta["title"] = _clean("".join(k for k in title.kids if isinstance(k, str))) or None
    blocks = []

    def list_items(node, depth, out):
        for k in node.kids:
            if isinstance(k, str) or k.tag in SKIP_TAGS:
                continue
            if _is_hidden(k):
                state["hidden"] = True
            elif k.tag == "li":
                own = _Node("li", [])
                own.kids = [c for c in k.kids if isinstance(c, str) or c.tag not in ("ul", "ol")]
                text = _clean(_text_of(own, state))
                if text:
                    out.append("  " * depth + text)
                for c in k.kids:
                    if not isinstance(c, str) and c.tag in ("ul", "ol"):
                        list_items(c, depth + 1, out)
            elif k.tag in ("ul", "ol"):
                list_items(k, depth, out)

    def table_rows(node, rows):
        for k in node.kids:
            if isinstance(k, str) or k.tag in SKIP_TAGS or _is_hidden(k):
                continue
            if k.tag == "tr":
                cells = [c for c in k.kids if not isinstance(c, str) and c.tag in ("td", "th")]
                if cells:
                    rows.append(([_clean(_text_of(c, state)) for c in cells], any(c.tag == "th" for c in cells)))
            else:
                table_rows(k, rows)

    def flush(loose):
        block = _runs_block(loose)
        if block:
            blocks.append(block)

    def walk(node):
        loose = []
        for k in node.kids:
            if isinstance(k, str):
                loose.append({"text": k})
                continue
            if k.tag in SKIP_TAGS:
                state["unsupported"] = state["unsupported"] or k.tag in ("iframe", "object", "embed")
                continue
            if _is_hidden(k):
                state["hidden"] = True
                continue
            if k.tag in INLINE_TAGS or k.tag == "br":
                holder = _Node("x", [])
                holder.kids = [k]
                loose += _runs(holder, state)
                continue
            flush(loose)
            loose = []
            if re.fullmatch(r"h[1-6]", k.tag):
                text = _clean(_text_of(k, state))
                if text:
                    blocks.append({"type": "heading", "level": int(k.tag[1]), "text": text})
            elif k.tag == "p":
                block = _runs_block(_runs(k, state))
                if block:
                    blocks.append(block)
            elif k.tag in ("ul", "ol"):
                items = []
                list_items(k, 0, items)
                if items:
                    blocks.append({"type": "list", "ordered": k.tag == "ol", "items": items})
            elif k.tag == "table":
                rows = []
                table_rows(k, rows)
                if rows:
                    header = rows[0][0] if rows[0][1] else None
                    body = rows[1:] if header else rows
                    blocks.append(dict({"type": "table"}, **({"header": header} if header else {}), rows=[r for r, _ in body]))
            elif k.tag == "blockquote":
                block = _runs_block(_runs(k, state))
                if block:
                    blocks.append({"type": "quote", "text": block["text"]})
            elif k.tag == "aside" or "callout" in (k.attrs.get("class") or ""):
                block = _runs_block(_runs(k, state))
                if block:
                    blocks.append({"type": "callout", "tone": "note", "text": block["text"]})
            elif k.tag == "img":
                state["images"] = True
            else:
                walk(k)
        flush(loose)

    walk(_find(tree.root, "body") or tree.root)
    warnings = set()
    if state["hidden"] or strip_hidden(str(html_text))[1]:
        warnings.add("hidden_text_removed")
    if state["unsupported"]:
        warnings.add("unsupported_block")
    if state["images"]:
        warnings.add("images_omitted")
    return _finish(blocks), sorted(warnings), meta


# ----------------------------------------------------------------------------- export
def _md_inline(block):
    if not block.get("runs"):
        return block.get("text", "")
    out = []
    for r in block["runs"]:
        t = r["text"]
        if r.get("code"):
            t = f"`{t}`"
        if r.get("bold"):
            t = f"**{t}**"
        if r.get("italic"):
            t = f"*{t}*"
        if r.get("href"):
            t = f"[{t}]({r['href']})"
        out.append(t)
    return "".join(out)


def _md_cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def _md_blocks(blocks):
    out = []
    for b in blocks:
        kind = b.get("type")
        if kind == "heading":
            out.append("#" * max(1, min(6, b.get("level", 1))) + " " + b["text"])
        elif kind == "paragraph":
            out.append(_md_inline(b))
        elif kind == "list":
            counters, lines = {}, []
            for item in b.get("items", []):
                depth = (len(item) - len(item.lstrip(" "))) // 2
                counters[depth] = counters.get(depth, 0) + 1
                for deeper in [d for d in counters if d > depth]:
                    del counters[deeper]
                lines.append("  " * depth + f"{counters[depth]}. " * bool(b.get("ordered")) + ("" if b.get("ordered") else "- ") + item.strip())
            out.append("\n".join(lines))
        elif kind == "table":
            rows = b.get("rows", [])
            header = b.get("header") or (rows[0] if rows else [])
            body = rows if b.get("header") else rows[1:]
            lines = ["| " + " | ".join(_md_cell(c) for c in header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
            lines += ["| " + " | ".join(_md_cell(c) for c in r) + " |" for r in body]
            out.append("\n".join(lines))
        elif kind == "quote":
            out.append("> " + b["text"])
        elif kind == "callout":
            out.append(f"> [!{b.get('tone', 'note').upper()}]\n> {b['text']}")
        elif kind == "image":
            out.append(f"![{b.get('alt', '')}]({b.get('ref', '')})")
    return out


def to_markdown(doc):
    """Return (text, warnings) following formats.md section 5 (decks: slides separated by a --- line)."""
    if doc.get("type") == "deck":
        parts = []
        for slide in doc.get("slides", []):
            chunk = [f"## {slide.get('title') or 'Slide ' + str(slide.get('index', ''))}"]
            chunk += _md_blocks(slide.get("blocks", []))
            chunk += [c.get("text", "") for c in slide.get("components", []) if c.get("text")]
            parts.append("\n\n".join(chunk))
        return "\n\n---\n\n".join(parts) + "\n", []
    return "\n\n".join(_md_blocks(doc.get("blocks", []))) + "\n", []


def _esc(text):
    return _html.escape(str(text), quote=True).replace("=", "&#61;")


def _html_runs(block):
    if not block.get("runs"):
        return _esc(block.get("text", ""))
    out = []
    for r in block["runs"]:
        t = _esc(r["text"])
        if r.get("code"):
            t = f"<code>{t}</code>"
        if r.get("bold"):
            t = f"<strong>{t}</strong>"
        if r.get("italic"):
            t = f"<em>{t}</em>"
        if r.get("href") and re.match(r"(https?://|mailto:|/|#)", r["href"], re.I):
            t = f'<a href="{_esc(r["href"])}">{t}</a>'
        out.append(t)
    return "".join(out)


def _html_blocks(blocks):
    out = []
    for b in blocks:
        kind = b.get("type")
        if kind == "heading":
            n = max(1, min(6, b.get("level", 1)))
            out.append(f"<h{n}>{_esc(b['text'])}</h{n}>")
        elif kind == "paragraph":
            out.append(f"<p>{_html_runs(b)}</p>")
        elif kind == "list":
            tag = "ol" if b.get("ordered") else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{_esc(i.strip())}</li>" for i in b.get("items", [])) + f"</{tag}>")
        elif kind == "table":
            head = "<thead><tr>" + "".join(f"<th>{_esc(c)}</th>" for c in b["header"]) + "</tr></thead>" if b.get("header") else ""
            rows = "".join("<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in r) + "</tr>" for r in b.get("rows", []))
            out.append(f"<table>{head}<tbody>{rows}</tbody></table>")
        elif kind == "quote":
            out.append(f"<blockquote>{_esc(b['text'])}</blockquote>")
        elif kind == "callout":
            out.append(f"<aside>{_esc(b['text'])}</aside>")
        elif kind == "image":
            out.append(f"<p>{_esc(b.get('alt', ''))}</p>")  # image references never become external <img> sources
    return out


def to_html(doc):
    """HTML using only the allowlisted tags; every text is escaped (formats.md section 5, FMT-03)."""
    if doc.get("type") == "deck":
        return "".join(f"<h2>{_esc(s.get('title') or '')}</h2>" + "".join(_html_blocks(s.get("blocks", []))) +
                       "".join(f"<p>{_esc(c['text'])}</p>" for c in s.get("components", []) if c.get("text")) for s in doc.get("slides", []))
    return "".join(_html_blocks(doc.get("blocks", [])))


def to_json(doc):
    return json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


# ----------------------------------------------------------------------------- derived views
def _block_chars(b):
    n = len(b.get("text", "")) + len(b.get("alt", "")) + sum(len(i) for i in b.get("items", []))
    return n + sum(len(c) for row in ([b["header"]] if b.get("header") else []) + b.get("rows", []) for c in row)


def structure_only(doc):
    """Keep headings, table header rows, slots and styles; drop all body content (copy policy structure_only). Returns (doc, retained)."""
    kept, removed, heads, tabs = [], 0, 0, 0
    for b in doc.get("blocks", []):
        if b.get("type") == "heading":
            kept.append({"type": "heading", "level": b.get("level", 1), "text": b["text"][:120]})
            heads += 1
        elif b.get("type") == "table" and b.get("header"):
            kept.append({"type": "table", "header": list(b["header"]), "rows": []})
            tabs += 1
            removed += sum(len(c) for r in b.get("rows", []) for c in r)
        else:
            removed += _block_chars(b)
    new = dict(doc, blocks=kept, slots=list(doc.get("slots", [])))
    if doc.get("type") == "deck":
        slides = []
        for s in doc.get("slides", []):
            removed += sum(_block_chars(b) for b in s.get("blocks", [])) + sum(len(c.get("text", "")) for c in s.get("components", []))
            slides.append(dict({k: v for k, v in s.items() if k not in ("blocks", "components", "notes")}, blocks=[], components=[]))
            heads += 1 if s.get("title") else 0
        new["slides"] = slides
    return new, {"headings": heads, "table_headers": tabs, "body_chars_removed": removed}


def outline(doc):
    if doc.get("type") == "deck":
        items = [{"level": 1, "text": s.get("title") or f"Slide {s.get('index', '')}"} for s in doc.get("slides", [])]
    else:
        items = [{"level": b.get("level", 1), "text": b["text"]} for b in doc.get("blocks", []) if b.get("type") == "heading"]
    return [{"level": i["level"], "text": sanitize_text(i["text"])[:60]} for i in items[:12]]


def spans(doc):
    out, p, t = [], 0, 0
    for b in doc.get("blocks", []):
        kind = b.get("type")
        if kind in ("paragraph", "quote", "callout"):
            p += 1
            out.append({"locator": f"p:{p}", "text": b["text"]})
        elif kind == "list":
            p += 1
            out.append({"locator": f"p:{p}", "text": "\n".join(i.strip() for i in b.get("items", []))})
        elif kind == "table":
            t += 1
            rows = ([b["header"]] if b.get("header") else []) + b.get("rows", [])
            out.append({"locator": f"t:{t}", "text": "\n".join(" | ".join(r) for r in rows)})
    for n, s in enumerate(doc.get("slides", []), 1):
        text = "\n".join([s.get("title") or ""] + [b.get("text", "") for b in s.get("blocks", [])] + [c.get("text", "") for c in s.get("components", [])]).strip()
        if text:
            out.append({"locator": f"s:{n}", "text": text})
    return out


def placeholders(doc):
    names = {s.get("name") for s in doc.get("slots", []) if s.get("name")}
    names |= {m for b in doc.get("blocks", []) for m in SLOT.findall(b.get("text", ""))}
    return sorted(names)


def autosummary(doc, doc_type, kind=None):
    """Deterministic L1 summary built from STRUCTURE (headings, slots, counts), never from body prose.
    A reference memory summarises its first fact instead (the user's own sentence, validated like any L1 text)."""
    if kind == "reference":
        s = spans(doc)
        if s:
            return re.sub(r"\s+", " ", sanitize_text(s[0]["text"]))[:200]
    heads = [o["text"] for o in outline(doc)][:8]
    slots = placeholders(doc)[:8]
    tables = sum(1 for b in doc.get("blocks", []) if b.get("type") == "table")
    parts = [str(doc_type)]
    if doc.get("type") == "deck":
        parts.append(f"slides {len(doc.get('slides', []))}: " + " / ".join(heads))
    elif heads:
        parts.append("sections: " + " / ".join(heads))
    if tables:
        parts.append(f"tables {tables}")
    if slots:
        parts.append("slots: " + ", ".join(slots))
    return sanitize_text("; ".join(parts))[:600]


def est_text_size(doc):
    return len(to_json(doc).encode("utf-8"))
