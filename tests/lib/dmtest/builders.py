"""Deterministic standard-library builders for the format test fixtures."""
from io import BytesIO
import re
import zipfile
import xml.etree.ElementTree as ET

W="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
P="http://schemas.openxmlformats.org/presentationml/2006/main"
A="http://schemas.openxmlformats.org/drawingml/2006/main"
CT="http://schemas.openxmlformats.org/package/2006/content-types"
REL="http://schemas.openxmlformats.org/package/2006/relationships"
for prefix,uri in (("w",W),("r",R),("p",P),("a",A),("ct",CT),("rel",REL)):
    ET.register_namespace(prefix,uri)

_PNG=bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c636000020000050001a5f645400000000049454e44ae426082")
_WREL="http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
_PREL="http://schemas.openxmlformats.org/officeDocument/2006/relationships/"

def _tag(ns,name): return "{%s}%s"%(ns,name)
def _xml(el): return ET.tostring(el,encoding="utf-8",xml_declaration=True)
def _rels(items):
    root=ET.Element(_tag(REL,"Relationships"))
    for rid,typ,target,mode in items:
        attrs={"Id":rid,"Type":typ,"Target":target}
        if mode: attrs["TargetMode"]=mode
        ET.SubElement(root,_tag(REL,"Relationship"),attrs)
    return _xml(root)
def _zip(parts):
    out=BytesIO()
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(parts.items()):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3; info.external_attr=0o100600<<16
            z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    return out.getvalue()

def _page_xml(page):
    page=page or {}; sizes={"A4":(11906,16838),"Letter":(12240,15840),"A3":(16838,23811),"A5":(8391,11906),"Legal":(12240,20160)}
    size=page.get("size","A4"); width,height=sizes.get(size,sizes["A4"]); orient=page.get("orientation","portrait")
    if orient=="landscape": width,height=max(width,height),min(width,height)
    m=page.get("margins_mm",[25,20,25,20]); tw=lambda v:str(round(int(v)*1440/25.4))
    return ET.Element(_tag(W,"sectPr")),(width,height,[tw(x) for x in m],orient)

def _run(parent,text,bold=False,italic=False):
    r=ET.SubElement(parent,_tag(W,"r")); props=ET.SubElement(r,_tag(W,"rPr"))
    if bold: ET.SubElement(props,_tag(W,"b"))
    if italic: ET.SubElement(props,_tag(W,"i"))
    t=ET.SubElement(r,_tag(W,"t")); t.text=str(text); return r
def _paragraph(text="",style=None,runs=None):
    p=ET.Element(_tag(W,"p"))
    if style: ET.SubElement(ET.SubElement(p,_tag(W,"pPr")),_tag(W,"pStyle"),{_tag(W,"val"):style})
    for run in runs or [{"text":text}]: _run(p,run.get("text",""),run.get("bold",False),run.get("italic",False))
    return p
def _image_paragraph():
    ns="http://schemas.openxmlformats.org/drawingml/2006/main"; wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"; pic="http://schemas.openxmlformats.org/drawingml/2006/picture"
    p=ET.Element(_tag(W,"p")); r=ET.SubElement(p,_tag(W,"r")); d=ET.SubElement(r,_tag(W,"drawing")); inline=ET.SubElement(d,_tag(wp,"inline"))
    ET.SubElement(inline,_tag(wp,"extent"),{"cx":"914400","cy":"514350"}); ET.SubElement(inline,_tag(wp,"docPr"),{"id":"1","name":"Fixture image"})
    graphic=ET.SubElement(inline,_tag(ns,"graphic")); gd=ET.SubElement(graphic,_tag(ns,"graphicData"),{"uri":pic})
    pc=ET.SubElement(gd,_tag(pic,"pic")); nv=ET.SubElement(pc,_tag(pic,"nvPicPr")); ET.SubElement(nv,_tag(pic,"cNvPr"),{"id":"0","name":"fixture.png"}); ET.SubElement(nv,_tag(pic,"cNvPicPr"))
    fill=ET.SubElement(pc,_tag(pic,"blipFill")); ET.SubElement(fill,_tag(ns,"blip"),{_tag(R,"embed"):"rIdImage"}); stretch=ET.SubElement(fill,_tag(ns,"stretch")); ET.SubElement(stretch,_tag(ns,"fillRect"))
    sp=ET.SubElement(pc,_tag(pic,"spPr")); xfrm=ET.SubElement(sp,_tag(ns,"xfrm")); ET.SubElement(xfrm,_tag(ns,"off"),{"x":"0","y":"0"}); ET.SubElement(xfrm,_tag(ns,"ext"),{"cx":"914400","cy":"514350"})
    geom=ET.SubElement(sp,_tag(ns,"prstGeom"),{"prst":"rect"}); ET.SubElement(geom,_tag(ns,"avLst")); return p

def _doc_parts(blocks,page=None,styles=None,title=None,extra="",url="https://fixture.invalid/template.dotx"):
    styles=styles or {}; body=ET.Element(_tag(W,"document")); b=ET.SubElement(body,_tag(W,"body"))
    if title is not None: b.append(_paragraph(title,"Title"))
    image=False
    for block in blocks:
        typ=block.get("type"); txt=block.get("text","")
        if typ=="heading": b.append(_paragraph(txt,"Heading%d"%int(block.get("level",1))))
        elif typ=="paragraph": b.append(_paragraph(txt,runs=block.get("runs")))
        elif typ=="list":
            for i,item in enumerate(block.get("items",[]),1): b.append(_paragraph((str(i)+". " if block.get("ordered") else "• ")+str(item)))
        elif typ=="table":
            rows=(([block["header"]] if block.get("header") else [])+block.get("rows",[])); tbl=ET.SubElement(b,_tag(W,"tbl")); pr=ET.SubElement(tbl,_tag(W,"tblPr")); ET.SubElement(pr,_tag(W,"tblW"),{_tag(W,"w"):"0",_tag(W,"type"):"auto"})
            cols=max([len(row) for row in rows] or [1]); grid=ET.SubElement(tbl,_tag(W,"tblGrid"))
            for _ in range(cols): ET.SubElement(grid,_tag(W,"gridCol"),{_tag(W,"w"):"2400"})
            for row in rows:
                tr=ET.SubElement(tbl,_tag(W,"tr"))
                for cell in row:
                    tc=ET.SubElement(tr,_tag(W,"tc")); tc.append(_paragraph(str(cell)))
        elif typ in ("quote","callout"): b.append(_paragraph(txt,"Quote"))
        elif typ=="image": image=True; b.append(_image_paragraph())
        else: b.append(_paragraph(txt or str(block)))
    sect,vals=_page_xml(page); width,height,m,orient=vals; ET.SubElement(sect,_tag(W,"pgSz"),{_tag(W,"w"):str(width),_tag(W,"h"):str(height),_tag(W,"orient"):orient}); ET.SubElement(sect,_tag(W,"pgMar"),{_tag(W,"top"):m[0],_tag(W,"right"):m[1],_tag(W,"bottom"):m[2],_tag(W,"left"):m[3],_tag(W,"header"):"720",_tag(W,"footer"):"720",_tag(W,"gutter"):"0"})
    b.append(sect)
    rels=[("rIdStyles",_WREL+"styles","styles.xml",None)]
    parts={"[Content_Types].xml":_xml(_types("word/document.xml",extra)),"_rels/.rels":_rels([("rId1",_WREL+"officeDocument","word/document.xml",None)]),"word/document.xml":_xml(body),"word/styles.xml":_styles_xml(styles)}
    if image:
        rels.append(("rIdImage",_WREL+"image","media/image1.png",None)); parts["word/media/image1.png"]=_PNG
    if extra=="macro": parts["word/vbaProject.bin"]=b"MZ\x90\x00fixture-vba"
    if extra=="ole": parts["word/embeddings/oleObject1.bin"]=b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1fixture-ole"
    if extra=="external": rels.append(("rIdExternal",_WREL+"attachedTemplate",url,"External"))
    if extra=="dde":
        fld=ET.Element(_tag(W,"p")); rr=ET.SubElement(fld,_tag(W,"r")); ET.SubElement(rr,_tag(W,"fldChar"),{_tag(W,"fldCharType"):"begin"}); instr=ET.SubElement(ET.SubElement(fld,_tag(W,"r")),_tag(W,"instrText")); instr.text="DDEAUTO c:\\windows\\system32\\cmd.exe /c calc.exe"; ET.SubElement(ET.SubElement(fld,_tag(W,"r")),_tag(W,"fldChar"),{_tag(W,"fldCharType"):"end"}); b.insert(len(b)-1,fld); parts["word/document.xml"]=_xml(body)  # re-serialise: the field was added after the first pass
    if extra=="rich":
        rels += [("rIdComments",_WREL+"comments","comments.xml",None),("rIdFootnotes",_WREL+"footnotes","footnotes.xml",None)]
        parts["word/comments.xml"]=_xml(ET.fromstring('<w:comments xmlns:w="%s"><w:comment w:id="0" w:author="Fixture" w:date="2026-01-01T00:00:00Z"><w:p><w:r><w:t>Fixture review note</w:t></w:r></w:p></w:comment></w:comments>'%W))
        parts["word/footnotes.xml"]=_xml(ET.fromstring('<w:footnotes xmlns:w="%s"><w:footnote w:type="separator" w:id="-1"><w:p/></w:footnote><w:footnote w:id="1"><w:p><w:r><w:t>Fixture footnote</w:t></w:r></w:p></w:footnote></w:footnotes>'%W))
        parts["[Content_Types].xml"]=_xml(_types("word/document.xml","rich"))
    if extra=="ole": rels.append(("rIdOle",_WREL+"oleObject","embeddings/oleObject1.bin",None))
    if extra=="macro": rels.append(("rIdVba",_WREL+"vbaProject","vbaProject.bin",None))
    parts["word/_rels/document.xml.rels"]=_rels(rels)
    return parts

def _styles_xml(styles):
    root=ET.Element(_tag(W,"styles")); defaults={"Normal":{"name":"Normal"},"Title":{"name":"Title","basedOn":"Normal","size":32,"bold":True},"Heading1":{"name":"heading 1","basedOn":"Normal","size":28,"bold":True},"Heading2":{"name":"heading 2","basedOn":"Normal","size":24,"bold":True},"Heading3":{"name":"heading 3","basedOn":"Normal","size":20,"bold":True},"Quote":{"name":"Quote","basedOn":"Normal","italic":True}}
    for sid,props in {**defaults,**styles}.items():
        style=ET.SubElement(root,_tag(W,"style"),{_tag(W,"type"):"paragraph",_tag(W,"styleId"):sid}); ET.SubElement(style,_tag(W,"name"),{_tag(W,"val"):str(props.get("name",sid))})
        if props.get("basedOn"): ET.SubElement(style,_tag(W,"basedOn"),{_tag(W,"val"):str(props["basedOn"])})
        if props.get("bold") or props.get("italic") or props.get("size"):
            rp=ET.SubElement(style,_tag(W,"rPr"))
            if props.get("bold"): ET.SubElement(rp,_tag(W,"b"))
            if props.get("italic"): ET.SubElement(rp,_tag(W,"i"))
            if props.get("size"): ET.SubElement(rp,_tag(W,"sz"),{_tag(W,"val"):str(int(props["size"]))})
    return _xml(root)

def _types(main,extra=""):
    root=ET.Element(_tag(CT,"Types")); ET.SubElement(root,_tag(CT,"Default"),{"Extension":"rels","ContentType":"application/vnd.openxmlformats-package.relationships+xml"}); ET.SubElement(root,_tag(CT,"Default"),{"Extension":"xml","ContentType":"application/xml"}); ET.SubElement(root,_tag(CT,"Default"),{"Extension":"png","ContentType":"image/png"})
    if main.startswith("word/"):
        typ="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml" if extra!="macro" else "application/vnd.ms-word.document.macroEnabled.main+xml"
        for part,ct in [(main,typ),("word/styles.xml","application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml")]: ET.SubElement(root,_tag(CT,"Override"),{"PartName":"/"+part,"ContentType":ct})
        if extra=="rich":
            for part,ct in [("word/comments.xml","application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"),("word/footnotes.xml","application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml")]: ET.SubElement(root,_tag(CT,"Override"),{"PartName":"/"+part,"ContentType":ct})
        if extra=="macro": ET.SubElement(root,_tag(CT,"Override"),{"PartName":"/word/vbaProject.bin","ContentType":"application/vnd.ms-office.vbaProject"})
    return root

def _build_docx(blocks,page=None,styles=None,title=None,extra="",url="https://fixture.invalid/template.dotx"):
    return _zip(_doc_parts(blocks,page,styles,title,extra,url))
def docx(blocks,page=None,styles=None):
    """Build a deterministic minimal DOCX from StandardDoc document blocks."""
    return _build_docx(blocks,page,styles)
def tpl01():
    blocks=[{"type":"heading","level":1,"text":s} for s in ("요약","지표","위험","요청")]
    blocks.insert(1,{"type":"table","header":["항목","목표","실적"],"rows":[["매출","100","92"],["활성 사용자","500","476"]]})
    return _build_docx(blocks,{"size":"Letter","orientation":"portrait","margins_mm":[25,20,25,20]}, {"Title":{"name":"Title","size":32,"bold":True},"Heading1":{"name":"heading 1","basedOn":"Normal","size":28,"bold":True},"Normal":{"name":"Normal","size":22}},title="월간 운영 보고서")
def evil_docx(kind,url="https://fixture.invalid/attached-template.dotx"):
    if kind not in ("macro","ole","external","dde"): raise ValueError("kind must be macro, ole, external, or dde")
    return _build_docx([{"type":"paragraph","text":"안전성 테스트 문서"}],extra=kind,url=url)
def rich_lossy_docx():
    return _build_docx([{"type":"heading","level":1,"text":"손실 변환 시험"},{"type":"image","alt":"도표","ref":"sha256:fixture-image"}],extra="rich")

def _slide_text(slide):
    out=[slide.get("title") or ""]
    for b in slide.get("blocks",[]):
        if b.get("type")=="table": out += [" | ".join(x) for x in (([b["header"]] if b.get("header") else [])+b.get("rows",[]))]
        elif b.get("type")=="list": out += [str(x) for x in b.get("items",[])]
        elif b.get("type")=="image": out += [b.get("alt","")]
        else: out += [b.get("text","")]
    return [x for x in out if x]
def _shape(text,ident):
    sp=ET.Element(_tag(P,"sp")); nv=ET.SubElement(sp,_tag(P,"nvSpPr")); ET.SubElement(nv,_tag(P,"cNvPr"),{"id":str(ident),"name":"Text %d"%ident}); ET.SubElement(nv,_tag(P,"cNvSpPr")); ET.SubElement(nv,_tag(P," nvPr".strip()))
    body=ET.SubElement(sp,_tag(P,"txBody")); ET.SubElement(body,_tag(A,"bodyPr")); ET.SubElement(body,_tag(A,"lstStyle")); para=ET.SubElement(body,_tag(A,"p")); run=ET.SubElement(para,_tag(A,"r")); ET.SubElement(run,_tag(A,"rPr"),{"lang":"en-US"}); t=ET.SubElement(run,_tag(A,"t")); t.text=str(text); ET.SubElement(para,_tag(A,"endParaRPr"),{"lang":"en-US"}); return sp
def _slide_xml(slide):
    root=ET.Element(_tag(P,"sld"),{_tag(A,"colorMapOvr"):""}); tree=ET.SubElement(root,_tag(P,"cSld")); st=ET.SubElement(tree,_tag(P,"spTree")); nv=ET.SubElement(st,_tag(P,"nvGrpSpPr")); ET.SubElement(nv,_tag(P,"cNvPr"),{"id":"1","name":""}); ET.SubElement(nv,_tag(P,"cNvGrpSpPr")); ET.SubElement(nv,_tag(P,"nvGrpSpPr")); xf=ET.SubElement(st,_tag(P,"grpSpPr")); ET.SubElement(xf,_tag(A,"xfrm"))
    for n,text in enumerate(_slide_text(slide),2): st.append(_shape(text,n))
    ET.SubElement(root,_tag(P,"clrMapOvr")); return _xml(root)
def _theme_xml(theme):
    colors={"dk1":"1F2937","lt1":"FFFFFF","dk2":"44546A","lt2":"E7E6E6","accent1":"4472C4","accent2":"ED7D31","accent3":"70AD47","accent4":"FFC000","accent5":"5B9BD5","accent6":"A5A5A5","hlink":"0563C1","folHlink":"954F72"}; colors.update(theme.get("colors",{}))
    root=ET.Element(_tag(A,"theme"),{"name":"Fixture theme"}); el=ET.SubElement(root,_tag(A,"themeElements")); cs=ET.SubElement(el,_tag(A,"clrScheme"),{"name":"Fixture"})
    for key,value in colors.items():
        node=ET.SubElement(cs,_tag(A,key)); value=str(value).lstrip("#"); ET.SubElement(node,_tag(A,"srgbClr"),{"val":value})
    fs=ET.SubElement(el,_tag(A,"fontScheme"),{"name":"Fixture"}); major=ET.SubElement(fs,_tag(A,"majorFont")); ET.SubElement(major,_tag(A,"latin"),{"typeface":theme.get("fonts",{}).get("heading","Aptos Display")}); minor=ET.SubElement(fs,_tag(A,"minorFont")); ET.SubElement(minor,_tag(A,"latin"),{"typeface":theme.get("fonts",{}).get("body","Aptos")}); fmt=ET.SubElement(el,_tag(A,"fmtScheme"),{"name":"Fixture"})
    for name in ("fillStyleLst","lnStyleLst","effectStyleLst","bgFillStyleLst"): ET.SubElement(fmt,_tag(A,name))
    return _xml(root)
def _make_pptx(slides,theme=None,rich=False):
    theme=theme or {}; aspect=theme.get("aspect","16:9"); cx,cy=(12192000,6858000) if aspect=="16:9" else ((9144000,6858000) if aspect=="4:3" else (12192000,6858000))
    pres=ET.Element(_tag(P,"presentation")); masters=ET.SubElement(pres,_tag(P,"sldMasterIdLst")); ET.SubElement(masters,_tag(P,"sldMasterId"),{"id":"2147483648",_tag(R,"id"):"rIdMaster"}); ids=ET.SubElement(pres,_tag(P,"sldIdLst"))
    for i,_ in enumerate(slides,1): ET.SubElement(ids,_tag(P,"sldId"),{"id":str(255+i),_tag(R,"id"):"rId%d"%i})
    ET.SubElement(pres,_tag(P,"sldSz"),{"cx":str(cx),"cy":str(cy),"type":"screen16x9" if aspect=="16:9" else "screen4x3"}); ET.SubElement(pres,_tag(P,"notesSz"),{"cx":"6858000","cy":"9144000"})
    parts={"[Content_Types].xml":_xml(_ppt_types(len(slides),rich)),"_rels/.rels":_rels([("rId1",_PREL+"officeDocument","ppt/presentation.xml",None)]),"ppt/presentation.xml":_xml(pres),"ppt/_rels/presentation.xml.rels":_rels([("rIdMaster",_PREL+"slideMaster","slideMasters/slideMaster1.xml",None)]+[("rId%d"%i,_PREL+"slide","slides/slide%d.xml"%i,None) for i in range(1,len(slides)+1)]),"ppt/theme/theme1.xml":_theme_xml(theme)}
    for i,slide in enumerate(slides,1):
        parts["ppt/slides/slide%d.xml"%i]=_slide_xml(slide); parts["ppt/slides/_rels/slide%d.xml.rels"%i]=_rels([("rIdLayout",_PREL+"slideLayout","../slideLayouts/slideLayout1.xml",None)])
    master=ET.Element(_tag(P,"sldMaster")); cs=ET.SubElement(master,_tag(P,"cSld")); sp=ET.SubElement(cs,_tag(P,"spTree")); nv=ET.SubElement(sp,_tag(P,"nvGrpSpPr")); ET.SubElement(nv,_tag(P,"cNvPr"),{"id":"1","name":""}); ET.SubElement(nv,_tag(P,"cNvGrpSpPr")); ET.SubElement(nv,_tag(P,"nvGrpSpPr")); ET.SubElement(ET.SubElement(sp,_tag(P,"grpSpPr")),_tag(A,"xfrm")); ET.SubElement(master,_tag(P,"clrMap"),{k:k for k in ("accent1","accent2","accent3","accent4","accent5","accent6","bg1","tx1","bg2","tx2","folHlink","hlink")}); ET.SubElement(master,_tag(P,"sldLayoutIdLst")); parts["ppt/slideMasters/slideMaster1.xml"]=_xml(master); parts["ppt/slideMasters/_rels/slideMaster1.xml.rels"]=_rels([("rIdLayout",_PREL+"slideLayout","../slideLayouts/slideLayout1.xml",None),("rIdTheme",_PREL+"theme","../theme/theme1.xml",None)])
    layout=ET.Element(_tag(P,"sldLayout"),{"type":"blank","preserve":"1"}); c=ET.SubElement(layout,_tag(P,"cSld")); g=ET.SubElement(c,_tag(P,"spTree")); n=ET.SubElement(g,_tag(P,"nvGrpSpPr")); ET.SubElement(n,_tag(P,"cNvPr"),{"id":"1","name":""}); ET.SubElement(n,_tag(P,"cNvGrpSpPr")); ET.SubElement(n,_tag(P,"nvGrpSpPr")); ET.SubElement(ET.SubElement(g,_tag(P,"grpSpPr")),_tag(A,"xfrm")); ET.SubElement(layout,_tag(P,"clrMapOvr")); parts["ppt/slideLayouts/slideLayout1.xml"]=_xml(layout); parts["ppt/slideLayouts/_rels/slideLayout1.xml.rels"]=_rels([("rIdMaster",_PREL+"slideMaster","../slideMasters/slideMaster1.xml",None)])
    if rich:
        parts["ppt/media/image1.png"]=_PNG; parts["ppt/charts/chart1.xml"]=_xml(ET.fromstring('<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"><c:chart><c:plotArea><c:layout/></c:plotArea></c:chart></c:chartSpace>'))
        parts["ppt/comments/comment1.xml"]=_xml(ET.fromstring('<p:cmLst xmlns:p="%s"><p:cm authorId="0" dt="2026-01-01T00:00:00Z" idx="1"><p:p><p:r><p:t>Fixture comment</p:t></p:r></p:p></p:cm></p:cmLst>'%P)); parts["ppt/commentAuthors.xml"]=_xml(ET.fromstring('<p:cmAuthorLst xmlns:p="%s"><p:cmAuthor id="0" name="Fixture" initials="FX" lastIdx="1"/></p:cmAuthorLst>'%P))
        # Relationships make the rich elements discoverable even to readers that ignore them.
        parts["ppt/slides/_rels/slide1.xml.rels"]=_rels([("rIdLayout",_PREL+"slideLayout","../slideLayouts/slideLayout1.xml",None),("rIdImage",_PREL+"image","../media/image1.png",None),("rIdChart",_PREL+"chart","../charts/chart1.xml",None),("rIdComments",_PREL+"comments","../comments/comment1.xml",None)])
    return _zip(parts)
def _ppt_types(count,rich=False):
    root=ET.Element(_tag(CT,"Types")); ET.SubElement(root,_tag(CT,"Default"),{"Extension":"rels","ContentType":"application/vnd.openxmlformats-package.relationships+xml"}); ET.SubElement(root,_tag(CT,"Default"),{"Extension":"xml","ContentType":"application/xml"}); ET.SubElement(root,_tag(CT,"Default"),{"Extension":"png","ContentType":"image/png"})
    overrides=[("ppt/presentation.xml","application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"),("ppt/slideMasters/slideMaster1.xml","application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"),("ppt/slideLayouts/slideLayout1.xml","application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"),("ppt/theme/theme1.xml","application/vnd.openxmlformats-officedocument.theme+xml")]
    overrides += [("ppt/slides/slide%d.xml"%i,"application/vnd.openxmlformats-officedocument.presentationml.slide+xml") for i in range(1,count+1)]
    if rich: overrides += [("ppt/charts/chart1.xml","application/vnd.openxmlformats-officedocument.drawingml.chart+xml"),("ppt/comments/comment1.xml","application/vnd.openxmlformats-officedocument.presentationml.comments+xml"),("ppt/commentAuthors.xml","application/vnd.openxmlformats-officedocument.presentationml.commentAuthors+xml")]
    for path,typ in overrides: ET.SubElement(root,_tag(CT,"Override"),{"PartName":"/"+path,"ContentType":typ})
    return root
def pptx(slides,theme=None):
    """Build a deterministic minimal PPTX from StandardDoc deck slides."""
    return _make_pptx(slides,theme)
def deck5():
    roles=[("표지","cover"),("문제","problem"),("해결","solution"),("시장","market"),("요청","ask")]
    slides=[{"index":i,"role":role,"layout":"title_body","title":title,"blocks":[{"type":"paragraph","text":body}]} for i,(title,role) in enumerate(roles,1) for body in ["My Document Memory — %s"%title]]
    return _make_pptx(slides,{"aspect":"16:9","fonts":{"heading":"Aptos Display","body":"Aptos"},"colors":{"accent1":"2855D9","accent2":"10A37F","accent3":"E8A838"}})
def rich_lossy_pptx():
    return _make_pptx([{"index":1,"role":"content","layout":"title_body","title":"손실 변환 시험","blocks":[{"type":"image","alt":"차트 미리보기","ref":"image1"}]}],{"aspect":"16:9"},True)

def pdf(pages_text,scanned=False):
    """Create a small PDF with literal text operators, or image-only scan pages."""
    pages=[pages_text] if isinstance(pages_text,str) else list(pages_text); pages=pages or [""]; objs=[None]
    def add(data): objs.append(data); return len(objs)-1
    catalog=add(b""); pages_id=add(b""); font=add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"); image=add(b"<< /Type /XObject /Subtype /Image /Width 1 /Height 1 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Length 3 >>\nstream\xff\xff\xff\nendstream") if scanned else None
    kidrefs=[]
    for value in pages:
        lines=str(value).splitlines() or [""]
        if scanned: stream=b"q 612 0 0 792 0 0 cm /Im1 Do Q"
        else:
            commands=["BT","/F1 12 Tf","50 750 Td"]
            for i,line in enumerate(lines):
                if i: commands.append("0 -16 Td")
                raw=line.encode("utf-8"); esc=raw.replace(b"\\",b"\\\\").replace(b"(",b"\\(").replace(b")",b"\\)")
                commands.append("("+esc.decode("latin-1")+") Tj")
            commands.append("ET"); stream="\n".join(commands).encode("latin-1")
        content=add(b"<< /Length %d >>\nstream\n"%len(stream)+stream+b"\nendstream")
        res=b"/XObject << /Im1 %d 0 R >>"%image if scanned else b"/Font << /F1 %d 0 R >>"%font
        page=add(b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 612 792] /Resources << %s >> /Contents %d 0 R >>"%(pages_id,res,content)); kidrefs.append(page)
    objs[catalog]=b"<< /Type /Catalog /Pages %d 0 R >>"%pages_id; objs[pages_id]=b"<< /Type /Pages /Kids [%s] /Count %d >>"%(b" ".join(b"%d 0 R"%x for x in kidrefs),len(kidrefs))
    out=bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"); offsets=[0]
    for i,obj in enumerate(objs[1:],1): offsets.append(len(out)); out.extend(b"%d 0 obj\n"%i+obj+b"\nendobj\n")
    xref=len(out); out.extend(b"xref\n0 %d\n0000000000 65535 f \n"%len(objs)); out.extend(b"".join(b"%010d 00000 n \n"%n for n in offsets[1:])); out.extend(b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n"%(len(objs),catalog,xref)); return bytes(out)

def zipbomb_docx():
    """Stream a highly compressible 100 MiB XML part into a tiny ZIP archive."""
    parts=_doc_parts([],extra=""); parts.pop("word/document.xml"); out=BytesIO()
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=9,allowZip64=True) as z:
        for name in sorted(list(parts)+["word/document.xml"]):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED; info.create_system=3; info.external_attr=0o100600<<16
            if name!="word/document.xml": z.writestr(info,parts[name],compresslevel=9); continue
            with z.open(info,"w",force_zip64=True) as f:
                f.write(("<?xml version='1.0' encoding='UTF-8'?><w:document xmlns:w='%s'><w:body><w:p><w:r><w:t>"%W).encode())
                chunk=b"x"*(1024*1024)
                for _ in range(100): f.write(chunk)
                f.write(b"</w:t></w:r></w:p><w:sectPr><w:pgSz w:w='11906' w:h='16838'/></w:sectPr></w:body></w:document>")
    return out.getvalue()

def resume_ko_md():
    return ("# 이력서\n\n## 인적사항\n- 이름: {{name}}\n- 이메일: {{email}}\n\n## 경력\n| 기간 | 회사 | 역할 |\n|---|---|---|\n| {{기간}} | {{회사}} | {{역할}} |\n\n## 학력\n- {{학교}}\n\n## 기술\nPython, 문서 자동화, 협업\n").encode("utf-8")
def invoice_kr_md():
    return ("# 세금계산서\n\n## 공급자\n- 상호: {{공급자명}}\n- 사업자등록번호: {{사업자번호}}\n\n## 거래 내역\n| 품목 | 수량 | 공급가액 |\n|---|---:|---:|\n| {{품목}} | {{수량}} | {{금액}}원 |\n\n## 합계\n부가가치세와 합계 금액을 기재합니다.\n").encode("utf-8")


def xlsx(sheets=None):
    """A deterministic minimal XLSX (inline strings): one sheet 'Quarters' with a header row by default."""
    sheets = sheets or [{"name": "Quarters", "header": ["Quarter", "Value"], "rows": [["Q1", "100"], ["Q2", "125"]]}]
    S = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    parts = {}
    wb = ET.Element("{%s}workbook" % S); lst = ET.SubElement(wb, "{%s}sheets" % S)
    rels = []
    for i, sheet in enumerate(sheets, 1):
        ET.SubElement(lst, "{%s}sheet" % S, {"name": sheet["name"], "sheetId": str(i), "{%s}id" % R: "rId%d" % i})
        rels.append(("rId%d" % i, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet", "worksheets/sheet%d.xml" % i, None))
        root = ET.Element("{%s}worksheet" % S); data = ET.SubElement(root, "{%s}sheetData" % S)
        for r, row in enumerate(([sheet["header"]] if sheet.get("header") else []) + sheet.get("rows", []), 1):
            tr = ET.SubElement(data, "{%s}row" % S, {"r": str(r)})
            for c, value in enumerate(row):
                cell = ET.SubElement(tr, "{%s}c" % S, {"r": "%s%d" % (chr(65 + c), r), "t": "inlineStr"})
                ET.SubElement(ET.SubElement(cell, "{%s}is" % S), "{%s}t" % S).text = str(value)
        parts["xl/worksheets/sheet%d.xml" % i] = _xml(root)
    types = ET.Element(_tag(CT, "Types")); ET.SubElement(types, _tag(CT, "Default"), {"Extension": "rels", "ContentType": "application/vnd.openxmlformats-package.relationships+xml"}); ET.SubElement(types, _tag(CT, "Default"), {"Extension": "xml", "ContentType": "application/xml"})
    ET.SubElement(types, _tag(CT, "Override"), {"PartName": "/xl/workbook.xml", "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"})
    parts.update({"[Content_Types].xml": _xml(types), "_rels/.rels": _rels([("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument", "xl/workbook.xml", None)]),
                  "xl/workbook.xml": _xml(wb), "xl/_rels/workbook.xml.rels": _rels(rels)})
    return _zip(parts)
