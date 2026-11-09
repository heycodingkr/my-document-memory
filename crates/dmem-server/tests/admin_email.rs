use axum::{
    Router,
    body::Body,
    http::{Request, StatusCode},
};
use dmem_contracts::Fault;
use dmem_server::{AuthConfig, Delivery, EmailSender, Store, router_with_auth};
use http_body_util::BodyExt;
use serde_json::{Value, json};
use std::{
    path::PathBuf,
    sync::{
        Arc, Mutex,
        atomic::{AtomicBool, AtomicU64, Ordering},
    },
};
use tower::ServiceExt;

const ORIGIN: &str = "http://localhost:5174";
const LOCAL: &str = "synthetic-admin-test-local-token";
const OPERATOR: &str = "synthetic-distinct-operator-token-at-least-32-characters";
#[derive(Default)]
struct Mail {
    links: Mutex<Vec<(String, String)>>,
    fail: AtomicBool,
}
impl EmailSender for Mail {
    fn send_code(&self, _: String, _: String, _: String) -> Delivery {
        Box::pin(async { Err(Fault::ServerUnavailable) })
    }
    fn send_link(&self, email: String, url: String, _: String) -> Delivery {
        self.links.lock().unwrap().push((email, url));
        let fail = self.fail.load(Ordering::SeqCst);
        Box::pin(async move {
            if fail {
                Err(Fault::ServerUnavailable)
            } else {
                Ok(())
            }
        })
    }
}
struct R {
    status: StatusCode,
    body: Value,
    cookies: Vec<String>,
    cache: String,
}
async fn req(
    app: &Router,
    method: &str,
    path: &str,
    value: Option<Value>,
    cookies: &str,
    csrf: &str,
    bearer: &str,
    origin: Option<&str>,
) -> R {
    let mut request = Request::builder()
        .method(method)
        .uri(path)
        .header("Content-Type", "application/json");
    if let Some(origin) = origin {
        request = request.header("Origin", origin);
    }
    if !cookies.is_empty() {
        request = request.header("Cookie", cookies);
    }
    if !csrf.is_empty() {
        request = request.header("X-CSRF-Token", csrf);
    }
    if !bearer.is_empty() {
        request = request.header("Authorization", format!("Bearer {bearer}"));
    }
    let response = app
        .clone()
        .oneshot(
            request
                .body(Body::from(value.map(|v| v.to_string()).unwrap_or_default()))
                .unwrap(),
        )
        .await
        .unwrap();
    let status = response.status();
    let cookies = response
        .headers()
        .get_all("set-cookie")
        .iter()
        .map(|v| v.to_str().unwrap().to_owned())
        .collect();
    let cache = response
        .headers()
        .get("cache-control")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("")
        .to_owned();
    let bytes = response.into_body().collect().await.unwrap().to_bytes();
    R {
        status,
        cookies,
        cache,
        body: serde_json::from_slice(&bytes).unwrap_or(Value::Null),
    }
}
struct F {
    _temp: tempfile::TempDir,
    path: PathBuf,
    store: Arc<Store>,
    auth: AuthConfig,
    mail: Arc<Mail>,
    clock: Arc<AtomicU64>,
    app: Router,
}
impl F {
    fn new(allowlist: &str) -> Self {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("admin.sqlite3");
        let store = Arc::new(Store::open(&path).unwrap());
        let mail = Arc::new(Mail::default());
        let clock = Arc::new(AtomicU64::new(100000));
        let mut auth = AuthConfig::new(
            "synthetic-stable-auth-secret-at-least-32-characters".into(),
            mail.clone(),
        )
        .unwrap();
        let emails = if allowlist.trim().is_empty() {
            Vec::new()
        } else {
            allowlist.split(',').map(str::trim).map(str::to_owned).collect()
        };
        auth.set_admin_emails(emails).unwrap();
        auth.admin_token = Some(OPERATOR.into());
        auth.secure_cookies = true;
        let now = clock.clone();
        auth.clock = Arc::new(move || now.load(Ordering::SeqCst));
        let app = Self::router(store.clone(), auth.clone());
        Self {
            _temp: temp,
            path,
            store,
            auth,
            mail,
            clock,
            app,
        }
    }
    fn router(store: Arc<Store>, auth: AuthConfig) -> Router {
        router_with_auth(
            store,
            vec![(LOCAL.into(), "local".into())],
            vec![ORIGIN.into()],
            None,
            auth,
        )
        .unwrap()
    }
    async fn call(
        &self,
        method: &str,
        path: &str,
        value: Option<Value>,
        cookie: &str,
        csrf: &str,
    ) -> R {
        req(
            &self.app,
            method,
            path,
            value,
            cookie,
            csrf,
            "",
            Some(ORIGIN),
        )
        .await
    }
    async fn start(&self, email: &str) -> R {
        self.call(
            "POST",
            "/v1/admin/auth/email/link",
            Some(json!({"email":email})),
            "",
            "",
        )
        .await
    }
    fn link(&self) -> String {
        let links = self.mail.links.lock().unwrap();
        reqwest::Url::parse(&links.last().unwrap().1)
            .unwrap()
            .fragment()
            .unwrap()
            .strip_prefix("admin-sign-in=")
            .unwrap()
            .to_owned()
    }
    async fn consume(&self, token: &str) -> R {
        self.call(
            "POST",
            "/v1/admin/auth/email/consume",
            Some(json!({"token":token})),
            "",
            "",
        )
        .await
    }
    async fn login(&self) -> (String, String) {
        assert_eq!(
            self.start("operator@example.test").await.status,
            StatusCode::ACCEPTED
        );
        let response = self.consume(&self.link()).await;
        assert_eq!(response.status, StatusCode::OK);
        let header = response
            .cookies
            .iter()
            .find(|c| c.starts_with("dmem_admin_session="))
            .unwrap();
        assert!(
            header.contains("HttpOnly")
                && header.contains("SameSite=Lax")
                && header.contains("Secure")
        );
        assert!(header.contains("Max-Age=7200"));
        assert_eq!(response.cache, "no-store");
        (
            header.split(';').next().unwrap().to_owned(),
            response.body["csrf_token"].as_str().unwrap().to_owned(),
        )
    }
    async fn submission(&self) -> Value {
        let created=req(&self.app,"POST","/v1/templates",Some(json!({"title":"Independent admin review fixture","summary":"Original reusable structure for a synthetic operator decision.","form":{"provider":"docx","doc_type":"report","locale":"en-US"},"sections":["Independent operational context","Distinct decision acceptance criteria","Assigned follow-up verification"],"tags":[]})),"","",LOCAL,Some(ORIGIN)).await;
        assert_eq!(created.status, StatusCode::OK);
        let submitted=req(&self.app,"POST","/v1/me/contributions",Some(json!({"template_id":created.body["id"],"author":"Synthetic reviewer","license":"CC-BY-4.0","rights_confirmed":true})),"","",LOCAL,Some(ORIGIN)).await;
        assert_eq!(submitted.status, StatusCode::OK);
        submitted.body
    }
}
#[tokio::test]
async fn unconfigured_admin_allowlist_accepts_request_without_sending_mail() {
    let f = F::new("");
    let response = f.start("operator@example.test").await;
    assert_eq!(response.status, StatusCode::ACCEPTED);
    assert_eq!(response.body["accepted"], true);
    assert!(f.mail.links.lock().unwrap().is_empty());
    assert_eq!(response.cache, "no-store");
    assert_eq!(
        f.call("GET", "/v1/admin/auth/config", None, "", "")
            .await
            .body["enabled"],
        false
    );
}
#[tokio::test]
async fn only_exact_normalized_allowed_email_gets_mail_with_generic_response() {
    let f = F::new(" Operator@Example.Test ,second@example.test ");
    let denied = f.start("operator+other@example.test").await;
    let allowed = f.start(" OPERATOR@EXAMPLE.TEST ").await;
    assert_eq!(denied.status, allowed.status);
    assert_eq!(denied.body, allowed.body);
    assert_eq!(denied.cookies, allowed.cookies);
    let links = f.mail.links.lock().unwrap();
    assert_eq!(links.len(), 1);
    assert_eq!(links[0].0, "operator@example.test");
    let url = reqwest::Url::parse(&links[0].1).unwrap();
    assert_eq!(url.origin().ascii_serialization(), ORIGIN);
    assert!(url.query().is_none());
    drop(links);
    assert_eq!(
        f.start("operator@example.test").await.status,
        StatusCode::ACCEPTED
    );
    assert_eq!(f.mail.links.lock().unwrap().len(), 1);
}
#[test]
fn invalid_allowlist_fails_closed_and_does_not_replace_valid_configuration() {
    let mut auth = AuthConfig::default();
    auth.set_admin_emails(["operator@example.test".to_owned()]).unwrap();
    for invalid in [
        "operator@example.test,",
        "*@example.test",
        "invalid",
        "operator@example.test,\nwrong",
    ] {
        assert_eq!(
            auth.set_admin_emails([invalid.to_owned()]),
            Err(Fault::InvalidInput)
        );
    }
}
#[tokio::test]
async fn administrator_link_requires_post_is_single_use_and_not_a_member_session() {
    let f = F::new("operator@example.test");
    f.start("operator@example.test").await;
    let token = f.link();
    assert_ne!(
        f.call("GET", "/v1/admin/auth/email/consume", None, "", "")
            .await
            .status,
        StatusCode::OK
    );
    assert_eq!(
        f.call("GET", "/v1/admin/auth/session", None, "", "")
            .await
            .status,
        StatusCode::UNAUTHORIZED
    );
    let mut changed = token.clone();
    let last = changed.pop().unwrap();
    changed.push(if last == '0' { '1' } else { '0' });
    assert_eq!(f.consume(&changed).await.status, StatusCode::UNAUTHORIZED);
    let response = f.consume(&token).await;
    assert_eq!(response.status, StatusCode::OK);
    let cookie = response.cookies[0].split(';').next().unwrap();
    assert_eq!(f.consume(&token).await.status, StatusCode::UNAUTHORIZED);
    assert_eq!(
        f.call("GET", "/v1/auth/session", None, cookie, "")
            .await
            .status,
        StatusCode::UNAUTHORIZED
    );
    assert_eq!(
        f.call("GET", "/v1/admin/auth/session", None, cookie, "")
            .await
            .status,
        StatusCode::OK
    );
}
#[tokio::test]
async fn expired_undelivered_and_revoked_links_cannot_create_admin_sessions() {
    let f = F::new("operator@example.test");
    f.start("operator@example.test").await;
    let token = f.link();
    f.clock.fetch_add(600, Ordering::SeqCst);
    assert_eq!(f.consume(&token).await.status, StatusCode::UNAUTHORIZED);
    let f = F::new("operator@example.test");
    f.mail.fail.store(true, Ordering::SeqCst);
    assert_eq!(
        f.start("operator@example.test").await.status,
        StatusCode::ACCEPTED
    );
    assert_eq!(f.consume(&f.link()).await.status, StatusCode::UNAUTHORIZED);
    let f = F::new("operator@example.test");
    f.start("operator@example.test").await;
    let token = f.link();
    let mut revoked = f.auth.clone();
    revoked.set_admin_emails(Vec::<String>::new()).unwrap();
    let app = F::router(f.store.clone(), revoked);
    assert_eq!(
        req(
            &app,
            "POST",
            "/v1/admin/auth/email/consume",
            Some(json!({"token":token})),
            "",
            "",
            "",
            Some(ORIGIN)
        )
        .await
        .status,
        StatusCode::UNAUTHORIZED
    );
}
#[tokio::test]
async fn ordinary_magic_links_and_library_tokens_do_not_grant_admin_authority() {
    let f = F::new("operator@example.test");
    assert_eq!(
        f.call(
            "POST",
            "/v1/auth/email/link",
            Some(json!({"email":"operator@example.test"})),
            "",
            ""
        )
        .await
        .status,
        StatusCode::ACCEPTED
    );
    let link = f.mail.links.lock().unwrap().last().unwrap().1.clone();
    let url = reqwest::Url::parse(&link).unwrap();
    let token = url.fragment().unwrap().strip_prefix("sign-in=").unwrap();
    assert_eq!(f.consume(token).await.status, StatusCode::UNAUTHORIZED);
    let member = f
        .call(
            "POST",
            "/v1/auth/email/consume",
            Some(json!({"token":token})),
            "",
            "",
        )
        .await;
    assert_eq!(member.status, StatusCode::OK);
    let cookie = member
        .cookies
        .iter()
        .find(|s| s.starts_with("dmem_session="))
        .unwrap()
        .split(';')
        .next()
        .unwrap();
    assert_eq!(
        f.call("GET", "/v1/admin/contributions", None, cookie, "")
            .await
            .status,
        StatusCode::UNAUTHORIZED
    );
    for bearer in ["", LOCAL] {
        assert_eq!(
            req(
                &f.app,
                "GET",
                "/v1/admin/contributions",
                None,
                "",
                "",
                bearer,
                None
            )
            .await
            .status,
            StatusCode::UNAUTHORIZED
        );
    }
    assert_eq!(
        req(
            &f.app,
            "GET",
            "/v1/admin/contributions",
            None,
            "",
            "",
            OPERATOR,
            None
        )
        .await
        .status,
        StatusCode::OK
    );
}
#[tokio::test]
async fn session_review_requires_csrf_and_origin_and_audits_only_committed_decision() {
    let f = F::new("operator@example.test");
    let submission = f.submission().await;
    let (cookie, csrf) = f.login().await;
    let path = format!(
        "/v1/admin/contributions/{}/decision",
        submission["id"].as_str().unwrap()
    );
    assert_eq!(
        f.call("GET", "/v1/admin/contributions", None, &cookie, "")
            .await
            .status,
        StatusCode::OK
    );
    for (token, origin, bearer) in [
        ("", Some(ORIGIN), ""),
        ("wrong", Some(ORIGIN), ""),
        (csrf.as_str(), Some("https://untrusted.example.test"), ""),
        (csrf.as_str(), None, ""),
        (csrf.as_str(), Some(ORIGIN), LOCAL),
    ] {
        assert_eq!(
            req(
                &f.app,
                "POST",
                &path,
                Some(json!({"decision":"approve"})),
                &cookie,
                token,
                bearer,
                origin
            )
            .await
            .status,
            StatusCode::UNAUTHORIZED
        );
    }
    let public = format!(
        "/v1/public/templates/{}",
        submission["snapshot"]["id"].as_str().unwrap()
    );
    assert_eq!(
        f.call("GET", &public, None, "", "").await.status,
        StatusCode::NOT_FOUND
    );
    assert_eq!(
        f.call(
            "POST",
            &path,
            Some(json!({"decision":"approve"})),
            &cookie,
            &csrf
        )
        .await
        .status,
        StatusCode::OK
    );
    assert_eq!(
        f.call("GET", &public, None, "", "").await.status,
        StatusCode::OK
    );
    assert_eq!(
        f.call(
            "POST",
            &path,
            Some(json!({"decision":"approve"})),
            &cookie,
            &csrf
        )
        .await
        .status,
        StatusCode::CONFLICT
    );
    let db = rusqlite::Connection::open(&f.path).unwrap();
    let (count, actor): (u32, String) = db
        .query_row("SELECT count(*),actor FROM admin_decision_audit", [], |r| {
            Ok((r.get(0)?, r.get(1)?))
        })
        .unwrap();
    assert_eq!(count, 1);
    assert!(actor.starts_with("admin:") && !actor.contains("operator@example.test"));
}
#[tokio::test]
async fn session_persists_but_revocation_expiry_and_logout_remove_authority() {
    let f = F::new("operator@example.test");
    let (cookie, csrf) = f.login().await;
    let restarted = F::router(Arc::new(Store::open(&f.path).unwrap()), f.auth.clone());
    assert_eq!(
        req(
            &restarted,
            "GET",
            "/v1/admin/contributions",
            None,
            &cookie,
            "",
            "",
            None
        )
        .await
        .status,
        StatusCode::OK
    );
    let mut revoked = f.auth.clone();
    revoked.set_admin_emails(Vec::<String>::new()).unwrap();
    let revoked = F::router(f.store.clone(), revoked);
    assert_eq!(
        req(
            &revoked,
            "GET",
            "/v1/admin/contributions",
            None,
            &cookie,
            "",
            "",
            None
        )
        .await
        .status,
        StatusCode::UNAUTHORIZED
    );
    assert_eq!(
        f.call("POST", "/v1/admin/auth/logout", None, &cookie, "")
            .await
            .status,
        StatusCode::UNAUTHORIZED
    );
    assert_eq!(
        f.call("POST", "/v1/admin/auth/logout", None, &cookie, &csrf)
            .await
            .status,
        StatusCode::OK
    );
    assert_eq!(
        f.call("GET", "/v1/admin/contributions", None, &cookie, "")
            .await
            .status,
        StatusCode::UNAUTHORIZED
    );
    let f = F::new("operator@example.test");
    let (cookie, _) = f.login().await;
    f.clock.fetch_add(2 * 3600, Ordering::SeqCst);
    assert_eq!(
        f.call("GET", "/v1/admin/contributions", None, &cookie, "")
            .await
            .status,
        StatusCode::UNAUTHORIZED
    );
}
