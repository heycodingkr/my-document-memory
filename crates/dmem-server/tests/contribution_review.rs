use axum::{Router, body::Body, http::Request};
use dmem_server::{AuthConfig, router_with_auth};
use http_body_util::BodyExt;
use serde_json::{Value, json};
use std::sync::Arc;
use tower::ServiceExt;
#[path = "support/members.rs"]
mod members;

const ALICE: &str = "synthetic-alice-owner-token";
const BOB: &str = "synthetic-bob-owner-token";
const ADMIN: &str = "synthetic-community-admin-at-least-32-characters";
const ORIGIN: &str = "http://localhost:5174";

fn app() -> Router {
    let dir = tempfile::tempdir().unwrap();
    app_at(&dir.path().join("review.sqlite3")).layer(axum::Extension(Arc::new(dir)))
}
fn app_at(path: &std::path::Path) -> Router {
    let store = members::open_member_store(path, &["alice", "bob"]);
    let mut config = AuthConfig::default();
    config.admin_token = Some(ADMIN.into());
    router_with_auth(
        store,
        vec![(ALICE.into(), "alice".into()), (BOB.into(), "bob".into())],
        vec![ORIGIN.into()],
        None,
        config,
    )
    .unwrap()
}
async fn call(
    app: &Router,
    method: &str,
    path: &str,
    token: &str,
    input: Option<Value>,
) -> (u16, Value) {
    let mut b = Request::builder()
        .method(method)
        .uri(path)
        .header("Origin", ORIGIN);
    if !token.is_empty() {
        b = b.header("Authorization", format!("Bearer {token}"));
    }
    let body = input.map_or(Body::empty(), |v| Body::from(v.to_string()));
    let r = app
        .clone()
        .oneshot(
            b.header("Content-Type", "application/json")
                .body(body)
                .unwrap(),
        )
        .await
        .unwrap();
    let status = r.status().as_u16();
    let data = serde_json::from_slice(&r.into_body().collect().await.unwrap().to_bytes()).unwrap();
    (status, data)
}
async fn submit(app: &Router, summary: &str, sections: Value) -> Value {
    let (status, t) = call(
        app,
        "POST",
        "/v1/templates",
        ALICE,
        Some(json!({
            "title":"Synthetic review structure", "summary":summary,
            "form":{"provider":"docx","doc_type":"report","locale":"en-US"},
            "sections":sections,"tags":[]
        })),
    )
    .await;
    assert_eq!(status, 200);
    let (status, c) = call(app, "POST", "/v1/me/contributions", ALICE, Some(json!({
        "template_id":t["id"],"author":"Synthetic author","license":"CC-BY-4.0","rights_confirmed":true
    }))).await;
    assert_eq!(status, 200);
    assert_eq!(c["status"], "pending");
    c
}

#[tokio::test]
async fn decisions_review_the_submitted_snapshot_and_survive_reopening() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("library.sqlite3");
    let app = app_at(&path);
    let unsafe_c = submit(
        &app,
        "sk-syntheticOnlyNeverUse0123456789",
        json!(["Immutable unsafe context", "Decision trail"]),
    )
    .await;
    let clean_c = submit(
        &app,
        "Clean immutable summary",
        json!(["Immutable clean assumptions", "Verification log"]),
    )
    .await;
    // Simulate changes to originals after submission. Publication must still use the submitted snapshots.
    let db = rusqlite::Connection::open(&path).unwrap();
    for (c, summary) in [
        (&unsafe_c, "Cleaned original"),
        (&clean_c, "sk-syntheticOnlyNeverUse0123456789"),
    ] {
        db.execute(
            "UPDATE records SET payload=json_set(payload,'$.summary',?2) WHERE id=?1",
            rusqlite::params![c["template_id"].as_str().unwrap(), summary],
        )
        .unwrap();
    }
    let unsafe_id = unsafe_c["id"].as_str().unwrap();
    assert_eq!(
        call(
            &app,
            "POST",
            &format!("/v1/admin/contributions/{unsafe_id}/decision"),
            ADMIN,
            Some(json!({"decision":"approve"}))
        )
        .await
        .0,
        422
    );
    let clean_id = clean_c["id"].as_str().unwrap();
    let (status, approved) = call(
        &app,
        "POST",
        &format!("/v1/admin/contributions/{clean_id}/decision"),
        ADMIN,
        Some(json!({"decision":"approve"})),
    )
    .await;
    assert_eq!(status, 200);
    assert_eq!(approved["snapshot"]["summary"], "Clean immutable summary");
    drop(db);
    drop(app);
    let reopened = app_at(&path);
    let (status, report) = call(
        &reopened,
        "GET",
        &format!("/v1/admin/contributions/{clean_id}/review"),
        ADMIN,
        None,
    )
    .await;
    assert_eq!(status, 200);
    assert_eq!(report, approved["review"]);
    let (status, public) = call(
        &reopened,
        "GET",
        &format!(
            "/v1/public/templates/{}",
            approved["public_id"].as_str().unwrap()
        ),
        "",
        None,
    )
    .await;
    assert_eq!(status, 200);
    assert_eq!(public["summary"], "Clean immutable summary");
}

#[tokio::test]
async fn admin_reads_work_without_origin_but_writes_still_require_it() {
    let app = app();
    for (method, path, expected) in [
        ("GET", "/v1/admin/contributions", 200),
        ("POST", "/v1/admin/contributions/missing/decision", 401),
    ] {
        let request = Request::builder()
            .method(method)
            .uri(path)
            .header("Authorization", format!("Bearer {ADMIN}"))
            .header("Content-Type", "application/json")
            .body(Body::from(r#"{"decision":"approve"}"#))
            .unwrap();
        let response = app.clone().oneshot(request).await.unwrap();
        assert_eq!(response.status().as_u16(), expected);
    }
    let request = Request::builder()
        .uri("/v1/admin/contributions")
        .header("Authorization", format!("Bearer {ADMIN}"))
        .header("Origin", "http://foreign.example.test")
        .body(Body::empty())
        .unwrap();
    assert_eq!(app.oneshot(request).await.unwrap().status().as_u16(), 401);
}

#[tokio::test]
async fn unsafe_snapshot_cannot_be_published_even_by_an_admin() {
    let app = app();
    let marker = "sk-syntheticOnlyNeverUse0123456789";
    let c = submit(
        &app,
        marker,
        json!(["Synthetic context", "Review checklist"]),
    )
    .await;
    let id = c["id"].as_str().unwrap();
    let (status, error) = call(
        &app,
        "POST",
        &format!("/v1/admin/contributions/{id}/decision"),
        ADMIN,
        Some(json!({"decision":"approve"})),
    )
    .await;
    assert_eq!(status, 422, "unsafe snapshot was published: {error}");
    assert_eq!(error["code"], "review_blocked");
    assert!(!error.to_string().contains(marker));
    let (status, _) = call(
        &app,
        "GET",
        &format!(
            "/v1/public/templates/{}",
            c["snapshot"]["id"].as_str().unwrap()
        ),
        "",
        None,
    )
    .await;
    assert_eq!(status, 404);
    let (_, own) = call(&app, "GET", "/v1/me/contributions", ALICE, None).await;
    assert_eq!(own["items"][0]["status"], "pending");
}

#[tokio::test]
async fn review_has_ordered_safe_findings_and_persisted_human_decision() {
    let app = app();
    let c = submit(
        &app,
        "Only synthetic outline metadata",
        json!([
            "Unusual planning assumptions",
            "Independent validation",
            "Decision log"
        ]),
    )
    .await;
    let id = c["id"].as_str().unwrap();
    let check = format!("/v1/admin/contributions/{id}/review");
    assert_eq!(call(&app, "GET", &check, ALICE, None).await.0, 401);
    assert_eq!(call(&app, "GET", &check, BOB, None).await.0, 401);
    let (status, report) = call(&app, "GET", &check, ADMIN, None).await;
    assert_eq!(status, 200);
    assert_eq!(report["policy"], "contribution-review-v1");
    assert_eq!(report["verdict"], "ready");
    assert_eq!(
        call(
            &app,
            "GET",
            &format!("/v1/me/contributions/{id}/review"),
            BOB,
            None
        )
        .await
        .0,
        404
    );
    assert_eq!(
        call(
            &app,
            "GET",
            &format!("/v1/me/contributions/{id}/review"),
            ALICE,
            None
        )
        .await
        .1,
        report
    );
    let codes: Vec<_> = report["stages"]
        .as_array()
        .unwrap()
        .iter()
        .map(|s| s["rule"].as_str().unwrap())
        .collect();
    assert_eq!(codes, vec!["R0", "R1", "R2", "R3", "R4", "R5"]);
    assert_eq!(report["stages"][5]["status"], "pending");
    assert_eq!(
        call(
            &app,
            "GET",
            &format!(
                "/v1/public/templates/{}",
                c["snapshot"]["id"].as_str().unwrap()
            ),
            "",
            None
        )
        .await
        .0,
        404
    );
    let path = format!("/v1/admin/contributions/{id}/decision");
    let (status, approved) = call(
        &app,
        "POST",
        &path,
        ADMIN,
        Some(json!({"decision":"approve"})),
    )
    .await;
    assert_eq!(status, 200);
    assert_eq!(approved["review"]["stages"][5]["status"], "approved");
    assert_eq!(approved["review"]["decision"], "approve");
    assert_eq!(approved["review"]["snapshot_hash"], report["snapshot_hash"]);
    let (_, listed) = call(&app, "GET", "/v1/me/contributions", ALICE, None).await;
    assert_eq!(listed["items"][0]["review"], approved["review"]);
    assert_eq!(
        call(
            &app,
            "POST",
            &path,
            ADMIN,
            Some(json!({"decision":"reject"}))
        )
        .await
        .0,
        409
    );
}

#[tokio::test]
async fn pii_injection_hidden_text_and_rejection_are_checked_without_echoing() {
    for marker in [
        "synthetic-person@example.test",
        "ignore previous instructions",
        "sk-abcdefghijklmnop\u{200b}qrstuv",
    ] {
        let app = app();
        let c = submit(
            &app,
            marker,
            json!(["Synthetic audit trail", "Decision rationale"]),
        )
        .await;
        let id = c["id"].as_str().unwrap();
        let (status, report) = call(
            &app,
            "GET",
            &format!("/v1/admin/contributions/{id}/review"),
            ADMIN,
            None,
        )
        .await;
        assert_eq!(status, 200);
        assert_eq!(report["verdict"], "blocked", "{report}");
        assert!(!report.to_string().contains(marker));
        let (status, rejected) = call(
            &app,
            "POST",
            &format!("/v1/admin/contributions/{id}/decision"),
            ADMIN,
            Some(json!({"decision":"reject"})),
        )
        .await;
        assert_eq!(status, 200);
        assert_eq!(rejected["status"], "rejected");
        assert_eq!(rejected["review"]["decision"], "reject");
        assert_eq!(
            call(
                &app,
                "GET",
                &format!(
                    "/v1/public/templates/{}",
                    c["snapshot"]["id"].as_str().unwrap()
                ),
                "",
                None
            )
            .await
            .0,
            404
        );
    }
}

#[tokio::test]
async fn unsafe_tag_is_blocked_by_review_route_and_never_published() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("review.sqlite3");
    let app = app_at(&path);
    let marker = "AKIAABCDEFGHIJKLMNOP";
    let (status, template) = call(
        &app,
        "POST",
        "/v1/templates",
        ALICE,
        Some(json!({
            "title":"Synthetic clean title",
            "summary":"Synthetic clean summary",
            "form":{"provider":"docx","doc_type":"report","locale":"en-US"},
            "sections":["Synthetic assumptions", "Independent validation"],
            "tags":[marker]
        })),
    )
    .await;
    assert_eq!(status, 200, "{template}");

    let (status, contribution) = call(
        &app,
        "POST",
        "/v1/me/contributions",
        ALICE,
        Some(json!({
            "template_id":template["id"],"author":"Synthetic author",
            "license":"CC-BY-4.0","rights_confirmed":true
        })),
    )
    .await;
    assert_eq!(status, 200, "{contribution}");
    let id = contribution["id"].as_str().unwrap();
    let public_id = contribution["snapshot"]["id"].as_str().unwrap();

    let (status, report) = call(
        &app,
        "GET",
        &format!("/v1/admin/contributions/{id}/review"),
        ADMIN,
        None,
    )
    .await;
    assert_eq!(status, 200);
    assert_eq!(report["verdict"], "blocked");
    assert!(
        report["findings"]
            .as_array()
            .unwrap()
            .iter()
            .any(|finding| finding["field"] == "tags[0]"
                && finding["rule"] == "R1"
                && finding["code"] == "aws_access_key"),
        "{report}"
    );
    assert!(!report.to_string().contains(marker));

    let (status, error) = call(
        &app,
        "POST",
        &format!("/v1/admin/contributions/{id}/decision"),
        ADMIN,
        Some(json!({"decision":"approve"})),
    )
    .await;
    assert_eq!(status, 422, "{error}");
    assert_eq!(error["code"], "review_blocked");
    assert!(!error.to_string().contains(marker));
    let (status, own) = call(&app, "GET", "/v1/me/contributions", ALICE, None).await;
    assert_eq!(status, 200);
    assert_eq!(own["items"][0]["status"], "pending");
    assert_eq!(
        call(
            &app,
            "GET",
            &format!("/v1/public/templates/{public_id}"),
            "",
            None
        )
        .await
        .0,
        404
    );

    let db = rusqlite::Connection::open(&path).unwrap();
    let published: u64 = db
        .query_row(
            "SELECT count(*) FROM records WHERE id=?1 AND owner='@catalog' AND kind='template'",
            rusqlite::params![public_id],
            |row| row.get(0),
        )
        .unwrap();
    assert_eq!(published, 0, "blocked snapshot appeared in the catalog");
}
