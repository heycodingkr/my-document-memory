use dmem_contracts::*;
use quick_xml::{
    Reader,
    events::{BytesStart, Event},
};
use std::{
    collections::BTreeMap,
    io::{Cursor, Read},
};

#[derive(Debug)]
pub struct Extracted {
    pub format: String,
    pub blocks: Vec<Block>,
    pub slides: Vec<Slide>,
    pub spans: Vec<SourceSpan>,
}
pub fn extract(filename: &str, bytes: &[u8]) -> Result<Extracted, Fault> {
    if bytes.len() > MAX_UPLOAD {
        return Err(Fault::PayloadTooLarge);
    }
    let ext = filename
        .rsplit('.')
        .next()
        .unwrap_or("")
        .to_ascii_lowercase();
    let (format, blocks, slides) = match ext.as_str() {
        "txt" | "md" | "markdown" => {
            if bytes.len() > MAX_CONTENT {
                return Err(Fault::PayloadTooLarge);
            }
            let text = std::str::from_utf8(bytes).map_err(|_| Fault::InvalidInput)?;
            if text.contains('\0') {
                return Err(Fault::InvalidInput);
            }
            let mut blocks = Vec::new();
            for line in text.lines().map(str::trim).filter(|s| !s.is_empty()) {
                let level = line.chars().take_while(|c| *c == '#').count();
                if ext != "txt"
                    && (1..=6).contains(&level)
                    && line.as_bytes().get(level) == Some(&b' ')
                {
                    blocks.push(Block::Heading {
                        text: line[level + 1..].into(),
                        level: level as u8,
                    })
                } else if ext != "txt" && (line.starts_with("- ") || line.starts_with("* ")) {
                    if let Some(Block::List { items }) = blocks.last_mut() {
                        items.push(line[2..].into())
                    } else {
                        blocks.push(Block::List {
                            items: vec![line[2..].into()],
                        })
                    }
                } else {
                    blocks.push(Block::Paragraph { text: line.into() })
                }
            }
            (
                if ext == "txt" { "txt" } else { "markdown" }.to_owned(),
                blocks,
                vec![],
            )
        }
        "docx" => {
            let files = package(bytes)?;
            let xml = files.get("word/document.xml").ok_or(Fault::InvalidInput)?;
            ("docx".into(), docx_blocks(xml)?, vec![])
        }
        "pptx" => {
            let files = package(bytes)?;
            let presentation = files
                .get("ppt/presentation.xml")
                .ok_or(Fault::InvalidInput)?;
            let relations = files
                .get("ppt/_rels/presentation.xml.rels")
                .ok_or(Fault::InvalidInput)?;
            let mut targets = BTreeMap::new();
            let mut reader = Reader::from_str(relations);
            loop {
                match reader.read_event().map_err(|_| Fault::InvalidInput)? {
                    Event::Empty(e) | Event::Start(e)
                        if e.local_name().as_ref() == b"Relationship" =>
                    {
                        if let (Some(id), Some(target)) = (attr(&e, b"Id")?, attr(&e, b"Target")?) {
                            targets.insert(id, target);
                        }
                    }
                    Event::DocType(_) => return Err(Fault::InvalidInput),
                    Event::Eof => break,
                    _ => {}
                }
            }
            let mut ids = Vec::new();
            let mut reader = Reader::from_str(presentation);
            loop {
                match reader.read_event().map_err(|_| Fault::InvalidInput)? {
                    Event::Empty(e) | Event::Start(e) if e.local_name().as_ref() == b"sldId" => {
                        if let Some(id) = attr_exact(&e, b"r:id")? {
                            ids.push(id)
                        }
                    }
                    Event::DocType(_) => return Err(Fault::InvalidInput),
                    Event::Eof => break,
                    _ => {}
                }
            }
            if ids.len() > 100 {
                return Err(Fault::PayloadTooLarge);
            }
            let mut slides = Vec::new();
            for id in ids {
                let t = targets.get(&id).ok_or(Fault::InvalidInput)?;
                let path = if t.starts_with("/ppt/slides/") {
                    t.trim_start_matches('/').to_owned()
                } else if t.starts_with("slides/") {
                    format!("ppt/{t}")
                } else {
                    return Err(Fault::InvalidInput);
                };
                if path.contains("..") {
                    return Err(Fault::InvalidInput);
                }
                let xml = files.get(&path).ok_or(Fault::InvalidInput)?;
                let lines = paragraphs(xml)?;
                let title = lines
                    .first()
                    .cloned()
                    .unwrap_or_else(|| format!("Slide {}", slides.len() + 1));
                slides.push(Slide {
                    title,
                    body: lines.into_iter().skip(1).collect::<Vec<_>>().join("\n"),
                    citations: vec![],
                });
            }
            ("pptx".into(), vec![], slides)
        }
        _ => return Err(Fault::UnsupportedFormat),
    };
    let mut spans: Vec<SourceSpan> = blocks
        .iter()
        .enumerate()
        .filter_map(|(i, b)| {
            let text = b.text();
            if text.trim().is_empty() {
                None
            } else {
                Some(SourceSpan {
                    id: format!("p{}", i + 1),
                    location: format!("Paragraph {}", i + 1),
                    text,
                })
            }
        })
        .collect();
    for (i, s) in slides.iter().enumerate() {
        spans.push(SourceSpan {
            id: format!("s{}", i + 1),
            location: format!("Slide {}", i + 1),
            text: format!("{}\n{}", s.title, s.body),
        })
    }
    if spans.is_empty() || spans.iter().all(|s| s.text.trim().is_empty()) {
        return Err(Fault::ExtractEmpty("no_text"));
    }
    if spans.len() > 1000 || spans.iter().map(|s| s.text.len()).sum::<usize>() > MAX_CONTENT {
        return Err(Fault::PayloadTooLarge);
    }
    Ok(Extracted {
        format,
        blocks,
        slides,
        spans,
    })
}

fn package(bytes: &[u8]) -> Result<BTreeMap<String, String>, Fault> {
    let mut archive = zip::ZipArchive::new(Cursor::new(bytes)).map_err(|_| Fault::InvalidInput)?;
    if archive.len() > 512 {
        return Err(Fault::PayloadTooLarge);
    }
    let mut total = 0u64;
    let mut out = BTreeMap::new();
    for i in 0..archive.len() {
        let file = archive.by_index(i).map_err(|_| Fault::InvalidInput)?;
        total = total
            .checked_add(file.size())
            .ok_or(Fault::PayloadTooLarge)?;
        if total > 20 * 1024 * 1024 || file.size() > 5 * 1024 * 1024 {
            return Err(Fault::PayloadTooLarge);
        }
        let name = file.name().to_owned();
        if name.ends_with(".xml") || name.ends_with(".rels") {
            let mut buf = String::new();
            file.take(5 * 1024 * 1024 + 1)
                .read_to_string(&mut buf)
                .map_err(|_| Fault::InvalidInput)?;
            if buf.len() > 5 * 1024 * 1024 {
                return Err(Fault::PayloadTooLarge);
            }
            if out.insert(name, buf).is_some() {
                return Err(Fault::InvalidInput);
            }
        }
    }
    Ok(out)
}
fn attr_exact(e: &BytesStart<'_>, name: &[u8]) -> Result<Option<String>, Fault> {
    for a in e.attributes() {
        let a = a.map_err(|_| Fault::InvalidInput)?;
        if a.key.as_ref() == name {
            return Ok(Some(
                a.unescape_value()
                    .map_err(|_| Fault::InvalidInput)?
                    .into_owned(),
            ));
        }
    }
    Ok(None)
}
fn attr(e: &BytesStart<'_>, name: &[u8]) -> Result<Option<String>, Fault> {
    for a in e.attributes() {
        let a = a.map_err(|_| Fault::InvalidInput)?;
        if a.key.local_name().as_ref() == name {
            return Ok(Some(
                a.unescape_value()
                    .map_err(|_| Fault::InvalidInput)?
                    .into_owned(),
            ));
        }
    }
    Ok(None)
}
fn paragraphs(xml: &str) -> Result<Vec<String>, Fault> {
    let mut r = Reader::from_str(xml);
    let mut text = String::new();
    let mut lines = Vec::new();
    let mut in_text = false;
    loop {
        match r.read_event().map_err(|_| Fault::InvalidInput)? {
            Event::Start(e) if e.local_name().as_ref() == b"t" => in_text = true,
            Event::End(e) if e.local_name().as_ref() == b"t" => in_text = false,
            Event::Text(e) if in_text => {
                text.push_str(&e.unescape().map_err(|_| Fault::InvalidInput)?)
            }
            Event::End(e) if e.local_name().as_ref() == b"p" => {
                if !text.trim().is_empty() {
                    lines.push(std::mem::take(&mut text))
                }
            }
            Event::Empty(e) if e.local_name().as_ref() == b"br" => text.push('\n'),
            Event::DocType(_) => return Err(Fault::InvalidInput),
            Event::Eof => break,
            _ => {}
        }
    }
    Ok(lines)
}
fn docx_blocks(xml: &str) -> Result<Vec<Block>, Fault> {
    let mut r = Reader::from_str(xml);
    let mut blocks = Vec::new();
    let mut text = String::new();
    let mut heading = None;
    let mut in_text = false;
    let mut table = false;
    let mut rows = Vec::new();
    let mut row = Vec::new();
    let mut cell = String::new();
    loop {
        match r.read_event().map_err(|_| Fault::InvalidInput)? {
            Event::Start(e) => match e.local_name().as_ref() {
                b"tbl" => {
                    if table {
                        return Err(Fault::UnsupportedFormat);
                    }
                    table = true;
                    rows.clear()
                }
                b"tr" => row.clear(),
                b"tc" => cell.clear(),
                b"p" => {
                    text.clear();
                    heading = None
                }
                b"t" => in_text = true,
                b"pStyle" => {
                    heading = attr(&e, b"val")?
                        .and_then(|s| {
                            s.to_ascii_lowercase()
                                .strip_prefix("heading")
                                .and_then(|v| v.parse::<u8>().ok())
                        })
                        .filter(|v| (1..=6).contains(v));
                }
                _ => {}
            },
            Event::Empty(e) => match e.local_name().as_ref() {
                b"pStyle" => {
                    heading = attr(&e, b"val")?
                        .and_then(|s| {
                            s.to_ascii_lowercase()
                                .strip_prefix("heading")
                                .and_then(|v| v.parse::<u8>().ok())
                        })
                        .filter(|v| (1..=6).contains(v));
                }
                b"tab" => text.push('\t'),
                b"br" => text.push('\n'),
                _ => {}
            },
            Event::Text(e) if in_text => {
                text.push_str(&e.unescape().map_err(|_| Fault::InvalidInput)?)
            }
            Event::End(e) => match e.local_name().as_ref() {
                b"t" => in_text = false,
                b"p" => {
                    if table {
                        if !cell.is_empty() {
                            cell.push('\n')
                        }
                        cell.push_str(&text)
                    } else if !text.trim().is_empty() {
                        blocks.push(if let Some(level) = heading {
                            Block::Heading {
                                text: std::mem::take(&mut text),
                                level,
                            }
                        } else {
                            Block::Paragraph {
                                text: std::mem::take(&mut text),
                            }
                        })
                    }
                }
                b"tc" => row.push(std::mem::take(&mut cell)),
                b"tr" => rows.push(std::mem::take(&mut row)),
                b"tbl" => {
                    table = false;
                    blocks.push(Block::Table {
                        rows: std::mem::take(&mut rows),
                    })
                }
                _ => {}
            },
            Event::DocType(_) => return Err(Fault::InvalidInput),
            Event::Eof => break,
            _ => {}
        }
    }
    Ok(blocks)
}
