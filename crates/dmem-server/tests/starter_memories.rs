use dmem_contracts::{CreateDocument, MAX_RESULTS, Search};
use dmem_server::Store;
use serde_json::json;

const STARTERS: &[&str] = &[
    "project.brief",
    "product.requirements",
    "decision.memo",
    "research.brief",
    "incident.postmortem",
    "blog.technical",
    "project.plan",
    "presentation.executive",
    "memory.evidence",
    "memory.clear-writing",
    "memory.quality-review",
    "memory.slide-story",
];

#[test]
fn curated_starters_are_public_original_bilingual_and_usable() {
    let db = Store::open(":memory:").unwrap();
    for (suffix, locale) in [("en", "en-US"), ("ko", "ko-KR")] {
        for prefix in STARTERS {
            let id = format!("{prefix}.{suffix}");
            let template = db
                .template("@catalog", &id)
                .unwrap_or_else(|error| panic!("Missing {id}: {error:?}"));
            assert_eq!(template.form.locale, locale);
            assert_eq!(template.author, "My Document Memory");
            assert_eq!(template.license, "CC0-1.0");
            assert_eq!(template.version, 1);
            let search: Search = serde_json::from_value(
                json!({"q":template.title,"locale":locale,"visibility":"public"}),
            )
            .unwrap();
            assert!(
                db.templates("@catalog", search)
                    .unwrap()
                    .items
                    .iter()
                    .any(|entry| entry.id == template.id)
            );
            assert!(template.origin.is_none() && template.attributions.is_empty());
            assert!(template.sections.len() >= 5 && template.summary.chars().count() >= 70);
            let document = db
                .create_document(
                    "starter-test-owner",
                    CreateDocument {
                        title: format!("Example {}", template.title),
                        template_id: id,
                        source_ids: vec![],
                        outline_approved: true,
                    },
                )
                .unwrap();
            assert!(document.source_versions.is_empty());
            assert!(!document.content.blocks.is_empty() || !document.content.slides.is_empty());
        }
        let search: Search =
            serde_json::from_value(json!({"locale":locale,"visibility":"public"})).unwrap();
        let items = db.templates("@catalog", search).unwrap().items;
        assert_eq!(items.len(), 21.min(MAX_RESULTS));
    }
}

#[test]
fn reopening_starters_preserves_existing_versions_and_saved_documents() {
    let temp = tempfile::tempdir().unwrap();
    let path = temp.path().join("starters.sqlite3");
    let db = Store::open(&path).unwrap();
    let original =
        serde_json::to_value(db.template("owner", "meeting.minutes.en").unwrap()).unwrap();
    let memory = serde_json::to_value(db.template("owner", "memory.evidence.en").unwrap()).unwrap();
    let copy = db.copy_template("owner", "memory.evidence.en").unwrap();
    assert_eq!(
        copy.origin.as_ref().unwrap().template_id,
        "memory.evidence.en"
    );
    assert_eq!(copy.attributions[0].license, "CC0-1.0");
    let saved = db
        .create_document(
            "owner",
            CreateDocument {
                title: "Evidence review".into(),
                template_id: copy.id.clone(),
                source_ids: vec![],
                outline_approved: false,
            },
        )
        .unwrap();
    drop(db);
    let db = Store::open(&path).unwrap();
    assert_eq!(
        serde_json::to_value(db.template("owner", "meeting.minutes.en").unwrap()).unwrap(),
        original
    );
    assert_eq!(
        serde_json::to_value(db.template("owner", "memory.evidence.en").unwrap()).unwrap(),
        memory
    );
    assert_eq!(
        db.document("owner", &saved.id).unwrap().version,
        saved.version
    );
    let public = db
        .templates(
            "@catalog",
            serde_json::from_value(json!({"visibility":"public"})).unwrap(),
        )
        .unwrap()
        .items;
    assert_eq!(public.len(), 42.min(MAX_RESULTS));
}
