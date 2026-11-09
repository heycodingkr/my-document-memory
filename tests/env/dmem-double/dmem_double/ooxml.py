"""Small, dependency-free OOXML/PDF adapter for the deterministic test double."""
from io import BytesIO
import re
import zipfile
import xml.etree.ElementTree as ET
import zlib

from .errors import DmemError

MAX_UNCOMPRESSED = 50 * 1024 * 1024
MAX_RATIO = 200
MAX_PARTS = 2000
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"w": W, "p": P, "a": A, "r": R, "rel": REL}


def _err(code, reason=None):
    raise DmemError(code, reason=reason)


def _q(ns, name):
    return "{%s}%s" % (ns, name)


def _text(el):
    return "".join((n.text or "") for n in el.iter() if n.tag in (_q(W, "t"), _q(A, "t")))


def _standard(kind, **kw):
    if kind in ("document", "deck"):
        kw.setdefault("slots", [])
        kw.setdefault("rules", [])
    return {"schema": "stddoc/1", "type": kind, **kw}


def detect_format(filename, data):
    ext = (filename or "").lower().rsplit(".", 1)[-1] if "." in (filename or "") else ""
    raw = bytes(data or b"")
    if raw.startswith(b"%PDF-"):
        return "pdf"
    if raw.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(BytesIO(raw)) as z:
                names = set(z.namelist())
            for part, fmt in (("word/", "docx"), ("ppt/", "pptx"), ("xl/", "xlsx")):
                if any(n.startswith(part) for n in names):
                    return fmt
        except (zipfile.BadZipFile, OSError):
            pass
        return {"docx": "docx", "pptx": "pptx", "xlsx": "xlsx"}.get(ext)
    sample = raw.lstrip()[:256].lower()
    if sample.startswith((b"<!doctype html", b"<html")):
        return "html"
    if ext == "pdf":
        return "pdf"
    if ext in ("md", "markdown"):
        return "markdown"
    if ext in ("txt", "text"):
        return "text"
    if ext == "html":
        return "html"
    if ext in ("docx", "pptx", "xlsx"):
        return ext
    if ext and ext not in ("htm", "csv"):
        return None  # a file name that claims another type (.exe, .zip, ...) is unsupported even when its bytes happen to decode as text
    if raw and b"\x00" in raw[:4096]:
        return None
    try:
        raw.decode("utf-8")
        return "text" if raw else None
    except UnicodeDecodeError:
        return None


def _open(data):
    try:
        z = zipfile.ZipFile(BytesIO(data))
        infos = z.infolist()
    except (zipfile.BadZipFile, OSError, TypeError):
        _err("unsupported_format")
    if len(infos) > MAX_PARTS:
        _err("payload_too_large")
    total = 0
    for info in infos:
        total += info.file_size
        if info.file_size and info.file_size / max(info.compress_size, 1) > MAX_RATIO:
            z.close()
            _err("payload_too_large")
        if total > MAX_UNCOMPRESSED:
            z.close()
            _err("payload_too_large")
    names = [i.filename.lower().replace("\\", "/") for i in infos]
    if any("vbaproject.bin" in n or re.search(r"/(?:embed(?:ding)?s?|oleobjects?)/", "/" + n) or re.search(r"(?:oleobject|package)\d*\.bin$", n) for n in names):
        z.close()
        _err("unsupported_format")
    return z, set(i.filename for i in infos)


def _xml(z, name):
    try:
        return ET.fromstring(z.read(name))
    except (KeyError, ET.ParseError, zipfile.BadZipFile, RuntimeError, zlib.error):
        _err("unsupported_format")


def _relationships(z, names, prefix, warnings):
    relname = prefix + "/_rels/" + prefix.rsplit("/", 1)[-1] + ".rels" if prefix.endswith(".xml") else prefix
    # Callers pass the package relationship part explicitly.
    if relname not in names:
        return
    root = _xml(z, relname)
    if any(r.get("TargetMode") == "External" for r in root):
        warnings.add("external_reference_removed")


def _external_rels(z, names, part, warnings):
    folder, base = part.rsplit("/", 1)
    path = folder + "/_rels/" + base + ".rels"
    if path in names:
        root = _xml(z, path)
        if any(r.get("TargetMode", "").lower() == "external" for r in root):
            warnings.add("external_reference_removed")


def _field_instructions(root):
    return [((n.text or "").strip().upper()) for n in root.iter(_q(W, "instrText"))]


def _styles(z, names):
    out = {}
    if "word/styles.xml" not in names:
        return out
    root = _xml(z, "word/styles.xml")
    for st in root.findall("w:style", NS):
        sid = st.get(_q(W, "styleId"), "")
        key = {"Heading1": "heading1", "Heading2": "heading2", "Heading3": "heading3", "Normal": "body"}.get(sid)
        if not key:
            continue
        name = st.find("w:name", NS)
        props = {"name": name.get(_q(W, "val")) if name is not None else sid}
        rp = st.find("w:rPr", NS)
        if rp is not None:
            sz = rp.find("w:sz", NS)
            if sz is not None:
                try:
                    props["size"] = int(sz.get(_q(W, "val"), "0")) / 2
                except ValueError:
                    pass
            props["bold"] = rp.find("w:b", NS) is not None
        out[key] = props
    return out


def _page(root):
    sect = root.find(".//w:sectPr", NS)
    if sect is None:
        return {"size": "A4", "orientation": "portrait", "margins_mm": [25, 25, 25, 25]}
    ps, pm = sect.find("w:pgSz", NS), sect.find("w:pgMar", NS)
    width = int(ps.get(_q(W, "w"), 11906)) if ps is not None else 11906
    height = int(ps.get(_q(W, "h"), 16838)) if ps is not None else 16838
    size = "A4" if (width, height) in ((11906, 16838), (16838, 11906)) else "Letter" if (width, height) in ((12240, 15840), (15840, 12240)) else "custom"
    orient = "landscape" if width > height else "portrait"
    margins = [25, 25, 25, 25]
    if pm is not None:
        margins = [round(int(pm.get(_q(W, key), "1417")) * 25.4 / 1440) for key in ("top", "right", "bottom", "left")]
    return {"size": size, "orientation": orient, "margins_mm": margins}


def _paragraph_block(p, numbering=None):
    text = _text(p)
    ppr = p.find("w:pPr", NS)
    style = ppr.find("w:pStyle", NS) if ppr is not None else None
    sid = style.get(_q(W, "val"), "") if style is not None else ""
    m = re.fullmatch(r"Heading([1-6])", sid, re.I)
    if sid.lower() == "title":
        return {"type": "heading", "level": 1, "text": text}
    if m:
        return {"type": "heading", "level": int(m.group(1)), "text": text}
    num = ppr.find("w:numPr", NS) if ppr is not None else None
    if num is not None:
        ordered = (numbering or {}).get((num.find("w:numId", NS).get(_q(W, "val"), "") if num.find("w:numId", NS) is not None else ""), False)
        return {"type": "list", "ordered": ordered, "items": [text]}
    if re.match(r"^\d+[.)]\s", text):
        return {"type": "list", "ordered": True, "items": [re.sub(r"^\d+[.)]\s*", "", text)]}
    if re.match(r"^[•●▪◦]\s*", text):
        return {"type": "list", "ordered": False, "items": [re.sub(r"^[•●▪◦]\s*", "", text)]}
    return {"type": "paragraph", "text": text}


def _numbering(z, names):
    result = {}
    if "word/numbering.xml" not in names: return result
    root = _xml(z, "word/numbering.xml")
    formats = {}
    for abstract in root.findall("w:abstractNum", NS):
        aid = abstract.get(_q(W, "abstractNumId"), "")
        lvl = abstract.find("w:lvl/w:numFmt", NS)
        formats[aid] = lvl is not None and lvl.get(_q(W, "val"), "bullet") != "bullet"
    for num in root.findall("w:num", NS):
        aid = num.find("w:abstractNumId", NS)
        if aid is not None: result[num.get(_q(W, "numId"), "")] = formats.get(aid.get(_q(W, "val"), ""), False)
    return result


def extract_docx(data):
    z, names = _open(data)
    if "word/document.xml" not in names:
        z.close()
        _err("unsupported_format")
    warnings = set()
    _all_external(z, names, warnings)
    if "word/comments.xml" in names:
        warnings.add("comments_dropped")
    root = _xml(z, "word/document.xml")
    numbering = _numbering(z, names)
    instr = _field_instructions(root)
    if any(re.search(r"\b(DDEAUTO|DDE|INCLUDETEXT)\b", x) for x in instr):
        warnings.add("fields_flattened")
    blocks = []
    body = root.find("w:body", NS)
    if body is not None:
        for child in body:
            if child.tag == _q(W, "p"):
                if any(re.search(r"\b(DDEAUTO|DDE|INCLUDETEXT)\b", x) for x in instr) and child.find(".//w:instrText", NS) is not None:
                    continue
                block = _paragraph_block(child, numbering)
                if block.get("text") or block.get("items"):
                    if block.get("type") == "list" and blocks and blocks[-1].get("type") == "list" and blocks[-1].get("ordered") == block.get("ordered"):
                        blocks[-1]["items"].extend(block["items"])
                    else:
                        blocks.append(block)
                if child.find(".//w:drawing", NS) is not None or child.find(".//w:pict", NS) is not None:
                    warnings.add("images_omitted")
            elif child.tag == _q(W, "tbl"):
                rows = []
                for tr in child.findall("w:tr", NS):
                    rows.append([_text(tc) for tc in tr.findall("w:tc", NS)])
                if rows:
                    blocks.append({"type": "table", "header": rows[0], "rows": rows[1:]})
            elif child.tag != _q(W, "sectPr"):
                warnings.add("unsupported_block")
    if any("footnotes.xml" in n or "endnotes.xml" in n for n in names):
        warnings.add("unsupported_block")
    z.close()
    if not any((b.get("text") or " ".join(b.get("items", [])) or " ".join(b.get("header", [])) or " ".join(sum(b.get("rows", []), []))).strip() for b in blocks):
        _err("extract_empty", "no_text")
    if names and any("word/styles.xml" in n for n in names):
        warnings.add("styles_approximated")
    return _standard("document", blocks=blocks, page=_page(root), styles=_styles_from_bytes(data)), sorted(warnings)


def _styles_from_bytes(data):
    z, names = _open(data)
    try:
        return _styles(z, names)
    finally:
        z.close()


def _all_external(z, names, warnings):
    for path in names:
        if path.endswith(".rels"):
            root = _xml(z, path)
            if any(r.get("TargetMode", "").lower() == "external" for r in root):
                warnings.add("external_reference_removed")


def _rels_map(root):
    return {r.get("Id"): r.get("Target", "") for r in root}


def _resolve(base, target):
    if target.startswith("/"):
        return target.lstrip("/")
    parts = base.split("/")[:-1]
    for part in target.split("/"):
        if part == "..":
            if parts: parts.pop()
        elif part not in ("", "."):
            parts.append(part)
    return "/".join(parts)


def _role(title, index):
    if index == 1: return "cover"
    t = (title or "").lower()
    for words, role in ((("problem", "문제"), "problem"), (("solution", "해결"), "solution"), (("market", "시장"), "market"), (("team", "팀"), "team"), (("ask", "요청", "투자"), "ask"), (("agenda", "목차"), "agenda")):
        if any(x in t for x in words): return role
    return "content"


def extract_pptx(data):
    z, names = _open(data)
    if "ppt/presentation.xml" not in names: z.close(); _err("unsupported_format")
    warnings = set()
    _all_external(z, names, warnings)
    pres = _xml(z, "ppt/presentation.xml")
    relpath = "ppt/_rels/presentation.xml.rels"
    rels = _rels_map(_xml(z, relpath)) if relpath in names else {}
    slides = []
    ids = pres.find("p:sldIdLst", NS)
    if ids is not None:
        for i, sid in enumerate(ids, 1):
            target = rels.get(sid.get(_q(R, "id")))
            if not target: continue
            part = _resolve("ppt/presentation.xml", target)
            if part not in names: continue
            root = _xml(z, part)
            shapes = root.findall(".//p:sp", NS)
            texts = [_text(s) for s in shapes]
            texts = [t for t in texts if t]
            title_shape = None
            for shape, txt in zip([s for s in shapes if _text(s)], texts):
                ph = shape.find(".//p:ph", NS)
                if ph is not None and ph.get("type") in ("title", "ctrTitle"):
                    title_shape = txt; break
            title = title_shape or (texts[0] if texts else "")
            body = [t for t in texts if t != title]
            slides.append({"index": len(slides)+1, "role": _role(title, len(slides)+1), "layout": "title_body", "title": title or None, "blocks": [{"type": "paragraph", "text": t} for t in body]})
            if root.find(".//p:pic", NS) is not None or any("/media/" in n for n in names): warnings.add("images_omitted")
    theme = {"aspect": "custom", "colors": {}}
    sz = pres.find("p:sldSz", NS)
    if sz is not None:
        try: dims = (int(sz.get("cx", 0)), int(sz.get("cy", 0)))
        except ValueError: dims = (0, 0)
        theme["aspect"] = "16:9" if dims == (12192000, 6858000) else "4:3" if dims == (9144000, 6858000) else "custom"
    if "ppt/theme/theme1.xml" in names:
        tr = _xml(z, "ppt/theme/theme1.xml")
        cs = tr.find(".//a:clrScheme", NS)
        if cs is not None:
            for name in ("accent1", "accent2", "dk1", "lt1"):
                el = cs.find("a:"+name, NS)
                if el is not None and len(el): theme["colors"][name] = next(iter(el)).get("val", "")
    if any("comment" in n.lower() for n in names): warnings.add("comments_dropped")
    warnings.add("layout_inferred")
    z.close()
    if not slides or not any(s["title"] or s["blocks"] for s in slides): _err("extract_empty", "no_text")
    return _standard("deck", theme=theme, slides=slides), sorted(warnings)


def extract_xlsx_meta(data):
    z, names = _open(data)
    if "xl/workbook.xml" not in names: z.close(); _err("unsupported_format")
    wb = _xml(z, "xl/workbook.xml")
    rp = "xl/_rels/workbook.xml.rels"
    rels = _rels_map(_xml(z, rp)) if rp in names else {}
    shared = []
    if "xl/sharedStrings.xml" in names:
        shared = ["".join(t.text or "" for t in si.findall(".//a:t", NS)) for si in _xml(z, "xl/sharedStrings.xml")]
    sheets = []
    for sh in wb.findall(".//{*}sheet"):
        name = sh.get("name", "Sheet")
        target = rels.get(sh.get(_q(R, "id")))
        item = {"name": name}
        if target:
            part = _resolve("xl/workbook.xml", target)
            if part in names:
                root = _xml(z, part); row = root.find(".//{*}row")
                if row is not None:
                    cols = []
                    for cell in row.findall("{*}c"):
                        val = cell.find("{*}v"); value = (val.text or "") if val is not None else ""
                        if cell.get("t") == "s" and value.isdigit() and int(value) < len(shared): value = shared[int(value)]
                        if cell.get("t") == "inlineStr": value = "".join(t.text or "" for t in cell.findall(".//{*}t"))
                        cols.append({"header": value})
                    item["columns"] = cols
        sheets.append(item)
    z.close()
    return _standard("sheet", sheets=sheets), ["sheet_support_deferred"]


def _pdf_string(data, i):
    out = bytearray(); depth = 1; i += 1
    while i < len(data) and depth:
        c = data[i]
        if c == 92 and i + 1 < len(data):
            i += 1; c = data[i]
            if c in b"nrtbf": c = {110:10, 114:13, 116:9, 98:8, 102:12}[c]
            elif c in b"()\\": pass
            elif 48 <= c <= 55:
                digs = bytes([c]);
                for _ in range(2):
                    if i+1 < len(data) and 48 <= data[i+1] <= 55: i += 1; digs += bytes([data[i]])
                c = int(digs, 8) & 255
            out.append(c)
        elif c == 40: depth += 1; out.append(c)
        elif c == 41:
            depth -= 1
            if depth: out.append(c)
        else: out.append(c)
        i += 1
    return bytes(out), i


def _pdf_text(stream):
    chunks = []
    for m in re.finditer(rb"\bBT\b(.*?)\bET\b", stream, re.S):
        body = m.group(1)
        i = 0
        while i < len(body):
            if body[i] == 40:
                val, end = _pdf_string(body, i); i = end
                tail = body[i:i+12]
                if re.match(rb"\s*Tj\b", tail): chunks.append(val.decode("utf-8", "replace")); i += re.match(rb"\s*Tj\b", tail).end()
            elif body[i] == 91:
                end = body.find(b"]", i+1)
                if end < 0: break
                arr, j = body[i+1:end], 0
                while j < len(arr):
                    if arr[j] == 40:
                        val, j = _pdf_string(arr, j); chunks.append(val.decode("utf-8", "replace"))
                    else: j += 1
                i = end+1
                if re.match(rb"\s*TJ\b", body[i:]): i += re.match(rb"\s*TJ\b", body[i:]).end()
            else: i += 1
    return " ".join(x for x in chunks if x).strip()


def extract_pdf(data):
    raw = bytes(data or b"")
    if not raw.startswith(b"%PDF-"): _err("unsupported_format")
    objs = {int(m.group(1)): m.group(2) for m in re.finditer(rb"(?m)(\d+)\s+\d+\s+obj\b(.*?)endobj", raw, re.S)}
    pages = []
    for n, body in objs.items():
        if re.search(rb"/Type\s*/Page\b", body) and not re.search(rb"/Type\s*/Pages\b", body): pages.append((n, body))
    pages.sort()
    blocks, spans = [], []
    for index, (_, page) in enumerate(pages, 1):
        refs = re.findall(rb"/Contents\s+(\d+)\s+\d+\s+R", page)
        text = ""
        for ref in refs:
            obj = objs.get(int(ref), b"")
            sm = re.search(rb"stream\r?\n(.*?)\r?\nendstream", obj, re.S)
            if sm and b"/FlateDecode" not in obj[:sm.start()]: text += _pdf_text(sm.group(1))
        if text:
            block = {"type": "paragraph", "text": text}
            blocks.append(block); spans.append({"text": text, "locator": "page:%d" % index})
    if not spans: _err("extract_empty", "ocr_required")
    # `spans` carries page locators for the text-only PDF adapter; blocks remain schema-valid.
    return _standard("document", blocks=blocks, slots=[], rules=[], spans=spans), []


def _xmlbytes(root):
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _pkg(parts):
    out = BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name in sorted(parts):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100600 << 16
            z.writestr(info, parts[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    return out.getvalue()


def _element(parent, ns, name, attrs=None):
    return ET.SubElement(parent, _q(ns, name), attrs or {})


def _word_para(text="", style=None, block=None):
    p = ET.Element(_q(W, "p"))
    ppr = None
    if style:
        ppr = _element(p, W, "pPr")
        _element(ppr, W, "pStyle", {_q(W, "val"): style})
    if block and block.get("type") in ("quote", "callout"):
        ppr = ppr or _element(p, W, "pPr")
        _element(ppr, W, "ind", {_q(W, "left"): "360"})
        if block.get("type") == "callout":
            _element(ppr, W, "shd", {_q(W, "fill"): "EAF2F8", _q(W, "val"): "clear"})
    runs = block.get("runs") if block and block.get("type") == "paragraph" else None
    for item in runs or [{"text": text}]:
        r = _element(p, W, "r")
        rp = None
        if item.get("bold") or item.get("italic"):
            rp = _element(r, W, "rPr")
            if item.get("bold"): _element(rp, W, "b")
            if item.get("italic"): _element(rp, W, "i")
        t = _element(r, W, "t"); t.text = str(item.get("text", ""))
    return p


def _docx_block(body, block):
    typ = block.get("type")
    if typ == "heading":
        body.append(_word_para(block.get("text", ""), "Heading%d" % min(6, max(1, int(block.get("level", 1))))))
    elif typ == "paragraph": body.append(_word_para(block.get("text", ""), block=block))
    elif typ == "list":
        for i, item in enumerate(block.get("items", []), 1):
            body.append(_word_para(("%d. " % i if block.get("ordered") else "• ") + str(item)))
    elif typ in ("quote", "callout"):
        body.append(_word_para(block.get("text", ""), "Quote", block))
    elif typ == "table":
        tbl = _element(body, W, "tbl")
        rows = ([block["header"]] if block.get("header") is not None else []) + list(block.get("rows", []))
        for row in rows:
            tr = _element(tbl, W, "tr")
            for val in row:
                tc = _element(tr, W, "tc"); tc.append(_word_para(str(val)))
    elif typ == "image":
        body.append(_word_para("[Image omitted: %s]" % block.get("alt", "")))


def _word_styles(styles):
    root = ET.Element(_q(W, "styles"))
    definitions = {"Normal": ("Normal", None), "Title": ("Title", "Normal"), "Quote": ("Quote", "Normal")}
    for n in range(1, 7): definitions["Heading%d" % n] = ("heading %d" % n, "Normal")
    for sid, (name, based) in definitions.items():
        st = _element(root, W, "style", {_q(W, "type"): "paragraph", _q(W, "styleId"): sid})
        _element(st, W, "name", {_q(W, "val"): name})
        if based: _element(st, W, "basedOn", {_q(W, "val"): based})
        if sid.startswith("Heading") or sid == "Title":
            rp = _element(st, W, "rPr"); _element(rp, W, "b")
    return _xmlbytes(root)


def export_docx(doc):
    body = ET.Element(_q(W, "body"))
    for block in doc.get("blocks", []): _docx_block(body, block)
    page = doc.get("page") or {}
    sizes = {"A4": (11906, 16838), "Letter": (12240, 15840), "A3": (16838, 23811), "A5": (8391, 11906), "Legal": (12240, 20160)}
    size = page.get("size", "A4"); width, height = sizes.get(size, sizes["A4"])
    if page.get("orientation") == "landscape": width, height = max(width, height), min(width, height)
    sect = _element(body, W, "sectPr")
    _element(sect, W, "pgSz", {_q(W, "w"): str(width), _q(W, "h"): str(height), _q(W, "orient"): page.get("orientation", "portrait")})
    mm = page.get("margins_mm", [25, 20, 25, 20]); tw = [str(round(int(v) * 1440 / 25.4)) for v in mm]
    _element(sect, W, "pgMar", {_q(W, k): v for k, v in zip(("top", "right", "bottom", "left"), tw)})
    root = ET.Element(_q(W, "document")); root.append(body)
    types = ET.Element("{http://schemas.openxmlformats.org/package/2006/content-types}Types")
    _element(types, "http://schemas.openxmlformats.org/package/2006/content-types", "Default", {"Extension": "rels", "ContentType": "application/vnd.openxmlformats-package.relationships+xml"})
    _element(types, "http://schemas.openxmlformats.org/package/2006/content-types", "Default", {"Extension": "xml", "ContentType": "application/xml"})
    _element(types, "http://schemas.openxmlformats.org/package/2006/content-types", "Override", {"PartName": "/word/document.xml", "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"})
    _element(types, "http://schemas.openxmlformats.org/package/2006/content-types", "Override", {"PartName": "/word/styles.xml", "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"})
    relns = REL
    package_rels = ET.Element(_q(relns, "Relationships"))
    _element(package_rels, relns, "Relationship", {"Id": "rId1", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument", "Target": "word/document.xml"})
    word_rels = ET.Element(_q(relns, "Relationships"))
    _element(word_rels, relns, "Relationship", {"Id": "rId1", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles", "Target": "styles.xml"})
    return _pkg({"[Content_Types].xml": _xmlbytes(types), "_rels/.rels": _xmlbytes(package_rels), "word/document.xml": _xmlbytes(root), "word/styles.xml": _word_styles(doc.get("styles", {})), "word/_rels/document.xml.rels": _xmlbytes(word_rels)})


def _ppt_text_shape(parent, text, ident):
    sp = _element(parent, P, "sp"); nv = _element(sp, P, "nvSpPr")
    _element(nv, P, "cNvPr", {"id": str(ident), "name": "Text %d" % ident}); _element(nv, P, "cNvSpPr"); _element(nv, P, "nvPr")
    tx = _element(sp, P, "txBody"); _element(tx, A, "bodyPr"); _element(tx, A, "lstStyle")
    para = _element(tx, A, "p"); run = _element(para, A, "r"); _element(run, A, "rPr", {"lang": "en-US"}); t = _element(run, A, "t"); t.text = str(text)
    _element(para, A, "endParaRPr", {"lang": "en-US"})


def _ppt_slide(slide):
    root = ET.Element(_q(P, "sld")); cs = _element(root, P, "cSld"); tree = _element(cs, P, "spTree")
    nv = _element(tree, P, "nvGrpSpPr"); _element(nv, P, "cNvPr", {"id": "1", "name": ""}); _element(nv, P, "cNvGrpSpPr"); _element(nv, P, "nvGrpSpPr")
    _element(_element(tree, P, "grpSpPr"), A, "xfrm")
    vals = [slide.get("title") or ""]
    for b in slide.get("blocks", []):
        if b.get("type") == "table": vals.extend([" | ".join(x) for x in ([b.get("header", [])] if b.get("header") else []) + b.get("rows", [])])
        elif b.get("type") == "list": vals.extend(b.get("items", []))
        else: vals.append(b.get("text", b.get("alt", "")))
    for i, value in enumerate((v for v in vals if v), 2): _ppt_text_shape(tree, value, i)
    _element(root, P, "clrMapOvr")
    return _xmlbytes(root)


def _ppt_slides(doc):
    if doc.get("type") == "deck": return list(doc.get("slides", []))
    slides, current = [], None
    for b in doc.get("blocks", []):
        if b.get("type") == "heading" and b.get("level", 1) == 1:
            current = {"index": len(slides)+1, "role": "cover" if not slides else "content", "layout": "title_body", "title": b.get("text"), "blocks": []}; slides.append(current)
        else:
            if current is None:
                current = {"index": 1, "role": "cover", "layout": "title_body", "title": None, "blocks": []}; slides.append(current)
            current["blocks"].append(b)
    return slides or [{"index": 1, "role": "cover", "layout": "title_body", "title": None, "blocks": []}]


def export_pptx(doc):
    slides = _ppt_slides(doc); theme = doc.get("theme", {}) if doc.get("type") == "deck" else {}
    aspect = theme.get("aspect", "16:9")
    cx, cy = (9144000, 6858000) if aspect == "4:3" else (12192000, 6858000)
    pres = ET.Element(_q(P, "presentation")); masters = _element(pres, P, "sldMasterIdLst")
    _element(masters, P, "sldMasterId", {"id": "2147483648", _q(R, "id"): "rIdMaster"})
    ids = _element(pres, P, "sldIdLst")
    for i, _ in enumerate(slides, 1): _element(ids, P, "sldId", {"id": str(255+i), _q(R, "id"): "rId%d" % i})
    _element(pres, P, "sldSz", {"cx": str(cx), "cy": str(cy), "type": "screen16x9" if aspect == "16:9" else "screen4x3"})
    parts = {"ppt/presentation.xml": _xmlbytes(pres)}
    rels = ET.Element(_q(REL, "Relationships")); _element(rels, REL, "Relationship", {"Id": "rIdMaster", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster", "Target": "slideMasters/slideMaster1.xml"})
    for i, s in enumerate(slides, 1):
        _element(rels, REL, "Relationship", {"Id": "rId%d" % i, "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide", "Target": "slides/slide%d.xml" % i})
        parts["ppt/slides/slide%d.xml" % i] = _ppt_slide(s)
        sr = ET.Element(_q(REL, "Relationships")); _element(sr, REL, "Relationship", {"Id": "rIdLayout", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout", "Target": "../slideLayouts/slideLayout1.xml"})
        parts["ppt/slides/_rels/slide%d.xml.rels" % i] = _xmlbytes(sr)
    parts["ppt/_rels/presentation.xml.rels"] = _xmlbytes(rels)
    master = ET.Element(_q(P, "sldMaster")); cs = _element(master, P, "cSld"); tree = _element(cs, P, "spTree")
    nv = _element(tree, P, "nvGrpSpPr"); _element(nv, P, "cNvPr", {"id": "1", "name": ""}); _element(nv, P, "cNvGrpSpPr"); _element(nv, P, "nvGrpSpPr"); _element(_element(tree, P, "grpSpPr"), A, "xfrm")
    _element(master, P, "clrMap", {k: k for k in ("accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "bg1", "tx1", "bg2", "tx2", "folHlink", "hlink")})
    parts["ppt/slideMasters/slideMaster1.xml"] = _xmlbytes(master)
    mr = ET.Element(_q(REL, "Relationships")); _element(mr, REL, "Relationship", {"Id": "rIdLayout", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout", "Target": "../slideLayouts/slideLayout1.xml"}); _element(mr, REL, "Relationship", {"Id": "rIdTheme", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme", "Target": "../theme/theme1.xml"})
    parts["ppt/slideMasters/_rels/slideMaster1.xml.rels"] = _xmlbytes(mr)
    layout = ET.Element(_q(P, "sldLayout"), {"type": "blank", "preserve": "1"}); lc = _element(layout, P, "cSld"); lt = _element(lc, P, "spTree"); ln = _element(lt, P, "nvGrpSpPr"); _element(ln, P, "cNvPr", {"id": "1", "name": ""}); _element(ln, P, "cNvGrpSpPr"); _element(ln, P, "nvGrpSpPr"); _element(_element(lt, P, "grpSpPr"), A, "xfrm"); _element(layout, P, "clrMapOvr")
    parts["ppt/slideLayouts/slideLayout1.xml"] = _xmlbytes(layout)
    lr = ET.Element(_q(REL, "Relationships")); _element(lr, REL, "Relationship", {"Id": "rIdMaster", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster", "Target": "../slideMasters/slideMaster1.xml"}); parts["ppt/slideLayouts/_rels/slideLayout1.xml.rels"] = _xmlbytes(lr)
    colors = theme.get("colors", {}); th = ET.Element(_q(A, "theme"), {"name": "Test double"}); elems = _element(th, A, "themeElements"); cs = _element(elems, A, "clrScheme", {"name": "Test double"})
    for key, val in (("dk1", "1F2937"), ("lt1", "FFFFFF"), ("dk2", "44546A"), ("lt2", "E7E6E6"), ("accent1", "4472C4"), ("accent2", "ED7D31")):
        node = _element(cs, A, key); _element(node, A, "srgbClr", {"val": str(colors.get(key, val)).lstrip("#")})
    fs = _element(elems, A, "fontScheme", {"name": "Test double"}); major = _element(fs, A, "majorFont"); _element(major, A, "latin", {"typeface": theme.get("fonts", {}).get("heading", "Aptos Display")}); minor = _element(fs, A, "minorFont"); _element(minor, A, "latin", {"typeface": theme.get("fonts", {}).get("body", "Aptos")}); fmt = _element(elems, A, "fmtScheme", {"name": "Test double"})
    for key in ("fillStyleLst", "lnStyleLst", "effectStyleLst", "bgFillStyleLst"): _element(fmt, A, key)
    parts["ppt/theme/theme1.xml"] = _xmlbytes(th)
    rootrels = ET.Element(_q(REL, "Relationships")); _element(rootrels, REL, "Relationship", {"Id": "rId1", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument", "Target": "ppt/presentation.xml"}); parts["_rels/.rels"] = _xmlbytes(rootrels)
    ct = "http://schemas.openxmlformats.org/package/2006/content-types"; types = ET.Element(_q(ct, "Types")); _element(types, ct, "Default", {"Extension": "rels", "ContentType": "application/vnd.openxmlformats-package.relationships+xml"}); _element(types, ct, "Default", {"Extension": "xml", "ContentType": "application/xml"})
    overrides = [("ppt/presentation.xml", "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"), ("ppt/slideMasters/slideMaster1.xml", "application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"), ("ppt/slideLayouts/slideLayout1.xml", "application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"), ("ppt/theme/theme1.xml", "application/vnd.openxmlformats-officedocument.theme+xml")]
    overrides.extend(("ppt/slides/slide%d.xml" % i, "application/vnd.openxmlformats-officedocument.presentationml.slide+xml") for i in range(1, len(slides)+1))
    for name, typ in overrides: _element(types, ct, "Override", {"PartName": "/"+name, "ContentType": typ})
    parts["[Content_Types].xml"] = _xmlbytes(types)
    return _pkg(parts)


