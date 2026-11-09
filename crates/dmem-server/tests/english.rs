use dmem_contracts::*;
use dmem_server::Store;
use serde_json::json;

fn template(db: &Store, locale: &str, deck: bool) -> Template {
    db.create_template(
        "english-owner",
        serde_json::from_value(json!({
            "title": if deck { "Pilot Review Slides" } else { "Pilot Review Brief" },
            "summary": "Synthetic English demonstration.",
            "form": { "provider": if deck { "pptx" } else { "docx" },
                      "doc_type": if deck { "report_deck" } else { "report" }, "locale": locale },
            "sections": ["Purpose", "Next Steps"], "tags": []
        }))
        .unwrap(),
    )
    .unwrap()
}
fn source(db: &Store) -> Source {
    db.import_source(
        "english-owner",
        "Pilot Notes".into(),
        "notes.md".into(),
        b"# Pilot notes\nThe review is scheduled for 15 November 2026.".to_vec(),
    )
    .unwrap()
}
fn draft(
    db: &Store,
    template: &Template,
    source: &Source,
    approved: bool,
) -> Result<Document, Fault> {
    db.create_document(
        "english-owner",
        CreateDocument {
            title: "Pilot Review".into(),
            template_id: template.id.clone(),
            source_ids: vec![source.id.clone()],
            outline_approved: approved,
        },
    )
}

#[test]
fn english_document_draft_uses_english_labels_and_keeps_citations() {
    let db = Store::open(":memory:").unwrap();
    let t = template(&db, "en-US", false);
    let s = source(&db);
    let doc = draft(&db, &t, &s, false).unwrap();
    assert!(doc.content.blocks.iter().any(
        |b| matches!(b, Block::Paragraph { text } if text == "{{Needs confirmation: Purpose}}")
    ));
    assert!(
        doc.content.blocks.iter().any(
            |b| matches!(b, Block::Heading { text, .. } if text == "Selected Source Excerpts")
        )
    );
    assert!(
        doc.content
            .blocks
            .iter()
            .any(|b| matches!(b, Block::Quote { text, citation: Some(c) }
            if text.contains("15 November 2026") && c.source_id == s.id && c.source_version == 1))
    );
    assert_eq!(doc.template.version, 1);
    assert_eq!(doc.source_versions[0].version, 1);
}

#[test]
fn english_deck_labels_follow_locale_and_require_outline_approval() {
    let db = Store::open(":memory:").unwrap();
    let t = template(&db, "en-GB", true);
    let s = source(&db);
    assert_eq!(draft(&db, &t, &s, false).unwrap_err(), Fault::InvalidInput);
    let doc = draft(&db, &t, &s, true).unwrap();
    assert_eq!(
        doc.content.slides[0].body,
        "{{Needs confirmation: Purpose}}"
    );
    assert_eq!(doc.content.slides[2].title, "Evidence: Pilot Notes");
    assert_eq!(doc.content.slides[2].citations[0].source_id, s.id);
}

#[test]
fn korean_document_labels_remain_korean() {
    let db = Store::open(":memory:").unwrap();
    let t = template(&db, "ko-KR", false);
    let s = source(&db);
    let doc = draft(&db, &t, &s, false).unwrap();
    assert!(
        doc.content
            .blocks
            .iter()
            .any(|b| matches!(b, Block::Paragraph { text } if text == "{{확인 필요: Purpose}}"))
    );
    assert!(
        doc.content
            .blocks
            .iter()
            .any(|b| matches!(b, Block::Heading { text, .. } if text == "선택한 참고자료 원문"))
    );
}

#[test]
fn english_catalog_is_additive_and_idempotent() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("catalog.sqlite3");
    let db = Store::open(&path).unwrap();
    let korean = db.template("english-owner", "meeting.minutes.ko").unwrap();
    let english = db.template("english-owner", "meeting.minutes.en").unwrap();
    assert_eq!(english.title, "Meeting Notes and Action Items");
    assert_eq!(english.form.locale, "en-US");
    let private = template(&db, "en-US", false);
    drop(db);
    let db = Store::open(&path).unwrap();
    assert_eq!(
        db.template("english-owner", &private.id).unwrap().title,
        private.title
    );
    assert_eq!(
        serde_json::to_value(db.template("english-owner", &korean.id).unwrap()).unwrap(),
        serde_json::to_value(korean).unwrap()
    );
    let search: Search =
        serde_json::from_value(json!({"locale":"en-US","visibility":"public"})).unwrap();
    assert_eq!(
        db.templates("english-owner", search).unwrap().items.len(),
        21.min(MAX_RESULTS)
    );
}

#[test]
fn locale_is_filtered_before_the_result_limit() {
    let db = Store::open(":memory:").unwrap();
    for _ in 0..25 {
        template(&db, "ko-KR", false);
    }
    let search: Search = serde_json::from_value(json!({"locale":"en-US"})).unwrap();
    let result = db.templates("english-owner", search).unwrap();
    assert_eq!(result.items.len(), 21.min(MAX_RESULTS));
    assert!(result.items.iter().all(|t| t.form.locale == "en-US"));
    assert!(result.items.iter().any(|t| t.id == "meeting.minutes.en"));
}
