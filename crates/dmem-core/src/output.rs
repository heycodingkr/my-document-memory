use crate::validate_content;
use dmem_contracts::*;
use std::io::{Cursor, Write};
pub struct Export {
    pub bytes: Vec<u8>,
    pub mime: &'static str,
    pub extension: &'static str,
}
pub fn escape(s: &str) -> String {
    s.chars()
        .filter(|c| !c.is_control() || "\n\r\t".contains(*c))
        .collect::<String>()
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&apos;")
}
fn md(c: &Content) -> String {
    let mut out = Vec::new();
    for b in &c.blocks {
        out.push(match b {
            Block::Heading { text, level } => format!("{} {text}", "#".repeat(*level as usize)),
            Block::Paragraph { text } => text.clone(),
            Block::Quote { text, .. } => text
                .lines()
                .map(|s| format!("> {s}"))
                .collect::<Vec<_>>()
                .join("\n"),
            Block::List { items } => items
                .iter()
                .map(|s| format!("- {s}"))
                .collect::<Vec<_>>()
                .join("\n"),
            Block::Table { rows } => {
                let mut lines = Vec::new();
                for (i, row) in rows.iter().enumerate() {
                    let cells = row
                        .iter()
                        .map(|s| s.replace('|', "\\|").replace('\n', "<br>"))
                        .collect::<Vec<_>>();
                    lines.push(format!("| {} |", cells.join(" | ")));
                    if i == 0 {
                        lines.push(format!("| {} |", vec!["---"; row.len()].join(" | ")));
                    }
                }
                lines.join("\n")
            }
        })
    }
    for s in &c.slides {
        out.push(format!("## {}\n\n{}", s.title, s.body))
    }
    out.join("\n\n")
}
pub fn export(title: &str, family: Family, c: &Content, format: &str) -> Result<Export, Fault> {
    validate_content(family, c)?;
    let (bytes, mime, extension) = match format {
        "md" | "markdown" => (
            format!("# {title}\n\n{}\n", md(c)).into_bytes(),
            "text/markdown; charset=utf-8",
            "md",
        ),
        "html" => {
            let mut body = format!("<h1>{}</h1>", escape(title));
            for b in &c.blocks {
                body.push_str(&match b {
                    Block::Heading { text, level } => {
                        format!("<h{level}>{}</h{level}>", escape(text))
                    }
                    Block::Paragraph { text } => format!("<p>{}</p>", escape(text)),
                    Block::Quote { text, .. } => {
                        format!("<blockquote>{}</blockquote>", escape(text))
                    }
                    Block::List { items } => format!(
                        "<ul>{}</ul>",
                        items
                            .iter()
                            .map(|s| format!("<li>{}</li>", escape(s)))
                            .collect::<String>()
                    ),
                    Block::Table { rows } => format!(
                        "<table>{}</table>",
                        rows.iter()
                            .map(|r| format!(
                                "<tr>{}</tr>",
                                r.iter()
                                    .map(|s| format!("<td>{}</td>", escape(s)))
                                    .collect::<String>()
                            ))
                            .collect::<String>()
                    ),
                })
            }
            for s in &c.slides {
                body.push_str(&format!(
                    "<section class=\"slide\"><h2>{}</h2><p>{}</p></section>",
                    escape(&s.title),
                    escape(&s.body)
                ))
            }
            (format!("<!doctype html><html lang=\"ko\"><head><meta charset=\"UTF-8\"><meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'\"><title>{}</title><style>body{{font-family:system-ui;max-width:820px;margin:48px auto;padding:24px;color:#20312d}}p,blockquote{{white-space:pre-wrap}}table{{border-collapse:collapse}}td{{border:1px solid #ccd5d0;padding:8px}}.slide{{break-after:page;border:1px solid #ddd;padding:32px;min-height:380px}}</style></head><body>{body}</body></html>",escape(title)).into_bytes(),"text/html; charset=utf-8","html")
        }
        "docx" if family == Family::Document => (
            docx(title, c)?,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "docx",
        ),
        "pptx" if family == Family::Deck => (
            pptx(c)?,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "pptx",
        ),
        _ => return Err(Fault::UnsupportedFormat),
    };
    Ok(Export {
        bytes,
        mime,
        extension,
    })
}
fn zip_files(files: Vec<(String, String)>) -> Result<Vec<u8>, Fault> {
    let mut z = zip::ZipWriter::new(Cursor::new(Vec::new()));
    let options = zip::write::SimpleFileOptions::default()
        .compression_method(zip::CompressionMethod::Deflated);
    for (name, text) in files {
        z.start_file(name, options).map_err(|_| Fault::Internal)?;
        z.write_all(text.as_bytes()).map_err(|_| Fault::Internal)?
    }
    Ok(z.finish().map_err(|_| Fault::Internal)?.into_inner())
}
const RELNS: &str = "http://schemas.openxmlformats.org/package/2006/relationships";
const OFFREL: &str = "http://schemas.openxmlformats.org/officeDocument/2006/relationships";
const CTNS: &str = "http://schemas.openxmlformats.org/package/2006/content-types";
fn rels(s: &str) -> String {
    format!(
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?><Relationships xmlns=\"{RELNS}\">{s}</Relationships>"
    )
}
fn rel(id: &str, kind: &str, target: &str) -> String {
    format!("<Relationship Id=\"{id}\" Type=\"{OFFREL}/{kind}\" Target=\"{target}\"/>")
}
fn paragraph(text: &str, style: Option<String>) -> String {
    let props = style
        .map(|s| format!("<w:pPr><w:pStyle w:val=\"{s}\"/></w:pPr>"))
        .unwrap_or_default();
    format!(
        "<w:p>{props}<w:r><w:t xml:space=\"preserve\">{}</w:t></w:r></w:p>",
        escape(text)
    )
}
fn docx(title: &str, c: &Content) -> Result<Vec<u8>, Fault> {
    let mut body = paragraph(title, Some("Title".into()));
    for b in &c.blocks {
        body.push_str(&match b {
            Block::Heading { text, level } => paragraph(text, Some(format!("Heading{level}"))),
            Block::Paragraph { text } | Block::Quote { text, .. } => paragraph(text, None),
            Block::List { items } => items
                .iter()
                .map(|s| paragraph(&format!("• {s}"), None))
                .collect::<String>(),
            Block::Table { rows } => format!(
                "<w:tbl><w:tblPr><w:tblW w:w=\"0\" w:type=\"auto\"/></w:tblPr>{}</w:tbl>",
                rows.iter()
                    .map(|r| format!(
                        "<w:tr>{}</w:tr>",
                        r.iter()
                            .map(|s| format!("<w:tc>{}</w:tc>", paragraph(s, None)))
                            .collect::<String>()
                    ))
                    .collect::<String>()
            ),
        })
    }
    let styles=(1..=6).map(|n|format!("<w:style w:type=\"paragraph\" w:styleId=\"Heading{n}\"><w:name w:val=\"heading {n}\"/><w:basedOn w:val=\"Normal\"/><w:rPr><w:b/><w:sz w:val=\"{}\"/></w:rPr></w:style>",36-n*2)).collect::<String>();
    let document = format!(
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?><w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body>{body}<w:sectPr><w:pgSz w:w=\"11906\" w:h=\"16838\"/><w:pgMar w:top=\"1134\" w:right=\"1134\" w:bottom=\"1134\" w:left=\"1134\"/></w:sectPr></w:body></w:document>"
    );
    zip_files(vec![
        (
            "[Content_Types].xml".into(),
            format!(
                "<Types xmlns=\"{CTNS}\"><Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/><Default Extension=\"xml\" ContentType=\"application/xml\"/><Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/><Override PartName=\"/word/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml\"/></Types>"
            ),
        ),
        (
            "_rels/.rels".into(),
            rels(&rel("rId1", "officeDocument", "word/document.xml")),
        ),
        ("word/document.xml".into(), document),
        (
            "word/_rels/document.xml.rels".into(),
            rels(&rel("rId1", "styles", "styles.xml")),
        ),
        (
            "word/styles.xml".into(),
            format!(
                "<w:styles xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:style w:type=\"paragraph\" w:default=\"1\" w:styleId=\"Normal\"><w:name w:val=\"Normal\"/></w:style><w:style w:type=\"paragraph\" w:styleId=\"Title\"><w:name w:val=\"Title\"/></w:style>{styles}</w:styles>"
            ),
        ),
    ])
}
const PNS: &str = "http://schemas.openxmlformats.org/presentationml/2006/main";
const ANS: &str = "http://schemas.openxmlformats.org/drawingml/2006/main";
fn group() -> &'static str {
    "<p:nvGrpSpPr><p:cNvPr id=\"1\" name=\"\"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x=\"0\" y=\"0\"/><a:ext cx=\"0\" cy=\"0\"/><a:chOff x=\"0\" y=\"0\"/><a:chExt cx=\"0\" cy=\"0\"/></a:xfrm></p:grpSpPr>"
}
fn shape(id: u32, text: &str, y: u32, height: u32, size: u32) -> String {
    let paras=text.split('\n').map(|line|format!("<a:p><a:r><a:rPr lang=\"ko-KR\" sz=\"{size}\"/><a:t>{}</a:t></a:r><a:endParaRPr lang=\"ko-KR\"/></a:p>",escape(line))).collect::<String>();
    format!(
        "<p:sp><p:nvSpPr><p:cNvPr id=\"{id}\" name=\"Text {id}\"/><p:cNvSpPr txBox=\"1\"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x=\"700000\" y=\"{y}\"/><a:ext cx=\"10700000\" cy=\"{height}\"/></a:xfrm><a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom><a:noFill/></p:spPr><p:txBody><a:bodyPr wrap=\"square\"/><a:lstStyle/>{paras}</p:txBody></p:sp>"
    )
}
fn pptx(c: &Content) -> Result<Vec<u8>, Fault> {
    let mut ct = format!(
        "<Types xmlns=\"{CTNS}\"><Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/><Default Extension=\"xml\" ContentType=\"application/xml\"/><Override PartName=\"/ppt/presentation.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml\"/><Override PartName=\"/ppt/slideMasters/slideMaster1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml\"/><Override PartName=\"/ppt/slideLayouts/slideLayout1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml\"/>"
    );
    let mut ids = String::new();
    let mut relationships = rel("rIdM", "slideMaster", "slideMasters/slideMaster1.xml");
    let mut files = Vec::new();
    for (i, s) in c.slides.iter().enumerate() {
        let n = i + 1;
        ct.push_str(&format!("<Override PartName=\"/ppt/slides/slide{n}.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.presentationml.slide+xml\"/>"));
        ids.push_str(&format!("<p:sldId id=\"{}\" r:id=\"rId{n}\"/>", 256 + i));
        relationships.push_str(&rel(
            &format!("rId{n}"),
            "slide",
            &format!("slides/slide{n}.xml"),
        ));
        files.push((format!("ppt/slides/slide{n}.xml"),format!("<p:sld xmlns:p=\"{PNS}\" xmlns:a=\"{ANS}\" xmlns:r=\"{OFFREL}\"><p:cSld><p:spTree>{}{}{}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>",group(),shape(2,&s.title,500000,1000000,3200),shape(3,&s.body,1700000,4400000,1800))));
        files.push((
            format!("ppt/slides/_rels/slide{n}.xml.rels"),
            rels(&rel(
                "rId1",
                "slideLayout",
                "../slideLayouts/slideLayout1.xml",
            )),
        ));
    }
    ct.push_str("</Types>");
    files.extend([
 ("[Content_Types].xml".into(),ct),("_rels/.rels".into(),rels(&rel("rId1","officeDocument","ppt/presentation.xml"))),
 ("ppt/presentation.xml".into(),format!("<p:presentation xmlns:p=\"{PNS}\" xmlns:r=\"{OFFREL}\"><p:sldMasterIdLst><p:sldMasterId id=\"2147483648\" r:id=\"rIdM\"/></p:sldMasterIdLst><p:sldIdLst>{ids}</p:sldIdLst><p:sldSz cx=\"12192000\" cy=\"6858000\"/><p:notesSz cx=\"6858000\" cy=\"9144000\"/></p:presentation>")),
 ("ppt/_rels/presentation.xml.rels".into(),rels(&relationships)),
 ("ppt/slideLayouts/slideLayout1.xml".into(),format!("<p:sldLayout xmlns:p=\"{PNS}\" xmlns:a=\"{ANS}\" type=\"blank\" preserve=\"1\"><p:cSld name=\"Blank\"><p:spTree>{}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>",group())),
 ("ppt/slideLayouts/_rels/slideLayout1.xml.rels".into(),rels(&rel("rId1","slideMaster","../slideMasters/slideMaster1.xml"))),
 ("ppt/slideMasters/slideMaster1.xml".into(),format!("<p:sldMaster xmlns:p=\"{PNS}\" xmlns:a=\"{ANS}\" xmlns:r=\"{OFFREL}\"><p:cSld><p:spTree>{}</p:spTree></p:cSld><p:clrMap accent1=\"accent1\" accent2=\"accent2\" accent3=\"accent3\" accent4=\"accent4\" accent5=\"accent5\" accent6=\"accent6\" bg1=\"lt1\" bg2=\"lt2\" folHlink=\"folHlink\" hlink=\"hlink\" tx1=\"dk1\" tx2=\"dk2\"/><p:sldLayoutIdLst><p:sldLayoutId id=\"2147483649\" r:id=\"rId1\"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>",group())),
 ("ppt/slideMasters/_rels/slideMaster1.xml.rels".into(),rels(&rel("rId1","slideLayout","../slideLayouts/slideLayout1.xml")))
 ]);
    zip_files(files)
}
