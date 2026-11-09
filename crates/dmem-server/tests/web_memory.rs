use axum::{Router, body::Body, http::Request, routing::get};
use dmem_server::{AuthConfig, Store, WebConfig, router_with_services};
use http_body_util::BodyExt;
use serde_json::{Value, json};
use std::sync::{
    Arc, Mutex,
    atomic::{AtomicUsize, Ordering},
};
use tower::ServiceExt;
#[path = "support/members.rs"]
mod members;

const A: &str = "synthetic-alice-token-123456789";
const B: &str = "synthetic-bob-token-12345678901";
const ADMIN: &str = "synthetic-admin-token-12345678901234567890";
const PAGE: &str = r#"<html lang="ko-KR"><title>이력서</title><link rel="license" href="https://creativecommons.org/licenses/by/4.0/"><h2>경력</h2><p>PROSE_TEST</p><table><tr><th>기간</th></tr><tr><td>CELL_TEST</td></tr></table></html>"#;
struct Fixture {
    app: Router,
    store: Arc<Store>,
    url: String,
    content: Arc<Mutex<String>>,
    calls: Arc<AtomicUsize>,
    task: tokio::task::JoinHandle<()>,
}
impl Drop for Fixture {
    fn drop(&mut self) {
        self.task.abort();
    }
}
async fn fixture(path: &std::path::Path) -> Fixture {
    let content = Arc::new(Mutex::new(PAGE.to_string()));
    let served = content.clone();
    let calls = Arc::new(AtomicUsize::new(0));
    let counted = calls.clone();
    let site=Router::new().route("/doc",get(move || {let content=served.clone();let calls=counted.clone();async move{calls.fetch_add(1,Ordering::SeqCst);axum::response::Html(content.lock().unwrap().clone())}}))
        .route("/private",get(||async{axum::response::Redirect::temporary("http://127.0.0.2/private")}))
        .route("/large",get(||async{axum::response::Html("a".repeat(5*1024*1024+1))}))
        .route("/loop",get(||async{axum::response::Redirect::temporary("/loop")}))
        .route("/noai",get(||async{([("x-robots-tag","noai")],axum::response::Html(PAGE))}))
        .route("/search",get(||async{axum::Json(json!({"web":{"results":[{"title":"Resume","url":"https://example.com/resume?tracking=1","description":"Public structure"},{"title":"Private","url":"https://127.0.0.1/private","description":"Blocked"}]}}))}));
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let addr = listener.local_addr().unwrap();
    let task = tokio::spawn(async move { axum::serve(listener, site).await.unwrap() });
    let store = members::open_member_store(path, &["alice", "bob"]);
    let mut config = WebConfig::isolated_fixture(addr);
    config.capture_secret = Some("synthetic-capture-secret-1234567890".into());
    let mut auth = AuthConfig::default();
    auth.admin_token = Some(ADMIN.into());
    let app = router_with_services(
        store.clone(),
        vec![(A.into(), "alice".into()), (B.into(), "bob".into())],
        vec!["http://localhost:5174".into()],
        None,
        auth,
        config,
    )
    .unwrap();
    Fixture {
        app,
        store,
        url: format!("http://{addr}"),
        content,
        calls,
        task,
    }
}
async fn post(app: &Router, path: &str, token: &str, data: Value) -> (u16, Value) {
    let mut request = Request::builder()
        .uri(path)
        .method("POST")
        .header("content-type", "application/json");
    if !token.is_empty() {
        request = request.header("authorization", format!("Bearer {token}"));
    }
    if token == ADMIN {
        request = request.header("origin", "http://localhost:5174");
    }
    let response = app
        .clone()
        .oneshot(request.body(Body::from(data.to_string())).unwrap())
        .await
        .unwrap();
    let status = response.status().as_u16();
    let bytes = response.into_body().collect().await.unwrap().to_bytes();
    (status, serde_json::from_slice(&bytes).unwrap())
}
#[tokio::test]
async fn wi08_09_10_preview_snapshot_is_private_and_import_is_persistent_idempotent() {
    let tmp = tempfile::tempdir().unwrap();
    let path = tmp.path().join("library.sqlite3");
    let f = fixture(&path).await;
    let before = f
        .store
        .sources("alice", Default::default())
        .unwrap()
        .items
        .len();
    let (status, p) = post(
        &f.app,
        "/v1/web/preview",
        A,
        json!({"url":format!("{}/doc?SECRET=1#PRIVATE",f.url)}),
    )
    .await;
    assert_eq!(status, 200, "{p}");
    assert_eq!(p["license"], "CC-BY-4.0");
    assert!(!p.to_string().contains("SECRET"));
    assert_eq!(
        f.store
            .sources("alice", Default::default())
            .unwrap()
            .items
            .len(),
        before
    );
    *f.content.lock().unwrap() = "<title>Changed</title><h1>CHANGED_TEST</h1>".into();
    let input = json!({"preview_id":p["preview_id"],"kind":"reference","copy_mode":"full"});
    assert_eq!(
        post(&f.app, "/v1/web/import", B, input.clone()).await.0,
        404
    );
    let (status, first) = post(&f.app, "/v1/web/import", A, input.clone()).await;
    assert_eq!(status, 200, "{first}");
    assert_eq!(first["created"], true);
    let (_, second) = post(&f.app, "/v1/web/import", A, input).await;
    assert_eq!(first["id"], second["id"]);
    assert_eq!(second["created"], false);
    let source = f
        .store
        .source("alice", first["id"].as_str().unwrap())
        .unwrap();
    let text = serde_json::to_string(&source).unwrap();
    assert!(text.contains("PROSE_TEST"));
    assert!(!text.contains("CHANGED_TEST"));
    assert_eq!(f.calls.load(Ordering::SeqCst), 1);
    let reopened = Store::open(&path).unwrap();
    assert_eq!(
        reopened
            .web_origin("alice", &source.id)
            .unwrap()
            .content_hash,
        p["content_hash"].as_str().unwrap()
    );
    assert!(reopened.web_origin("bob", &source.id).is_err());
}
#[tokio::test]
async fn wi02_11_13_structure_only_and_country_variants_preserve_rights() {
    let tmp = tempfile::tempdir().unwrap();
    let f = fixture(&tmp.path().join("db")).await;
    *f.content.lock().unwrap() = PAGE.replace(
        r#"<link rel="license" href="https://creativecommons.org/licenses/by/4.0/">"#,
        "",
    );
    let (_, p) = post(
        &f.app,
        "/v1/web/preview",
        A,
        json!({"url":format!("{}/doc",f.url)}),
    )
    .await;
    assert_eq!(
        post(
            &f.app,
            "/v1/web/import",
            A,
            json!({"preview_id":p["preview_id"],"kind":"reference","copy_mode":"full"})
        )
        .await
        .0,
        403
    );
    let mut ids = vec![];
    for locale in ["ko-KR", "en-US", "ja-JP"] {
        let (status,item)=post(&f.app,"/v1/web/import",A,json!({"preview_id":p["preview_id"],"kind":"template","form":{"provider":"html","doc_type":"resume","locale":locale}})).await;
        assert_eq!(status, 200, "{item}");
        let id = item["id"].as_str().unwrap();
        let template = f.store.template("alice", id).unwrap();
        assert_eq!(template.form.locale, locale);
        assert!(template.sections.contains(&"경력".into()));
        assert!(
            !serde_json::to_string(&template)
                .unwrap()
                .contains("PROSE_TEST")
        );
        ids.push(id.to_string());
        assert_eq!(post(&f.app,"/v1/me/contributions",A,json!({"template_id":id,"author":"Synthetic author","license":"CC0-1.0","rights_confirmed":true})).await.0,403);
        let copy = f.store.copy_template("alice", id).unwrap();
        assert_eq!(post(&f.app,"/v1/me/contributions",A,json!({"template_id":copy.id,"author":"Synthetic author","license":"CC0-1.0","rights_confirmed":true})).await.0,403);
    }
    ids.sort();
    ids.dedup();
    assert_eq!(ids.len(), 3);
}
#[tokio::test]
async fn wi07_15_16_fetch_and_protocol_failures_do_not_create_records() {
    let tmp = tempfile::tempdir().unwrap();
    let f = fixture(&tmp.path().join("db")).await;
    for (path, reason) in [
        ("private", "private_address"),
        ("large", "size"),
        ("loop", "redirect_limit"),
        ("noai", "signal_noai"),
    ] {
        let (status, error) = post(
            &f.app,
            "/v1/web/preview",
            A,
            json!({"url":format!("{}/{path}",f.url)}),
        )
        .await;
        assert_eq!(status, 422, "{error}");
        assert_eq!(error["reason"], reason);
    }
    assert_eq!(
        post(
            &f.app,
            "/v1/web/preview",
            "",
            json!({"url":format!("{}/doc",f.url)})
        )
        .await
        .0,
        401
    );
    assert_eq!(
        post(
            &f.app,
            "/v1/web/preview",
            A,
            json!({"url":"https://example.com","unexpected":true})
        )
        .await
        .0,
        400
    );
    let (status, error) = post(
        &f.app,
        "/v1/web/search",
        A,
        json!({"query":"resume templates"}),
    )
    .await;
    assert_eq!(status, 503);
    assert_eq!(error["code"], "search_unavailable");
    assert!(
        f.store
            .sources("alice", Default::default())
            .unwrap()
            .items
            .is_empty()
    );
}
#[tokio::test]
async fn wi15_configured_search_filters_results_and_does_not_save() {
    let tmp = tempfile::tempdir().unwrap();
    let f = fixture(&tmp.path().join("db")).await;
    let mut config =
        WebConfig::isolated_fixture(f.url.trim_start_matches("http://").parse().unwrap());
    config.search_key = Some("synthetic-search-key".into());
    let app = router_with_services(
        f.store.clone(),
        vec![(A.into(), "alice".into())],
        vec![],
        None,
        AuthConfig::default(),
        config,
    )
    .unwrap();
    let (status, result) = post(
        &app,
        "/v1/web/search",
        A,
        json!({"query":"resume templates","locale":"ko-KR","limit":5}),
    )
    .await;
    assert_eq!(status, 200, "{result}");
    assert_eq!(result["items"].as_array().unwrap().len(), 1);
    assert_eq!(result["items"][0]["url"], "https://example.com/resume");
    assert!(!result.to_string().contains("synthetic-search-key"));
    assert!(
        f.store
            .sources("alice", Default::default())
            .unwrap()
            .items
            .is_empty()
    );
}
#[tokio::test]
async fn wi22_capture_requires_a_valid_fresh_body_signature() {
    use hmac::{Hmac, Mac};
    use sha2::Sha256;
    let tmp = tempfile::tempdir().unwrap();
    let f = fixture(&tmp.path().join("db")).await;
    let data = json!({"url":format!("{}/doc?PRIVATE=1",f.url),"html":PAGE,"kind":"template"});
    let (status, claimed) = post(&f.app, "/v1/web/clip", A, data.clone()).await;
    assert_eq!(status, 200, "{claimed}");
    assert_eq!(claimed["origin"]["provenance"], "claimed");
    let bytes = data.to_string();
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs();
    for (time, bad, expected) in [(now, false, 200), (now, true, 401), (now - 120, false, 401)] {
        let time = time.to_string();
        let mut mac =
            Hmac::<Sha256>::new_from_slice(b"synthetic-capture-secret-1234567890").unwrap();
        mac.update(time.as_bytes());
        mac.update(b"\n");
        mac.update(bytes.as_bytes());
        let proof = if bad {
            "a".repeat(64)
        } else {
            mac.finalize()
                .into_bytes()
                .iter()
                .map(|b| format!("{b:02x}"))
                .collect()
        };
        let request = Request::builder()
            .uri("/v1/web/clip")
            .method("POST")
            .header("authorization", format!("Bearer {A}"))
            .header("content-type", "application/json")
            .header("x-dmem-capture-time", time)
            .header("x-dmem-capture-proof", proof)
            .body(Body::from(bytes.clone()))
            .unwrap();
        let response = f.app.clone().oneshot(request).await.unwrap();
        assert_eq!(response.status().as_u16(), expected);
        if expected == 200 {
            let body = response.into_body().collect().await.unwrap().to_bytes();
            let value: Value = serde_json::from_slice(&body).unwrap();
            assert_eq!(value["origin"]["provenance"], "captured");
            assert!(!value.to_string().contains("PRIVATE"));
        }
    }
}
#[tokio::test]
async fn wi09_expired_previews_and_wi13_promoted_sources_keep_boundaries() {
    let tmp = tempfile::tempdir().unwrap();
    let f = fixture(&tmp.path().join("db")).await;
    let mut config =
        WebConfig::isolated_fixture(f.url.trim_start_matches("http://").parse().unwrap());
    config.preview_ttl = Some(0);
    let app = router_with_services(
        f.store.clone(),
        vec![(A.into(), "alice".into())],
        vec![],
        None,
        AuthConfig::default(),
        config,
    )
    .unwrap();
    let (_, p) = post(
        &app,
        "/v1/web/preview",
        A,
        json!({"url":format!("{}/doc",f.url)}),
    )
    .await;
    assert_eq!(
        post(
            &app,
            "/v1/web/import",
            A,
            json!({"preview_id":p["preview_id"],"kind":"template"})
        )
        .await
        .0,
        404
    );
    *f.content.lock().unwrap() =
        "<title>Unknown</title><h2>Unique source section</h2><p>PROSE_TEST</p>".into();
    let (_, p) = post(
        &f.app,
        "/v1/web/preview",
        A,
        json!({"url":format!("{}/doc",f.url)}),
    )
    .await;
    let (_, source) = post(
        &f.app,
        "/v1/web/import",
        A,
        json!({"preview_id":p["preview_id"],"kind":"reference"}),
    )
    .await;
    let template = f
        .store
        .template_from_source("alice", source["id"].as_str().unwrap())
        .unwrap();
    assert_eq!(post(&f.app,"/v1/me/contributions",A,json!({"template_id":template.id,"author":"Synthetic author","license":"CC0-1.0","rights_confirmed":true})).await.0,403);
}
#[tokio::test]
async fn wi11_reference_form_survives_reload_and_template_extraction() {
    let tmp = tempfile::tempdir().unwrap();
    let f = fixture(&tmp.path().join("db")).await;
    let (_, p) = post(
        &f.app,
        "/v1/web/preview",
        A,
        json!({"url":format!("{}/doc",f.url)}),
    )
    .await;
    let (status, source) = post(&f.app, "/v1/web/import", A, json!({"preview_id":p["preview_id"],"kind":"reference","form":{"provider":"google_docs","doc_type":"resume","locale":"ja-JP","variant":"jp_rirekisho"}})).await;
    assert_eq!(status, 200);
    let id = source["id"].as_str().unwrap();
    let origin = serde_json::to_value(f.store.web_origin("alice", id).unwrap()).unwrap();
    assert_eq!(origin["form"]["locale"], "ja-JP");
    assert_eq!(origin["form"]["region"], "JP");
    let reopened = Store::open(&tmp.path().join("db")).unwrap();
    let template = reopened.template_from_source("alice", id).unwrap();
    assert_eq!(template.form.provider, dmem_contracts::Provider::GoogleDocs);
    assert_eq!(template.form.doc_type, "resume");
    assert_eq!(template.form.locale, "ja-JP");
    assert_eq!(template.form.region.as_deref(), Some("JP"));
    assert_eq!(template.form.variant.as_deref(), Some("jp_rirekisho"));
}
#[tokio::test]
async fn wi11_detected_british_locale_keeps_its_region() {
    let tmp = tempfile::tempdir().unwrap();
    let f = fixture(&tmp.path().join("db")).await;
    *f.content.lock().unwrap() = PAGE.replace("ko-KR", "en-GB");
    let (status, preview) = post(
        &f.app,
        "/v1/web/preview",
        A,
        json!({"url":format!("{}/doc",f.url)}),
    )
    .await;
    assert_eq!(status, 200);
    assert_eq!(preview["form"]["locale"], "en-GB");
    assert_eq!(preview["form"]["region"], "GB");
}
#[tokio::test]
async fn wi13_publication_and_private_copies_keep_immutable_external_attribution() {
    let tmp = tempfile::tempdir().unwrap();
    let f = fixture(&tmp.path().join("db")).await;
    let (_, preview) = post(
        &f.app,
        "/v1/web/preview",
        A,
        json!({"url":format!("{}/doc?PRIVATE=1",f.url)}),
    )
    .await;
    let (_, item) = post(
        &f.app,
        "/v1/web/import",
        A,
        json!({"preview_id":preview["preview_id"],"kind":"template"}),
    )
    .await;
    let (status,denied)=post(&f.app,"/v1/me/contributions",A,json!({"template_id":item["id"],"author":"Synthetic author","license":"CC0-1.0","rights_confirmed":true})).await;
    assert_eq!(status, 403, "{denied}");
    let (status,pending)=post(&f.app,"/v1/me/contributions",A,json!({"template_id":item["id"],"author":"Synthetic author","license":"CC-BY-4.0","rights_confirmed":true})).await;
    assert_eq!(status, 200, "{pending}");
    let (status, published) = post(
        &f.app,
        &format!(
            "/v1/admin/contributions/{}/decision",
            pending["id"].as_str().unwrap()
        ),
        ADMIN,
        json!({"decision":"approve"}),
    )
    .await;
    assert_eq!(status, 200, "{published}");
    let public_id = published["public_id"].as_str().unwrap();
    let request = Request::builder()
        .uri(format!("/v1/public/templates/{public_id}/origin"))
        .body(Body::empty())
        .unwrap();
    let response = f.app.clone().oneshot(request).await.unwrap();
    assert_eq!(response.status(), 200);
    let bytes = response.into_body().collect().await.unwrap().to_bytes();
    let origin: Value = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(origin["record_id"], public_id);
    assert_eq!(origin["license"], "CC-BY-4.0");
    assert!(!origin.to_string().contains(item["id"].as_str().unwrap()));
    assert!(!origin.to_string().contains("PRIVATE"));
    let copied = f.store.copy_template("bob", public_id).unwrap();
    assert_eq!(
        f.store.web_origin("bob", &copied.id).unwrap().license,
        "CC-BY-4.0"
    );
}
