use axum::{
    Router,
    body::Body,
    http::{Request, StatusCode},
};
use dmem_server::{Store, router};
use http_body_util::BodyExt;
use serde_json::{Value, json};
use std::{path::Path, sync::Arc};
use tower::ServiceExt;

const TOKEN: &str = "test-owner-alpha-token";
const URL_N: &str = "https%3A%2F%2Fwww.example.org%2Ftemplates%2Fminutes";

fn harness(path: impl AsRef<Path>) -> (Router, Arc<Store>) {
    let store = Arc::new(Store::open(path).unwrap());
    let app = router(
        store.clone(),
        vec![(TOKEN.into(), "a".into())],
        vec!["http://127.0.0.1:5174".into()],
        None,
    )
    .unwrap();
    (app, store)
}

async fn get(app: &Router, path: &str, token: &str) -> (StatusCode, Value, String) {
    let request = Request::builder()
        .method("GET")
        .uri(path)
        .header("authorization", format!("Bearer {token}"))
        .body(Body::empty())
        .unwrap();
    let response = app.clone().oneshot(request).await.unwrap();
    let status = response.status();
    let bytes = response.into_body().collect().await.unwrap().to_bytes();
    let raw = String::from_utf8(bytes.to_vec()).unwrap();
    let value = serde_json::from_str(&raw).unwrap();
    (status, value, raw)
}

async fn post_json(
    app: &Router,
    path: &str,
    token: &str,
    body: Value,
) -> (StatusCode, Value, String) {
    let request = Request::builder()
        .method("POST")
        .uri(path)
        .header("authorization", format!("Bearer {token}"))
        .header("content-type", "application/json")
        .body(Body::from(body.to_string()))
        .unwrap();
    let response = app.clone().oneshot(request).await.unwrap();
    let status = response.status();
    let bytes = response.into_body().collect().await.unwrap().to_bytes();
    let raw = String::from_utf8(bytes.to_vec()).unwrap();
    let value = serde_json::from_str(&raw).unwrap();
    (status, value, raw)
}

#[tokio::test]
async fn rv22_keyword_recall_finds_the_25th_private_template() {
    let (app, _store) = harness(":memory:");
    let mut last_id = None;
    for n in 1..=25 {
        let tags = if n == 25 {
            vec!["zz-needle"]
        } else {
            Vec::new()
        };
        let (status, value, raw) = post_json(
            &app,
            "/v1/templates",
            TOKEN,
            json!({
                "title": format!("Report template {n}"),
                "summary": format!("Report summary {n}"),
                "form": {"provider": "docx", "doc_type": "report", "locale": "ko-KR"},
                "sections": ["Overview", "Details"],
                "tags": tags,
            }),
        )
        .await;
        assert_eq!(status, StatusCode::OK, "{raw}");
        if n == 25 {
            last_id = value["id"].as_str().map(str::to_owned);
        }
    }

    let path = format!(
        "/v1/recall?url={URL_N}&doc_type=report&locale=ko-KR&keywords=zz-needle&scope=mine&limit=3"
    );
    let (status, value, _) = get(&app, &path, TOKEN).await;
    assert_eq!(status, StatusCode::OK);
    let hints = value["hints"].as_array().unwrap();
    assert_eq!(hints.len(), 3);
    assert_eq!(hints[0]["memory_id"], last_id.unwrap());
}

#[tokio::test]
async fn rv24_invalid_queries_use_fixed_error_codes_without_echoing_values() {
    let (app, _store) = harness(":memory:");
    let queries = [
        (format!("/v1/recall?url={URL_N}&limit=0"), "invalid_input"),
        (format!("/v1/recall?url={URL_N}&limit=4"), "invalid_input"),
        (format!("/v1/recall?url={URL_N}&limit=x"), "invalid_input"),
        (
            format!("/v1/recall?url={URL_N}&foo=BOGUS_FOO_MARK"),
            "invalid_input",
        ),
        ("/v1/recall?doc_type=report".into(), "invalid_input"),
        (
            format!("/v1/recall?url={URL_N}&keywords=a,b,c,d,e,f,g,h,i"),
            "invalid_input",
        ),
        (
            format!("/v1/recall?url={URL_N}&keywords=a,,b"),
            "invalid_input",
        ),
        (
            format!("/v1/recall?url={URL_N}&scope=BOGUS_SCOPE_MARK"),
            "invalid_input",
        ),
        (
            format!("/v1/recall?url={URL_N}&kind=BOGUS_KIND_MARK"),
            "invalid_input",
        ),
        (
            format!("/v1/recall?url={URL_N}&doc_type=UNKNOWN_DOCTYPE_MARK"),
            "invalid_form",
        ),
    ];
    let markers = [
        "BOGUS_FOO_MARK",
        "BOGUS_SCOPE_MARK",
        "BOGUS_KIND_MARK",
        "UNKNOWN_DOCTYPE_MARK",
    ];

    for (path, expected_code) in queries {
        let (status, value, raw) = get(&app, &path, TOKEN).await;
        assert_eq!(status, StatusCode::BAD_REQUEST, "{path}: {raw}");
        assert_eq!(value["code"], expected_code, "{path}: {raw}");
        for marker in markers {
            assert!(!raw.contains(marker), "{path} echoed {marker}: {raw}");
        }
    }
}

#[tokio::test]
async fn rv25_google_document_url_is_canonicalized_without_url_parts() {
    let (app, _store) = harness(":memory:");
    let path = "/v1/recall?url=https%3A%2F%2Fdocs.google.com%2Fdocument%2Fd%2FGDOC_ID_SENTINEL_abc123%2Fedit%3Fresourcekey%3DRK_SENTINEL_xyz%23F_SENTINEL_frag";
    let (status, value, raw) = get(&app, path, TOKEN).await;

    assert_eq!(status, StatusCode::OK);
    assert_eq!(
        value["canonical_url"],
        "docs.google.com/document/d/:id/edit"
    );
    for marker in [
        "GDOC_ID_SENTINEL_abc123",
        "RK_SENTINEL_xyz",
        "F_SENTINEL_frag",
    ] {
        assert!(!raw.contains(marker), "response echoed {marker}: {raw}");
    }
}

#[tokio::test]
async fn rv26_rejected_http_url_does_not_echo_host_or_path() {
    let (app, _store) = harness(":memory:");
    let (status, value, raw) = get(
        &app,
        "/v1/recall?url=http%3A%2F%2Fexample.com%2Fsecret-path",
        TOKEN,
    )
    .await;

    assert_eq!(status, StatusCode::BAD_REQUEST);
    assert_eq!(value["code"], "url_rejected");
    assert_eq!(value["reason"], "scheme_not_allowed");
    assert!(!raw.contains("secret-path"), "response echoed path: {raw}");
    assert!(!raw.contains("example.com"), "response echoed host: {raw}");
}

#[tokio::test]
async fn rv27_recall_is_read_only_deterministic_and_persistent() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("recall.sqlite3");
    let query = format!("/v1/recall?url={URL_N}&doc_type=meeting_minutes&locale=ko-KR");
    let (app, store) = harness(&path);

    let (status, before, raw_before) = get(&app, "/v1/templates", TOKEN).await;
    assert_eq!(status, StatusCode::OK, "{raw_before}");
    let before_count = before["items"].as_array().unwrap().len();

    let (first_status, _, first_raw) = get(&app, &query, TOKEN).await;
    let (second_status, _, second_raw) = get(&app, &query, TOKEN).await;
    assert_eq!(first_status, StatusCode::OK, "{first_raw}");
    assert_eq!(second_status, StatusCode::OK, "{second_raw}");
    assert_eq!(first_raw.as_bytes(), second_raw.as_bytes());

    let (status, after, raw_after) = get(&app, "/v1/templates", TOKEN).await;
    assert_eq!(status, StatusCode::OK, "{raw_after}");
    assert_eq!(after["items"].as_array().unwrap().len(), before_count);

    drop(app);
    drop(store);
    let (reopened_app, reopened_store) = harness(&path);
    let (reopened_status, _, reopened_raw) = get(&reopened_app, &query, TOKEN).await;
    assert_eq!(reopened_status, StatusCode::OK, "{reopened_raw}");
    assert_eq!(first_raw.as_bytes(), reopened_raw.as_bytes());
    drop(reopened_app);
    drop(reopened_store);
}
