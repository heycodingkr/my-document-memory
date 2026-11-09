use crate::{Store, web::Snapshot};
use dmem_contracts::*;
use rusqlite::{Connection, OptionalExtension, params};
use sha2::{Digest, Sha256};
use uuid::Uuid;
fn internal(_: impl std::fmt::Debug) -> Fault {
    Fault::Internal
}
pub(crate) fn origin(db: &Connection, owner: &str, id: &str) -> Result<Option<WebOrigin>, Fault> {
    let raw:Option<String>=db.query_row("SELECT w.payload FROM web_origins w JOIN records r ON r.id=w.record_id WHERE w.record_id=?1 AND (w.owner=?2 OR (r.owner='@catalog' AND r.kind='template'))",params![id,owner],|r|r.get(0)).optional().map_err(internal)?;
    raw.map(|s| serde_json::from_str(&s).map_err(internal))
        .transpose()
}
pub(crate) fn save_origin(db: &Connection, owner: &str, value: &WebOrigin) -> Result<(), Fault> {
    db.execute(
        "INSERT INTO web_origins(record_id,owner,payload) VALUES(?1,?2,?3)",
        params![
            value.record_id,
            owner,
            serde_json::to_string(value).map_err(internal)?
        ],
    )
    .map_err(internal)?;
    Ok(())
}
pub(crate) fn clone_origin(
    db: &Connection,
    owner: &str,
    from: &str,
    to: &str,
) -> Result<(), Fault> {
    if let Some(mut value) = origin(db, owner, from)? {
        value.record_id = to.into();
        save_origin(db, owner, &value)?;
    }
    Ok(())
}
impl Store {
    pub fn web_origin(&self, owner: &str, id: &str) -> Result<WebOrigin, Fault> {
        origin(&*self.db.lock().map_err(internal)?, owner, id)?.ok_or(Fault::NotFound)
    }
    pub(crate) fn web_import(
        &self,
        owner: &str,
        snapshot: Snapshot,
        input: WebImportInput,
        provenance: &str,
    ) -> Result<WebImportResult, Fault> {
        let mode = if input.kind == WebKind::Template {
            if input.copy_mode == Some(CopyMode::Full) {
                return Err(Fault::InvalidInput);
            }
            CopyMode::StructureOnly
        } else {
            input
                .copy_mode
                .unwrap_or(snapshot.preview.copy_policy_default)
        };
        if mode == CopyMode::Full && !snapshot.page.full_copy_allowed() {
            return Err(Fault::LicenseForbids);
        }
        let form = if let Some(form) = input.form {
            dmem_core::normalize_form(form)?
        } else {
            snapshot.preview.form.clone()
        };
        if form.family == Family::Sheet {
            return Err(Fault::UnsupportedFormat);
        }
        let title = input.title.unwrap_or(snapshot.preview.title.clone());
        dmem_core::validate_title(&title)?;
        if dmem_core::review::contains_secret(&title)
            || dmem_core::review::contains_injection(&title)
        {
            return Err(Fault::InvalidInput);
        }
        let identity = serde_json::to_vec(&(
            &snapshot.preview.canonical_url,
            &snapshot.preview.content_hash,
            &form,
            input.kind,
            mode,
            &title,
            provenance,
        ))
        .map_err(internal)?;
        let fingerprint = format!("{:x}", Sha256::digest(identity));
        let mut db = self.db.lock().map_err(internal)?;
        let tx = db.transaction().map_err(internal)?;
        let existing: Option<String> = tx
            .query_row(
                "SELECT record_id FROM web_import_keys WHERE owner=?1 AND fingerprint=?2",
                params![owner, fingerprint],
                |r| r.get(0),
            )
            .optional()
            .map_err(internal)?;
        let id = existing.clone().unwrap_or_else(|| {
            format!(
                "{}_{}",
                if input.kind == WebKind::Template {
                    "tpl"
                } else {
                    "src"
                },
                Uuid::new_v4().simple()
            )
        });
        let body_chars_removed = if mode == CopyMode::StructureOnly {
            snapshot
                .page
                .paragraphs
                .iter()
                .map(|s| s.chars().count())
                .sum()
        } else {
            0
        };
        let value = WebOrigin {
            record_id: id.clone(),
            canonical_url: snapshot.preview.canonical_url.clone(),
            license: snapshot.page.license.clone(),
            copy_policy: mode,
            provenance: provenance.into(),
            content_hash: snapshot.preview.content_hash.clone(),
            retrieved_at: snapshot.preview.fetched_at,
        };
        if existing.is_some() {
            let value = origin(&tx, owner, &id)?.ok_or(Fault::Internal)?;
            return Ok(WebImportResult {
                id,
                kind: input.kind,
                version: 1,
                created: false,
                origin: value,
                warnings: snapshot.preview.warnings,
                body_chars_removed,
            });
        }
        if input.kind == WebKind::Template {
            let mut sections = snapshot.page.outline.clone();
            for header in &snapshot.page.table_headers {
                if sections.len() < 12 {
                    sections.push(header.join(" / ").chars().take(60).collect());
                }
            }
            if sections.is_empty() {
                sections.push(title.chars().take(60).collect());
            }
            sections.truncate(12);
            let template = Template {
                id: id.clone(),
                version: 1,
                title,
                summary: "Imported document structure; check the original source before reuse."
                    .into(),
                form,
                sections,
                tags: vec!["web".into()],
                author: "External source".into(),
                license: snapshot.page.license.clone(),
                visibility: Visibility::Private,
                origin: None,
                attributions: vec![],
            };
            crate::store::insert(&tx, owner, "template", &id, &template)?;
        } else {
            let text = format!(
                "# {title}\n{}",
                snapshot.page.text(mode == CopyMode::StructureOnly)
            );
            let bytes = text.into_bytes();
            let extracted = dmem_core::extract("web.md", &bytes)?;
            let source = Source {
                id: id.clone(),
                version: 1,
                title,
                filename: "web.md".into(),
                format: extracted.format,
                checksum: format!("{:x}", Sha256::digest(&bytes)),
                spans: extracted.spans,
            };
            crate::store::insert(&tx, owner, "source", &id, &source)?;
            tx.execute(
                "INSERT INTO source_files(source_id,original) VALUES(?1,?2)",
                params![id, bytes],
            )
            .map_err(internal)?;
        }
        save_origin(&tx, owner, &value)?;
        tx.execute(
            "INSERT INTO web_import_keys(owner,fingerprint,record_id) VALUES(?1,?2,?3)",
            params![owner, fingerprint, id],
        )
        .map_err(internal)?;
        tx.commit().map_err(internal)?;
        Ok(WebImportResult {
            id,
            kind: input.kind,
            version: 1,
            created: true,
            origin: value,
            warnings: snapshot.preview.warnings,
            body_chars_removed,
        })
    }
}
