use axum::{
    Router,
    body::Body,
    http::{Request, StatusCode},
};
use dmem_contracts::Fault;
use dmem_server::{AuthConfig, Delivery, EmailSender, Store, router, router_with_auth};
use http_body_util::BodyExt;
use serde_json::{Value, json};
use std::sync::{
    Arc, Mutex,
    atomic::{AtomicBool, AtomicU64, Ordering},
};
use tower::ServiceExt;
const ORIGIN: &str = "http://localhost:5174";
const ADMIN: &str = "separate-test-admin-key-32-characters-long";
const LOCAL: &str = "test-local-owner-token";
#[derive(Default)]
struct Mail {
    codes: Mutex<Vec<(String, String)>>,
    links: Mutex<Vec<(String, String)>>,
    fail: AtomicBool,
}
impl EmailSender for Mail {
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
    fn send_code(&self, email: String, code: String, _: String) -> Delivery {
        self.codes.lock().unwrap().push((email, code));
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
struct Harness {
    app: Router,
    mail: Arc<Mail>,
    time: Arc<AtomicU64>,
    path: std::path::PathBuf,
    _dir: tempfile::TempDir,
    config: AuthConfig,
}
struct R {
    status: StatusCode,
    data: Value,
    cookies: String,
    raw: String,
}
async fn req(
    app: &Router,
    method: &str,
    path: &str,
    input: Option<Value>,
    cookies: &str,
    csrf: &str,
    token: &str,
    origin: &str,
) -> R {
    let mut b = Request::builder().method(method).uri(path);
    if !origin.is_empty() {
        b = b.header("Origin", origin)
    }
    if !cookies.is_empty() {
        b = b.header("Cookie", cookies)
    }
    if !csrf.is_empty() {
        b = b.header("X-CSRF-Token", csrf)
    }
    if !token.is_empty() {
        b = b.header("Authorization", format!("Bearer {token}"))
    }
    let body = if let Some(input) = input {
        b = b.header("Content-Type", "application/json");
        Body::from(input.to_string())
    } else {
        Body::empty()
    };
    let res = app.clone().oneshot(b.body(body).unwrap()).await.unwrap();
    let status = res.status();
    assert_eq!(res.headers().get("cache-control").unwrap(), "no-store");
    let cookies = res
        .headers()
        .get_all("set-cookie")
        .iter()
        .map(|v| v.to_str().unwrap().split(';').next().unwrap().to_owned())
        .collect::<Vec<_>>()
        .join("; ");
    for v in res.headers().get_all("set-cookie") {
        let v = v.to_str().unwrap();
        assert!(v.contains("HttpOnly") && v.contains("SameSite=Lax"));
    }
    let raw =
        String::from_utf8(res.into_body().collect().await.unwrap().to_bytes().to_vec()).unwrap();
    let data = serde_json::from_str(&raw).unwrap_or(Value::Null);
    R {
        status,
        data,
        cookies,
        raw,
    }
}
impl Harness {
    fn new() -> Self {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("accounts.sqlite3");
        let mail = Arc::new(Mail::default());
        let time = Arc::new(AtomicU64::new(100_000));
        let mut config = AuthConfig::new(
            "synthetic-identity-secret-at-least-32-chars".into(),
            mail.clone(),
        )
        .unwrap();
        config.admin_token = Some(ADMIN.into());
        config.set_admin_emails(" Operator@Example.Test ").unwrap();
        let clock = time.clone();
        config.clock = Arc::new(move || clock.load(Ordering::SeqCst));
        let app = Self::router(&path, config.clone());
        Self {
            app,
            mail,
            time,
            path,
            _dir: dir,
            config,
        }
    }
    fn router(path: &std::path::Path, auth: AuthConfig) -> Router {
        router_with_auth(
            Arc::new(Store::open(path).unwrap()),
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
        input: Option<Value>,
        cookies: &str,
        csrf: &str,
    ) -> R {
        req(&self.app, method, path, input, cookies, csrf, "", ORIGIN).await
    }
    async fn begin(&self, email: &str, cookies: &str) -> R {
        self.call(
            "POST",
            "/v1/auth/email/start",
            Some(json!({"email":email})),
            cookies,
            "",
        )
        .await
    }
    async fn login(&self, email: &str) -> (String, String, String) {
        let s = self.begin(email, "").await;
        assert_eq!(s.status, 202);
        let code = self.mail.codes.lock().unwrap().last().unwrap().1.clone();
        assert!(!s.raw.contains(&code));
        let v = self
            .call(
                "POST",
                "/v1/auth/email/verify",
                Some(json!({"code":code})),
                &s.cookies,
                "",
            )
            .await;
        assert_eq!(v.status, 200);
        (
            v.cookies,
            v.data["csrf_token"].as_str().unwrap().into(),
            v.data["account"]["id"].as_str().unwrap().into(),
        )
    }
}
#[tokio::test]
async fn magic_link_request_is_available_without_a_session() {
    let h = Harness::new();
    let result = h
        .call(
            "POST",
            "/v1/auth/email/link",
            Some(json!({"email":"Link@Example.Test"})),
            "",
            "",
        )
        .await;
    assert_eq!(
        result.status,
        StatusCode::ACCEPTED,
        "email-link requests should issue a login email"
    );
    assert_eq!(result.data["expires_in"], 600);
    assert_eq!(result.data["retry_after"], 60);
}
fn captured_link(h: &Harness) -> String {
    let messages = h.mail.links.lock().unwrap();
    let (email, url) = messages.last().unwrap();
    assert_eq!(email, "link@example.test");
    let url = reqwest::Url::parse(url).unwrap();
    assert_eq!(url.origin().ascii_serialization(), ORIGIN);
    assert_eq!(url.path(), "/");
    assert!(url.query().is_none());
    url.fragment()
        .unwrap()
        .strip_prefix("sign-in=")
        .unwrap()
        .to_owned()
}
fn captured_admin_link(h: &Harness) -> String {
    let messages = h.mail.links.lock().unwrap();
    let (email, url) = messages.last().unwrap();
    assert_eq!(email, "operator@example.test");
    let url = reqwest::Url::parse(url).unwrap();
    assert_eq!(url.origin().ascii_serialization(), ORIGIN);
    url.fragment()
        .unwrap()
        .strip_prefix("admin-sign-in=")
        .unwrap()
        .to_owned()
}
#[tokio::test]
async fn magic_links_are_portable_hashed_and_atomically_single_use() {
    let h = Harness::new();
    let sent = h
        .call(
            "POST",
            "/v1/auth/email/link",
            Some(json!({"email":" Link@Example.Test "})),
            "",
            "",
        )
        .await;
    assert_eq!(sent.status, 202);
    let token = captured_link(&h);
    let (challenge, verifier) = token.split_once('.').unwrap();
    assert_eq!((challenge.len(), verifier.len()), (64, 64));
    assert!(!sent.raw.contains(challenge) && !sent.raw.contains(verifier));
    let db = rusqlite::Connection::open(&h.path).unwrap();
    let stored: (String, String) = db
        .query_row("SELECT id_hash,code_hash FROM email_challenges", [], |r| {
            Ok((r.get(0)?, r.get(1)?))
        })
        .unwrap();
    assert_ne!(stored.0, challenge);
    assert_ne!(stored.1, verifier);
    let mut bad = token.clone();
    bad.replace_range(65..66, if &token[65..66] == "a" { "b" } else { "a" });
    assert_eq!(
        h.call(
            "POST",
            "/v1/auth/email/consume",
            Some(json!({"token":bad})),
            "",
            ""
        )
        .await
        .status,
        401
    );
    // No requesting-browser cookie: the email may open in another browser.
    let (a, b) = tokio::join!(
        h.call(
            "POST",
            "/v1/auth/email/consume",
            Some(json!({"token":token})),
            "",
            ""
        ),
        h.call(
            "POST",
            "/v1/auth/email/consume",
            Some(json!({"token":token})),
            "",
            ""
        )
    );
    let mut statuses = [a.status.as_u16(), b.status.as_u16()];
    statuses.sort();
    assert_eq!(statuses, [200, 401]);
    let signed = if a.status == 200 { a } else { b };
    assert_eq!(signed.data["account"]["email"], "link@example.test");
    assert!(!signed.data["csrf_token"].as_str().unwrap().is_empty());
    assert_eq!(
        h.call("GET", "/v1/auth/session", None, &signed.cookies, "")
            .await
            .status,
        200
    );
}
#[tokio::test]
async fn magic_links_reject_expiry_failed_delivery_foreign_origins_and_bad_tokens() {
    for failure in [false, true] {
        let h = Harness::new();
        h.mail.fail.store(failure, Ordering::SeqCst);
        let sent = h
            .call(
                "POST",
                "/v1/auth/email/link",
                Some(json!({"email":"link@example.test"})),
                "",
                "",
            )
            .await;
        assert_eq!(sent.status, if failure { 503 } else { 202 });
        let token = captured_link(&h);
        if !failure {
            h.time.fetch_add(600, Ordering::SeqCst);
        }
        assert_eq!(
            h.call(
                "POST",
                "/v1/auth/email/consume",
                Some(json!({"token":token})),
                "",
                ""
            )
            .await
            .status,
            401
        );
        let db = rusqlite::Connection::open(&h.path).unwrap();
        assert_eq!(
            db.query_row("SELECT COUNT(*) FROM accounts", [], |r| r.get::<_, u64>(0))
                .unwrap(),
            0
        );
    }
    let h = Harness::new();
    for origin in ["", "https://evil.test"] {
        assert_eq!(
            req(
                &h.app,
                "POST",
                "/v1/auth/email/link",
                Some(json!({"email":"link@example.test"})),
                "",
                "",
                "",
                origin
            )
            .await
            .status,
            401
        );
    }
    assert!(h.mail.links.lock().unwrap().is_empty());
    let sent = h
        .call(
            "POST",
            "/v1/auth/email/link",
            Some(json!({"email":"link@example.test"})),
            "",
            "",
        )
        .await;
    assert_eq!(sent.status, 202);
    assert_eq!(
        h.call(
            "POST",
            "/v1/auth/email/link",
            Some(json!({"email":"link@example.test"})),
            &sent.cookies,
            ""
        )
        .await
        .status,
        429
    );
    let token = captured_link(&h);
    for bad in [
        "".to_owned(),
        "not-a-token".to_owned(),
        format!("{}.123456", token.split_once('.').unwrap().0),
        format!("{token}.extra"),
    ] {
        assert_eq!(
            h.call(
                "POST",
                "/v1/auth/email/consume",
                Some(json!({"token":bad})),
                "",
                ""
            )
            .await
            .status,
            401
        );
    }
    assert_eq!(
        req(
            &h.app,
            "POST",
            "/v1/auth/email/consume",
            Some(json!({"token":token})),
            "",
            "",
            "",
            "https://evil.test"
        )
        .await
        .status,
        401
    );
    assert_eq!(
        h.call(
            "POST",
            "/v1/auth/email/consume",
            Some(json!({"token":token})),
            "",
            ""
        )
        .await
        .status,
        200
    );
}
#[tokio::test]
async fn anonymous_public_catalog_exposes_seed_without_private_data() {
    let app = router(
        Arc::new(Store::open(":memory:").unwrap()),
        vec![(LOCAL.into(), "local".into())],
        vec![ORIGIN.into()],
        None,
    )
    .unwrap();
    let r = req(&app, "GET", "/v1/public/templates", None, "", "", "", "").await;
    assert_eq!(r.status, 200);
    assert!(!r.data["items"].as_array().unwrap().is_empty());
    assert!(
        r.data["items"]
            .as_array()
            .unwrap()
            .iter()
            .all(|t| t["visibility"] == "public")
    );
}
#[tokio::test]
async fn email_validation_disabled_sender_and_origin() {
    let h = Harness::new();
    for email in ["bad", "x@localhost", "a\r\nb@example.test", "a@-bad.test"] {
        assert_eq!(h.begin(email, "").await.status, 400)
    }
    for origin in ["", "https://evil.test"] {
        assert_eq!(
            req(
                &h.app,
                "POST",
                "/v1/auth/email/start",
                Some(json!({"email":"alice@example.test"})),
                "",
                "",
                "",
                origin
            )
            .await
            .status,
            401
        )
    }
    assert!(h.mail.codes.lock().unwrap().is_empty());
    assert_eq!(
        h.call(
            "POST",
            "/v1/auth/email/start",
            Some(json!({"email":"alice@example.test","unknown":true})),
            "",
            ""
        )
        .await
        .status,
        400
    );
    h.mail.fail.store(true, Ordering::SeqCst);
    assert_eq!(h.begin("alice@example.test", "").await.status, 503);
    let mut disabled = h.config.clone();
    disabled.mailer = None;
    let app = Harness::router(&h.path, disabled);
    assert_eq!(
        req(
            &app,
            "POST",
            "/v1/auth/email/start",
            Some(json!({"email":"new@example.test"})),
            "",
            "",
            "",
            ORIGIN
        )
        .await
        .status,
        503
    );
}
#[tokio::test]
async fn codes_are_browser_bound_attempt_limited_expiring_and_single_use() {
    let h = Harness::new();
    let s = h.begin("alice@example.test", "").await;
    assert_eq!(s.status, 202);
    let code = h.mail.codes.lock().unwrap().last().unwrap().1.clone();
    assert_eq!(
        h.call(
            "POST",
            "/v1/auth/email/verify",
            Some(json!({"code":code})),
            "",
            ""
        )
        .await
        .status,
        401
    );
    for _ in 0..5 {
        assert_eq!(
            h.call(
                "POST",
                "/v1/auth/email/verify",
                Some(json!({"code":"invalid"})),
                &s.cookies,
                ""
            )
            .await
            .status,
            401
        )
    }
    assert_eq!(
        h.call(
            "POST",
            "/v1/auth/email/verify",
            Some(json!({"code":code})),
            &s.cookies,
            ""
        )
        .await
        .status,
        401
    );
    assert_eq!(h.begin("alice@example.test", &s.cookies).await.status, 429);
    h.time.fetch_add(61, Ordering::SeqCst);
    let next = h.begin("alice@example.test", &s.cookies).await;
    assert_eq!(next.status, 202);
    let next_code = h.mail.codes.lock().unwrap().last().unwrap().1.clone();
    assert_eq!(
        h.call(
            "POST",
            "/v1/auth/email/verify",
            Some(json!({"code":code})),
            &s.cookies,
            ""
        )
        .await
        .status,
        401
    );
    h.time.fetch_add(601, Ordering::SeqCst);
    assert_eq!(
        h.call(
            "POST",
            "/v1/auth/email/verify",
            Some(json!({"code":next_code})),
            &next.cookies,
            ""
        )
        .await
        .status,
        401
    );
    let s = h.begin("alice@example.test", &next.cookies).await;
    let code = h.mail.codes.lock().unwrap().last().unwrap().1.clone();
    assert_eq!(
        h.call(
            "POST",
            "/v1/auth/email/verify",
            Some(json!({"code":code})),
            &s.cookies,
            ""
        )
        .await
        .status,
        200
    );
    assert_eq!(
        h.call(
            "POST",
            "/v1/auth/email/verify",
            Some(json!({"code":code})),
            &s.cookies,
            ""
        )
        .await
        .status,
        401
    );
}
#[tokio::test]
async fn session_persistence_csrf_logout_and_owner_isolation() {
    let h = Harness::new();
    let (cookie, csrf, id) = h.login(" Alice@Example.Test ").await;
    let r = h.call("GET", "/v1/auth/session", None, &cookie, "").await;
    assert_eq!(r.data["account"]["email"], "alice@example.test");
    let create = json!({"title":"Alice private","summary":"private","form":{"provider":"docx","doc_type":"report","locale":"ko-KR"},"sections":["배경"],"tags":[]});
    for bad in ["", "bad-csrf"] {
        assert_eq!(
            h.call("POST", "/v1/templates", Some(create.clone()), &cookie, bad)
                .await
                .status,
            401
        )
    }
    assert_eq!(
        req(
            &h.app,
            "POST",
            "/v1/templates",
            Some(create.clone()),
            &cookie,
            &csrf,
            "",
            "https://evil.test"
        )
        .await
        .status,
        401
    );
    let t = h
        .call("POST", "/v1/templates", Some(create), &cookie, &csrf)
        .await;
    assert_eq!(t.status, 200);
    let tid = t.data["id"].as_str().unwrap();
    let (bob, _, _) = h.login("bob@example.test").await;
    assert_eq!(
        h.call("GET", &format!("/v1/templates/{tid}"), None, &bob, "")
            .await
            .status,
        404
    );
    assert_eq!(
        h.call("GET", "/v1/me", None, &cookie, "").await.data["templates"],
        1
    );
    assert_eq!(
        h.call("GET", "/v1/me", None, &bob, "").await.data["templates"],
        0
    );
    let reopened = Harness::router(&h.path, h.config.clone());
    assert_eq!(
        req(
            &reopened,
            "GET",
            "/v1/auth/session",
            None,
            &cookie,
            "",
            "",
            ""
        )
        .await
        .data["account"]["id"],
        id
    );
    let db = rusqlite::Connection::open(&h.path).unwrap();
    let stored: String = db
        .query_row(
            "SELECT token_hash FROM sessions WHERE account_id=?1",
            [id],
            |r| r.get(0),
        )
        .unwrap();
    assert!(!cookie.contains(&stored));
    assert_eq!(
        h.call("POST", "/v1/auth/logout", None, &cookie, "")
            .await
            .status,
        401
    );
    assert_eq!(
        h.call("POST", "/v1/auth/logout", None, &cookie, &csrf)
            .await
            .status,
        200
    );
    assert_eq!(
        h.call("GET", "/v1/auth/session", None, &cookie, "")
            .await
            .status,
        401
    );
    h.time.fetch_add(61, Ordering::SeqCst);
    let (_, _, again) = h.login("alice@example.test").await;
    assert_eq!(again, r.data["account"]["id"]);
}
#[tokio::test]
async fn hourly_email_limit_and_session_expiry() {
    let h = Harness::new();
    for i in 0..10 {
        let s = h.begin("limit@example.test", "").await;
        assert_eq!(s.status, 202, "request {i}");
        h.time.fetch_add(61, Ordering::SeqCst);
    }
    assert_eq!(h.begin("limit@example.test", "").await.status, 429);
    let (cookie, _, _) = h.login("alice@example.test").await;
    h.time.fetch_add(30 * 86400, Ordering::SeqCst);
    assert_eq!(
        h.call("GET", "/v1/auth/session", None, &cookie, "")
            .await
            .status,
        401
    );
}
#[tokio::test]
async fn public_reading_is_anonymous_but_contributions_require_a_registered_member() {
    let h = Harness::new();
    for path in [
        "/v1/public/templates",
        "/v1/public/templates/meeting.minutes.ko",
    ] {
        let response = req(&h.app, "GET", path, None, "", "", "", "").await;
        assert_eq!(response.status, 200, "{path}");
        assert!(!response.raw.contains("\"owner\":"));
        assert!(!response.raw.contains("\"email\":"));
    }
    // A configured local token authenticates its private library, but does not sign up a member.
    assert_eq!(
        req(&h.app, "GET", "/v1/templates", None, "", "", LOCAL, "")
            .await
            .status,
        200
    );
    for token in ["", LOCAL, ADMIN, "invalid-synthetic-token"] {
        for (method, path) in [
            ("GET", "/v1/me/contributions"),
            ("POST", "/v1/me/contributions"),
            ("GET", "/v1/me/contributions/missing/review"),
            ("POST", "/v1/me/contributions/missing/withdraw"),
        ] {
            let response = req(&h.app, method, path, Some(json!({})), "", "", token, ORIGIN).await;
            assert_eq!(response.status, 401, "{method} {path}");
            assert_eq!(response.data["code"], "auth_required");
        }
    }
    // Personal addresses need neither an invitation nor an administrator/domain allowlist.
    let (cookie, csrf, _) = h.login("Independent.Person@Gmail.Com").await;
    let copied = h
        .call(
            "POST",
            "/v1/templates/meeting.minutes.ko/copy",
            None,
            &cookie,
            &csrf,
        )
        .await;
    assert_eq!(copied.status, 200);
    let input = json!({"template_id":copied.data["id"],"author":"Individual member","license":"CC-BY-4.0","rights_confirmed":true});
    assert_eq!(
        h.call(
            "POST",
            "/v1/me/contributions",
            Some(input.clone()),
            &cookie,
            ""
        )
        .await
        .status,
        401
    );
    let contribution = h
        .call("POST", "/v1/me/contributions", Some(input), &cookie, &csrf)
        .await;
    assert_eq!(contribution.status, 200);
    assert_eq!(contribution.data["status"], "pending");
    let public_path = format!(
        "/v1/public/templates/{}",
        contribution.data["snapshot"]["id"].as_str().unwrap()
    );
    assert_eq!(
        req(&h.app, "GET", &public_path, None, "", "", "", "")
            .await
            .status,
        404
    );
    assert_eq!(
        h.call("POST", "/v1/auth/logout", None, &cookie, &csrf)
            .await
            .status,
        200
    );
    assert_eq!(
        h.call("GET", "/v1/me/contributions", None, &cookie, "")
            .await
            .status,
        401
    );
}

#[tokio::test]
async fn contribution_review_copy_attribution_withdrawal_and_private_boundary() {
    let h = Harness::new();
    let (alice, csrf, _) = h.login("alice@example.test").await;
    let (bob, bcsrf, _) = h.login("bob@example.test").await;
    let copied = h
        .call(
            "POST",
            "/v1/templates/meeting.minutes.ko/copy",
            None,
            &alice,
            &csrf,
        )
        .await;
    let tid = copied.data["id"].as_str().unwrap();
    let sub =
        json!({"template_id":tid,"author":"Alice","license":"CC-BY-4.0","rights_confirmed":true});
    assert_eq!(
        h.call(
            "POST",
            "/v1/me/contributions",
            Some(sub.clone()),
            &bob,
            &bcsrf
        )
        .await
        .status,
        404
    );
    let mut invalid = sub.clone();
    invalid["rights_confirmed"] = json!(false);
    assert_eq!(
        h.call("POST", "/v1/me/contributions", Some(invalid), &alice, &csrf)
            .await
            .status,
        400
    );
    let c = h
        .call(
            "POST",
            "/v1/me/contributions",
            Some(sub.clone()),
            &alice,
            &csrf,
        )
        .await;
    assert_eq!(c.data["status"], "pending");
    let cid = c.data["id"].as_str().unwrap();
    let public = c.data["snapshot"]["id"].as_str().unwrap();
    assert_ne!(public, tid);
    assert_eq!(
        h.call("POST", "/v1/me/contributions", Some(sub), &alice, &csrf)
            .await
            .status,
        409
    );
    assert!(
        h.call("GET", "/v1/me/contributions", None, &bob, "")
            .await
            .data["items"]
            .as_array()
            .unwrap()
            .is_empty()
    );
    assert_eq!(
        req(
            &h.app,
            "GET",
            &format!("/v1/public/templates/{public}"),
            None,
            "",
            "",
            "",
            ""
        )
        .await
        .status,
        404
    );
    let decision = format!("/v1/admin/contributions/{cid}/decision");
    assert_eq!(
        h.call(
            "POST",
            &decision,
            Some(json!({"decision":"approve"})),
            &alice,
            &csrf
        )
        .await
        .status,
        401
    );
    assert_eq!(
        req(
            &h.app,
            "POST",
            &decision,
            Some(json!({"decision":"approve"})),
            "",
            "",
            LOCAL,
            ORIGIN
        )
        .await
        .status,
        401
    );
    assert_eq!(
        req(
            &h.app,
            "POST",
            &decision,
            Some(json!({"decision":"approve"})),
            "",
            "",
            ADMIN,
            ORIGIN
        )
        .await
        .status,
        200
    );
    assert_eq!(
        req(
            &h.app,
            "POST",
            &decision,
            Some(json!({"decision":"approve"})),
            "",
            "",
            ADMIN,
            ORIGIN
        )
        .await
        .status,
        409
    );
    let published = req(
        &h.app,
        "GET",
        &format!("/v1/public/templates/{public}"),
        None,
        "",
        "",
        "",
        "",
    )
    .await;
    assert_eq!(published.status, 200);
    assert!(!published.raw.contains("alice@example.test"));
    assert!(!published.raw.contains(tid));
    let copy = h
        .call(
            "POST",
            &format!("/v1/templates/{public}/copy"),
            None,
            &bob,
            &bcsrf,
        )
        .await;
    assert_eq!(copy.data["visibility"], "private");
    assert_eq!(copy.data["origin"]["template_id"], public);
    let btid = copy.data["id"].as_str().unwrap();
    let bsub =
        json!({"template_id":btid,"author":"Bob","license":"CC0-1.0","rights_confirmed":true});
    assert_eq!(
        h.call(
            "POST",
            "/v1/me/contributions",
            Some(bsub.clone()),
            &bob,
            &bcsrf
        )
        .await
        .status,
        403
    );
    let mut bsub = bsub;
    bsub["license"] = json!("CC-BY-4.0");
    assert_eq!(
        h.call("POST", "/v1/me/contributions", Some(bsub), &bob, &bcsrf)
            .await
            .status,
        200
    );
    assert_eq!(
        h.call(
            "POST",
            &format!("/v1/me/contributions/{cid}/withdraw"),
            None,
            &bob,
            &bcsrf
        )
        .await
        .status,
        404
    );
    assert_eq!(
        h.call(
            "POST",
            &format!("/v1/me/contributions/{cid}/withdraw"),
            None,
            &alice,
            &csrf
        )
        .await
        .data["status"],
        "withdrawn"
    );
    assert_eq!(
        req(
            &h.app,
            "GET",
            &format!("/v1/public/templates/{public}"),
            None,
            "",
            "",
            "",
            ""
        )
        .await
        .status,
        404
    );
    assert_eq!(
        h.call("GET", &format!("/v1/templates/{btid}"), None, &bob, "")
            .await
            .data["origin"]["template_id"],
        public
    );
}

#[tokio::test]
async fn allowlisted_admin_session_can_review_contributions_with_csrf_and_origin() {
    let h = Harness::new();
    let (member_cookie, member_csrf, _) = h.login("contributor@example.test").await;
    let copied = h
        .call(
            "POST",
            "/v1/templates/meeting.minutes.ko/copy",
            None,
            &member_cookie,
            &member_csrf,
        )
        .await;
    assert_eq!(copied.status, 200);
    let contribution = h
        .call(
            "POST",
            "/v1/me/contributions",
            Some(json!({"template_id":copied.data["id"],"author":"Contributor","license":"CC-BY-4.0","rights_confirmed":true})),
            &member_cookie,
            &member_csrf,
        )
        .await;
    assert_eq!(contribution.status, 200);
    let contribution_id = contribution.data["id"].as_str().unwrap();
    let public_id = contribution.data["snapshot"]["id"].as_str().unwrap();

    let previous_link_count = h.mail.links.lock().unwrap().len();
    let unknown = h
        .call(
            "POST",
            "/v1/admin/auth/email/link",
            Some(json!({"email":"not-allowlisted@example.test"})),
            "",
            "",
        )
        .await;
    assert_eq!(unknown.status, 202);
    assert_eq!(unknown.data["accepted"], true);
    assert_eq!(h.mail.links.lock().unwrap().len(), previous_link_count);

    let requested = h
        .call(
            "POST",
            "/v1/admin/auth/email/link",
            Some(json!({"email":"operator@example.test"})),
            "",
            "",
        )
        .await;
    assert_eq!(requested.status, 202);
    assert_eq!(requested.data["accepted"], true);
    assert_eq!(unknown.data, requested.data);
    assert!(!requested.raw.contains("operator@example.test"));
    let token = captured_admin_link(&h);
    let consumed = h
        .call(
            "POST",
            "/v1/admin/auth/email/consume",
            Some(json!({"token":token.clone()})),
            "",
            "",
        )
        .await;
    assert_eq!(consumed.status, 200);
    assert!(consumed.cookies.starts_with("dmem_admin_session="));
    assert!(!consumed.cookies.contains("dmem_session="));
    assert!(!requested.raw.contains(&token));
    let admin_cookie = consumed.cookies.clone();
    let admin_csrf = consumed.data["csrf_token"].as_str().unwrap();
    let decision = format!("/v1/admin/contributions/{contribution_id}/decision");
    assert_eq!(
        h.call(
            "POST",
            "/v1/admin/auth/email/consume",
            Some(json!({"token":token})),
            "",
            "",
        )
        .await
        .status,
        401,
        "an administrator link can be consumed only once",
    );
    let session = req(
        &h.app,
        "GET",
        "/v1/admin/auth/session",
        None,
        &admin_cookie,
        "",
        "",
        "",
    )
    .await;
    assert_eq!(session.status, 200);
    assert_eq!(session.data["email"], "operator@example.test");

    for (cookie, bearer, origin, csrf) in [
        ("", "", ORIGIN, ""),
        (member_cookie.as_str(), "", ORIGIN, ""),
        ("", LOCAL, ORIGIN, ""),
    ] {
        assert_eq!(
            req(
                &h.app,
                "GET",
                "/v1/admin/contributions",
                None,
                cookie,
                csrf,
                bearer,
                origin,
            )
            .await
            .status,
            401
        );
    }
    let queue = req(
        &h.app,
        "GET",
        "/v1/admin/contributions",
        None,
        &admin_cookie,
        "",
        "",
        ORIGIN,
    )
    .await;
    assert_eq!(
        queue.status, 200,
        "admin email session must reach the queue"
    );
    assert!(
        queue.data["items"]
            .as_array()
            .unwrap()
            .iter()
            .any(|row| row["id"] == contribution_id)
    );
    assert_eq!(
        req(
            &h.app,
            "GET",
            "/v1/admin/contributions",
            None,
            &admin_cookie,
            "",
            "",
            "",
        )
        .await
        .status,
        200,
        "same-origin GET should not require an Origin header",
    );

    for (origin, csrf, bearer) in [
        (ORIGIN, "", ""),
        (ORIGIN, "wrong-csrf", ""),
        ("https://evil.test", admin_csrf, ""),
        ("", admin_csrf, ""),
        (ORIGIN, admin_csrf, LOCAL),
    ] {
        assert_eq!(
            req(
                &h.app,
                "POST",
                &decision,
                Some(json!({"decision":"approve"})),
                &admin_cookie,
                csrf,
                bearer,
                origin,
            )
            .await
            .status,
            401
        );
    }
    assert_eq!(
        h.call("GET", "/v1/me/contributions", None, &member_cookie, "",)
            .await
            .data["items"][0]["status"],
        "pending"
    );
    assert_eq!(
        req(
            &h.app,
            "GET",
            &format!("/v1/public/templates/{public_id}"),
            None,
            "",
            "",
            "",
            "",
        )
        .await
        .status,
        404
    );
    assert_eq!(
        h.call(
            "POST",
            &decision,
            Some(json!({"decision":"approve"})),
            &admin_cookie,
            admin_csrf,
        )
        .await
        .status,
        200
    );
    assert_eq!(
        h.call(
            "POST",
            &decision,
            Some(json!({"decision":"approve"})),
            &admin_cookie,
            admin_csrf,
        )
        .await
        .status,
        409
    );
    assert_eq!(
        req(
            &h.app,
            "GET",
            &format!("/v1/public/templates/{public_id}"),
            None,
            "",
            "",
            "",
            "",
        )
        .await
        .status,
        200
    );

    let reopened = Harness::router(&h.path, h.config.clone());
    assert_eq!(
        req(
            &reopened,
            "GET",
            "/v1/admin/contributions",
            None,
            &admin_cookie,
            "",
            "",
            "",
        )
        .await
        .status,
        200
    );
    let mut revoked = h.config.clone();
    revoked.set_admin_emails("").unwrap();
    let revoked_app = Harness::router(&h.path, revoked);
    assert_eq!(
        req(
            &revoked_app,
            "GET",
            "/v1/admin/contributions",
            None,
            &admin_cookie,
            "",
            "",
            ORIGIN,
        )
        .await
        .status,
        401
    );
}
