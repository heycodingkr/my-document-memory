use axum::{
    Router,
    body::Body,
    http::{Request, StatusCode},
};
use dmem_server::{Store, router};
use http_body_util::BodyExt;
use serde_json::{Value, json};
use std::sync::Arc;
use tower::ServiceExt;

const TOKEN_A: &str = "test-owner-alpha-token";
const TOKEN_B: &str = "test-owner-beta-token";
const RECALL_QUERY: &str = "/v1/recall?url=https%3A%2F%2Fwww.example.org%2Ftemplates%2Fminutes&doc_type=meeting_minutes&locale=ko-KR";

fn app() -> Router {
    router(
        Arc::new(Store::open(":memory:").unwrap()),
        vec![(TOKEN_A.into(), "a".into()), (TOKEN_B.into(), "b".into())],
        vec!["http://127.0.0.1:5174".into()],
        None,
    )
    .unwrap()
}

async fn read_response(response: axum::response::Response) -> (StatusCode, Value, String) {
    let status = response.status();
    let bytes = response.into_body().collect().await.unwrap().to_bytes();
    let raw = String::from_utf8(bytes.to_vec()).unwrap();
    let value = serde_json::from_str(&raw).unwrap();
    (status, value, raw)
}

async fn get(app: &Router, path: &str, token: Option<&str>) -> (StatusCode, Value, String) {
    let mut request = Request::builder().method("GET").uri(path);
    if let Some(token) = token {
        request = request.header("authorization", format!("Bearer {token}"));
    }
    let response = app
        .clone()
        .oneshot(request.body(Body::empty()).unwrap())
        .await
        .unwrap();
    read_response(response).await
}

async fn post_json(
    app: &Router,
    path: &str,
    token: &str,
    body: Value,
) -> (StatusCode, Value, String) {
    let response = app
        .clone()
        .oneshot(
            Request::builder()
                .method("POST")
                .uri(path)
                .header("authorization", format!("Bearer {token}"))
                .header("content-type", "application/json")
                .body(Body::from(body.to_string()))
                .unwrap(),
        )
        .await
        .unwrap();
    read_response(response).await
}

#[tokio::test]
async fn rv20_recall_returns_seeded_minutes_hint() {
    let app = app();

    let (status, body, _) = get(&app, RECALL_QUERY, Some(TOKEN_A)).await;

    assert_eq!(status, StatusCode::OK);
    assert_eq!(body["hints"][0]["memory_id"], "meeting.minutes.ko");
    let hints = body["hints"].as_array().unwrap();
    assert!(hints.len() <= 3);
    assert!(
        hints
            .iter()
            .all(|hint| hint["form"]["doc_type"] == "meeting_minutes")
    );
    assert_eq!(body["untrusted"], true);
}

#[tokio::test]
async fn rv21_private_template_is_visible_only_to_its_owner() {
    let app = app();
    let (status, created, _) = post_json(
        &app,
        "/v1/templates",
        TOKEN_A,
        json!({
            "title": "SENTINEL_RECALL_PRIVATE",
            "summary": "Private minutes template for recall owner isolation.",
            "form": {"provider": "docx", "doc_type": "meeting_minutes", "locale": "ko-KR"},
            "sections": ["회의 개요"],
            "tags": ["초안"]
        }),
    )
    .await;
    assert_eq!(status, StatusCode::OK);
    let created_id = created["id"].as_str().unwrap();

    let (owner_status, owner_body, _) = get(&app, RECALL_QUERY, Some(TOKEN_A)).await;
    assert_eq!(owner_status, StatusCode::OK);
    assert_eq!(owner_body["hints"][0]["memory_id"], created_id);

    let (other_status, other_body, other_raw) = get(&app, RECALL_QUERY, Some(TOKEN_B)).await;
    assert_eq!(other_status, StatusCode::OK);
    assert!(!other_raw.contains(created_id));
    assert!(!other_raw.contains("SENTINEL_RECALL_PRIVATE"));
    assert_eq!(other_body["hints"][0]["memory_id"], "meeting.minutes.ko");
}

#[tokio::test]
async fn rv23_recall_requires_a_valid_bearer_token() {
    let app = app();

    let (missing_status, missing_body, _) = get(&app, RECALL_QUERY, None).await;
    assert_eq!(missing_status, StatusCode::UNAUTHORIZED);
    assert_eq!(missing_body["code"], "auth_required");

    let (wrong_status, wrong_body, _) = get(&app, RECALL_QUERY, Some("wrong-recall-token")).await;
    assert_eq!(wrong_status, StatusCode::UNAUTHORIZED);
    assert_eq!(wrong_body["code"], "auth_required");
}

#[tokio::test]
async fn rv28_copied_seed_ranks_ahead_of_its_public_source() {
    let app = app();
    let (status, copied, _) = post_json(
        &app,
        "/v1/templates/meeting.minutes.ko/copy",
        TOKEN_A,
        json!({}),
    )
    .await;
    assert_eq!(status, StatusCode::OK);
    let copied_id = copied["id"].as_str().unwrap();

    let (recall_status, body, _) = get(&app, RECALL_QUERY, Some(TOKEN_A)).await;

    assert_eq!(recall_status, StatusCode::OK);
    assert_eq!(body["hints"][0]["memory_id"], copied_id);
    assert_eq!(body["hints"][0]["source"]["origin"], "copied");
    assert_eq!(body["hints"][0]["source"]["tier"], "mine");
    assert_eq!(body["hints"][0]["source"]["license"], "CC0-1.0");
    assert_eq!(body["hints"][1]["memory_id"], "meeting.minutes.ko");
}
