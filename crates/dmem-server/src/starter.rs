//! Original, additive starter structures and reusable writing/review guidance.
use dmem_contracts::{Fault, FormInput, Template, Visibility};
use dmem_core::{normalize_form, validate_title};
use rusqlite::{Connection, params};
use serde::Deserialize;
use std::collections::HashSet;

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Catalog {
    schema_version: u32,
    author: String,
    license: String,
    entries: Vec<Entry>,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Entry {
    id: String,
    locale: String,
    title: String,
    summary: String,
    doc_type: String,
    provider: String,
    sections: Vec<String>,
    tags: Vec<String>,
}

pub(crate) fn insert(db: &Connection) -> Result<(), Fault> {
    let catalog: Catalog =
        serde_json::from_str(include_str!("../../../contracts/starter-memories.v1.json"))
            .map_err(|_| Fault::Internal)?;
    if catalog.schema_version != 1
        || catalog.author != "My Document Memory"
        || catalog.license != "CC0-1.0"
    {
        return Err(Fault::Internal);
    }
    let mut seen = HashSet::new();
    for entry in catalog.entries {
        let valid_suffix = match entry.locale.as_str() {
            "en-US" => entry.id.ends_with(".en"),
            "ko-KR" => entry.id.ends_with(".ko"),
            _ => false,
        };
        if !valid_suffix
            || !seen.insert(entry.id.clone())
            || entry.id.len() > 100
            || entry.id.is_empty()
            || !entry
                .id
                .bytes()
                .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || b".-".contains(&c))
            || entry.summary.chars().count() > 600
            || !(1..=12).contains(&entry.sections.len())
            || entry.sections.iter().any(|s| {
                s.trim().is_empty() || s.chars().count() > 60 || s.chars().any(char::is_control)
            })
            || entry.tags.len() > 8
            || entry.tags.iter().any(|tag| {
                tag.is_empty() || tag.chars().count() > 32 || tag.chars().any(char::is_control)
            })
        {
            return Err(Fault::Internal);
        }
        validate_title(&entry.title)?;
        let template = Template {
            id: entry.id,
            version: 1,
            title: entry.title,
            summary: entry.summary,
            form: normalize_form(FormInput {
                provider: entry.provider,
                doc_type: entry.doc_type,
                locale: entry.locale,
                region: None,
                variant: None,
                page: None,
            })?,
            tags: entry.tags,
            sections: entry.sections,
            author: catalog.author.clone(),
            license: catalog.license.clone(),
            visibility: Visibility::Public,
            origin: None,
            attributions: vec![],
        };
        let payload = serde_json::to_string(&template).map_err(|_| Fault::Internal)?;
        db.execute("INSERT OR IGNORE INTO records(id,owner,kind,version,payload,updated_at) VALUES(?1,'@catalog','template',1,?2,0)",
            params![template.id, payload]).map_err(|_| Fault::Internal)?;
    }
    Ok(())
}
