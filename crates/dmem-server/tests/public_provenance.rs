use axum::{body::Body, http::Request};
use dmem_server::{AuthConfig, Store, router, router_with_auth};
use http_body_util::BodyExt;
use serde_json::{Value, json};
use std::sync::Arc;
use tower::ServiceExt;
const TOKEN: &str = "synthetic-owner-token";
const ADMIN: &str = "synthetic-reviewer-key-at-least-32-characters";
#[tokio::test]
async fn attribution_limit_rejects_instead_of_silently_dropping_credits() {
    let db = Arc::new(Store::open(":memory:").unwrap());
    let mut config = AuthConfig::default();
    config.admin_token = Some(ADMIN.into());
    let app = router_with_auth(
        db.clone(),
        vec![(TOKEN.into(), "alice".into())],
        vec!["http://localhost".into()],
        None,
        config,
    )
    .unwrap();
    let mut public_id = "meeting.minutes.ko".to_owned();
    for _ in 0..16 {
        let copy = db.copy_template("alice", &public_id).unwrap();
        let c=call(&app,"/v1/me/contributions",json!({"template_id":copy.id,"author":"Alice","license":"CC-BY-4.0","rights_confirmed":true}),false).await;
        call(
            &app,
            &format!(
                "/v1/admin/contributions/{}/decision",
                c["id"].as_str().unwrap()
            ),
            json!({"decision":"approve"}),
            true,
        )
        .await;
        public_id = c["snapshot"]["id"].as_str().unwrap().to_owned();
    }
    assert_eq!(
        db.copy_template("alice", &public_id).unwrap_err(),
        dmem_contracts::Fault::LicenseForbids
    );
}
async fn call(app: &axum::Router, path: &str, input: Value, admin: bool) -> Value {
    let res = app
        .clone()
        .oneshot(
            Request::builder()
                .method("POST")
                .uri(path)
                .header("Origin", "http://localhost")
                .header(
                    "Authorization",
                    format!("Bearer {}", if admin { ADMIN } else { TOKEN }),
                )
                .header("Content-Type", "application/json")
                .body(Body::from(input.to_string()))
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(res.status(), 200);
    serde_json::from_slice(&res.into_body().collect().await.unwrap().to_bytes()).unwrap()
}
#[tokio::test]
async fn public_snapshot_never_exposes_a_private_copy_id() {
    let db = Arc::new(Store::open(":memory:").unwrap());
    let original = db.copy_template("alice", "meeting.minutes.ko").unwrap();
    let second = db.copy_template("alice", &original.id).unwrap();
    let app = router(
        db,
        vec![(TOKEN.into(), "alice".into())],
        vec!["http://localhost".into()],
        None,
    )
    .unwrap();
    let c=call(&app,"/v1/me/contributions",json!({"template_id":second.id,"author":"Alice","license":"CC0-1.0","rights_confirmed":true}),false).await;
    assert!(
        !c["snapshot"].to_string().contains(&original.id),
        "public metadata cannot disclose a private ancestor ID"
    );
}
#[tokio::test]
async fn public_derivative_copies_retain_the_first_contributors_attribution() {
    let db = Arc::new(Store::open(":memory:").unwrap());
    let a = db.copy_template("alice", "meeting.minutes.ko").unwrap();
    let mut config = AuthConfig::default();
    config.admin_token = Some(ADMIN.into());
    let alice = router_with_auth(
        db.clone(),
        vec![(TOKEN.into(), "alice".into())],
        vec!["http://localhost".into()],
        None,
        config.clone(),
    )
    .unwrap();
    let first = call(
        &alice,
        "/v1/me/contributions",
        json!({"template_id":a.id,"author":"Alice","license":"CC-BY-4.0","rights_confirmed":true}),
        false,
    )
    .await;
    call(
        &alice,
        &format!(
            "/v1/admin/contributions/{}/decision",
            first["id"].as_str().unwrap()
        ),
        json!({"decision":"approve"}),
        true,
    )
    .await;
    let original_public = first["snapshot"]["id"].as_str().unwrap();
    let b = db.copy_template("bob", original_public).unwrap();
    let bob = router_with_auth(
        db.clone(),
        vec![(TOKEN.into(), "bob".into())],
        vec!["http://localhost".into()],
        None,
        config,
    )
    .unwrap();
    let second = call(
        &bob,
        "/v1/me/contributions",
        json!({"template_id":b.id,"author":"Bob","license":"CC-BY-4.0","rights_confirmed":true}),
        false,
    )
    .await;
    call(
        &bob,
        &format!(
            "/v1/admin/contributions/{}/decision",
            second["id"].as_str().unwrap()
        ),
        json!({"decision":"approve"}),
        true,
    )
    .await;
    let copy = db
        .copy_template("charlie", second["snapshot"]["id"].as_str().unwrap())
        .unwrap();
    let value = serde_json::to_value(copy).unwrap();
    assert!(
        value["attributions"].as_array().is_some_and(|xs| xs
            .iter()
            .any(|x| x["template_id"] == original_public && x["author"] == "Alice")),
        "a derivative copy must retain the first contributor's attribution"
    );
}
