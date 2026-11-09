use axum::{
    body::Body,
    http::{Request, StatusCode},
};
use dmem_contracts::*;
use dmem_server::{Store, router};
use http_body_util::BodyExt;
use serde_json::{Value, json};
use std::sync::Arc;
use tower::ServiceExt;
const A: &str = "test-owner-alpha-token";
const B: &str = "test-owner-beta-token";
fn create() -> CreateDocument {
    CreateDocument {
        title: "첫 문서".into(),
        template_id: "meeting.minutes.ko".into(),
        source_ids: vec![],
        outline_approved: false,
    }
}
#[test]
fn copy_drafts_citations_versions_and_persistence() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("library.sqlite3");
    let db = Store::open(&path).unwrap();
    let original = db.template("a", "meeting.minutes.ko").unwrap();
    let copy = db.copy_template("a", &original.id).unwrap();
    assert_ne!(copy.id, original.id);
    assert_eq!(copy.visibility, Visibility::Private);
    assert_eq!(copy.origin.unwrap().template_id, original.id);
    assert_eq!(db.template("b", &copy.id).unwrap_err(), Fault::NotFound);
    let source = db
        .import_source(
            "a",
            "합성 자료".into(),
            "facts.md".into(),
            b"# Fact\nSENTINEL_PRIVATE_SOURCE".to_vec(),
        )
        .unwrap();
    assert_eq!(
        db.source_file("a", &source.id).unwrap().1,
        b"# Fact\nSENTINEL_PRIVATE_SOURCE"
    );
    assert!(
        db.sources(
            "b",
            Search {
                q: "SENTINEL".into(),
                ..Default::default()
            }
        )
        .unwrap()
        .items
        .is_empty()
    );
    assert_eq!(db.source("b", &source.id).unwrap_err(), Fault::NotFound);
    let mut req = create();
    req.source_ids = vec![source.id.clone()];
    assert_eq!(
        db.create_document("b", req.clone()).unwrap_err(),
        Fault::NotFound
    );
    let doc = db.create_document("a", req).unwrap();
    assert!(
        doc.content
            .blocks
            .iter()
            .any(|b| b.text().contains("확인 필요"))
    );
    assert_eq!(doc.source_versions[0].version, 1);
    assert!(
        doc.content
            .blocks
            .iter()
            .any(|b| matches!(b,Block::Quote{text,..} if text.contains("SENTINEL_PRIVATE_SOURCE"))),
        "selected factual paragraphs must be included, not just the heading"
    );
    assert!(
        doc.content
            .blocks
            .iter()
            .any(|b| matches!(b,Block::Quote{citation:Some(c),..} if c.source_id==source.id))
    );
    let save = SaveDocument {
        base_version: 1,
        title: "수정 문서".into(),
        content: doc.content.clone(),
    };
    let updated = db.save_document("a", &doc.id, save.clone()).unwrap();
    assert_eq!(updated.version, 2);
    assert_eq!(
        db.save_document("a", &doc.id, save).unwrap_err(),
        Fault::VersionConflict
    );
    assert_eq!(db.revisions("a", &doc.id).unwrap().items.len(), 2);
    assert_eq!(db.revisions("b", &doc.id).unwrap_err(), Fault::NotFound);
    drop(db);
    let db = Store::open(&path).unwrap();
    assert_eq!(db.document("a", &doc.id).unwrap().title, "수정 문서");
    assert_eq!(
        db.revisions("a", &doc.id).unwrap().items[1].title,
        "첫 문서"
    );
}
#[test]
fn deck_approval_and_citation_validation() {
    let db = Store::open(":memory:").unwrap();
    let mut req = create();
    req.template_id = "startup.pitch.ko".into();
    assert_eq!(
        db.create_document("a", req.clone()).unwrap_err(),
        Fault::InvalidInput
    );
    req.outline_approved = true;
    assert_eq!(
        db.create_document("a", req).unwrap().content.slides.len(),
        11
    );
    let mut doc = db.create_document("a", create()).unwrap();
    doc.content.blocks.push(Block::Quote {
        text: "forged".into(),
        citation: Some(Citation {
            source_id: "foreign".into(),
            source_version: 1,
            span_id: "p1".into(),
        }),
    });
    assert_eq!(
        db.save_document(
            "a",
            &doc.id,
            SaveDocument {
                base_version: 1,
                title: doc.title,
                content: doc.content
            }
        )
        .unwrap_err(),
        Fault::InvalidInput
    );
}
async fn call(
    app: axum::Router,
    method: &str,
    path: &str,
    token: Option<&str>,
    body: Value,
) -> (StatusCode, Value) {
    let mut builder = Request::builder()
        .method(method)
        .uri(path)
        .header("content-type", "application/json");
    if let Some(t) = token {
        builder = builder.header("authorization", format!("Bearer {t}"));
    }
    let response = app
        .oneshot(builder.body(Body::from(body.to_string())).unwrap())
        .await
        .unwrap();
    let status = response.status();
    let bytes = response.into_body().collect().await.unwrap().to_bytes();
    (status, serde_json::from_slice(&bytes).unwrap())
}
#[tokio::test]
async fn real_router_auth_privacy_conflict_and_fixed_errors() {
    let app = router(
        Arc::new(Store::open(":memory:").unwrap()),
        vec![(A.into(), "a".into()), (B.into(), "b".into())],
        vec!["http://127.0.0.1:5174".into()],
        None,
    )
    .unwrap();
    assert_eq!(
        call(app.clone(), "GET", "/v1/templates", None, json!(null))
            .await
            .0,
        401
    );
    let (status, copy) = call(
        app.clone(),
        "POST",
        "/v1/templates/meeting.minutes.ko/copy",
        Some(A),
        json!({}),
    )
    .await;
    assert_eq!(status, 200);
    let (status, error) = call(
        app.clone(),
        "GET",
        &format!("/v1/templates/{}", copy["id"].as_str().unwrap()),
        Some(B),
        json!(null),
    )
    .await;
    assert_eq!(status, 404);
    assert_eq!(error["code"], "not_found");
    let (status, error) = call(
        app.clone(),
        "POST",
        "/v1/documents",
        Some(A),
        json!({"title":"SECRET_SENTINEL","template_id":"meeting.minutes.ko","unknown":"PRIVATE"}),
    )
    .await;
    assert_eq!(status, 400);
    assert!(!error.to_string().contains("SECRET"));
    let (_, doc) = call(
        app.clone(),
        "POST",
        "/v1/documents",
        Some(A),
        serde_json::to_value(create()).unwrap(),
    )
    .await;
    let save = json!({"title":"saved","base_version":1,"content":doc["content"]});
    let id = doc["id"].as_str().unwrap();
    assert_eq!(
        call(
            app.clone(),
            "PUT",
            &format!("/v1/documents/{id}"),
            Some(A),
            save.clone()
        )
        .await
        .0,
        200
    );
    assert_eq!(
        call(
            app.clone(),
            "PUT",
            &format!("/v1/documents/{id}"),
            Some(A),
            save
        )
        .await
        .0,
        409
    );
    assert_eq!(
        call(
            app,
            "GET",
            "/v1/templates?unknown=SENTINEL",
            Some(A),
            json!(null)
        )
        .await
        .1["code"],
        "invalid_input"
    );
}

#[cfg(unix)]
#[test]
fn new_library_database_is_private_to_the_local_account() {
    use std::os::unix::fs::PermissionsExt;
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("private.sqlite3");
    let _db = Store::open(&path).unwrap();
    assert_eq!(
        std::fs::metadata(&path).unwrap().permissions().mode() & 0o777,
        0o600
    );
}
