use axum::{
    Router,
    body::Body,
    http::{Request, StatusCode},
};
use dmem_server::{AuthConfig, Delivery, EmailSender, Store, router_with_auth};
use http_body_util::BodyExt;
use serde_json::{Value, json};
use std::sync::{Arc, Mutex};
use tower::ServiceExt;
const ORIGIN: &str = "http://localhost:5174";
const LOCAL: &str = "synthetic-local-token";
const ADMIN: &str = "synthetic-leaderboard-admin-at-least-32-chars";
#[derive(Default)]
struct Mail(Mutex<Vec<String>>);
impl EmailSender for Mail {
    fn send_code(&self, _: String, code: String, _: String) -> Delivery {
        self.0.lock().unwrap().push(code);
        Box::pin(async { Ok(()) })
    }
}
struct User {
    cookie: String,
    csrf: String,
    id: String,
    email: String,
}
struct Reply {
    status: StatusCode,
    value: Value,
    cookies: String,
    raw: String,
}
async fn request(
    app: &Router,
    method: &str,
    path: &str,
    input: Option<Value>,
    cookie: &str,
    csrf: &str,
    token: &str,
    origin: &str,
) -> Reply {
    let mut b = Request::builder()
        .method(method)
        .uri(path)
        .header("Content-Type", "application/json");
    if !cookie.is_empty() {
        b = b.header("Cookie", cookie)
    }
    if !csrf.is_empty() {
        b = b.header("X-CSRF-Token", csrf)
    }
    if !token.is_empty() {
        b = b.header("Authorization", format!("Bearer {token}"))
    }
    if !origin.is_empty() {
        b = b.header("Origin", origin)
    }
    let res = app
        .clone()
        .oneshot(
            b.body(input.map_or(Body::empty(), |v| Body::from(v.to_string())))
                .unwrap(),
        )
        .await
        .unwrap();
    let status = res.status();
    let cookies = res
        .headers()
        .get_all("set-cookie")
        .iter()
        .map(|v| v.to_str().unwrap().split(';').next().unwrap().to_owned())
        .collect::<Vec<_>>()
        .join("; ");
    let raw =
        String::from_utf8(res.into_body().collect().await.unwrap().to_bytes().to_vec()).unwrap();
    let value = serde_json::from_str(&raw).unwrap();
    Reply {
        status,
        value,
        cookies,
        raw,
    }
}
struct Harness {
    app: Router,
    path: std::path::PathBuf,
    _dir: tempfile::TempDir,
    mail: Arc<Mail>,
    config: AuthConfig,
}
impl Harness {
    fn new() -> Self {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("rank.sqlite3");
        let mail = Arc::new(Mail::default());
        let mut config = AuthConfig::new(
            "synthetic-member-secret-at-least-32-chars".into(),
            mail.clone(),
        )
        .unwrap();
        config.admin_token = Some(ADMIN.into());
        let app = Self::open(&path, config.clone());
        Self {
            app,
            path,
            _dir: dir,
            mail,
            config,
        }
    }
    fn open(path: &std::path::Path, config: AuthConfig) -> Router {
        router_with_auth(
            Arc::new(Store::open(path).unwrap()),
            vec![(LOCAL.into(), "local".into())],
            vec![ORIGIN.into()],
            None,
            config,
        )
        .unwrap()
    }
    async fn call(
        &self,
        method: &str,
        path: &str,
        input: Option<Value>,
        u: Option<&User>,
    ) -> Reply {
        request(
            &self.app,
            method,
            path,
            input,
            u.map_or("", |u| &u.cookie),
            u.map_or("", |u| &u.csrf),
            "",
            ORIGIN,
        )
        .await
    }
    async fn user(&self, email: &str) -> User {
        let s = self
            .call(
                "POST",
                "/v1/auth/email/start",
                Some(json!({"email":email})),
                None,
            )
            .await;
        assert_eq!(s.status, 202);
        let code = self.mail.0.lock().unwrap().last().unwrap().clone();
        let v = request(
            &self.app,
            "POST",
            "/v1/auth/email/verify",
            Some(json!({"code":code})),
            &s.cookies,
            "",
            "",
            ORIGIN,
        )
        .await;
        assert_eq!(v.status, 200);
        User {
            cookie: v.cookies,
            csrf: v.value["csrf_token"].as_str().unwrap().into(),
            id: v.value["account"]["id"].as_str().unwrap().into(),
            email: email.into(),
        }
    }
    async fn profile(&self, u: &User) -> Value {
        let r = self.call("GET", "/v1/me/profile", None, Some(u)).await;
        assert_eq!(r.status, 200);
        r.value
    }
    async fn show(&self, u: &User, handle: &str, public: bool) -> Value {
        let r = self
            .call(
                "PUT",
                "/v1/me/profile",
                Some(json!({"handle":handle,"public_profile":public})),
                Some(u),
            )
            .await;
        assert_eq!(r.status, 200, "{}", r.raw);
        r.value
    }
    async fn contribution(&self, u: &User, n: u32) -> Value {
        let t=self.call("POST","/v1/templates",Some(json!({"title":format!("Research outline {n}"),"summary":format!("Original research planning structure {n}"),"form":{"provider":"docx","doc_type":"report","locale":"en-US"},"sections":[format!("Research background {n}"),format!("Experiment protocol {n}"),format!("Review decisions {n}")],"tags":[]})),Some(u)).await;
        assert_eq!(t.status, 200);
        let c=self.call("POST","/v1/me/contributions",Some(json!({"template_id":t.value["id"],"author":"Synthetic researcher","license":"CC-BY-4.0","rights_confirmed":true})),Some(u)).await;
        assert_eq!(c.status, 200);
        c.value
    }
    async fn decide(&self, id: &str, decision: &str) -> Reply {
        request(
            &self.app,
            "POST",
            &format!("/v1/admin/contributions/{id}/decision"),
            Some(json!({"decision":decision})),
            "",
            "",
            ADMIN,
            ORIGIN,
        )
        .await
    }
    async fn approved(&self, u: &User, n: u32) -> Value {
        let c = self.contribution(u, n).await;
        let r = self.decide(c["id"].as_str().unwrap(), "approve").await;
        assert_eq!(r.status, 200, "{}", r.raw);
        c
    }
    async fn board(&self) -> Value {
        let r = self.call("GET", "/v1/leaderboard", None, None).await;
        assert_eq!(r.status, 200);
        r.value
    }
}
#[tokio::test]
async fn anonymous_leaderboard_starts_empty() {
    let h = Harness::new();
    let r = h.board().await;
    assert_eq!(r["items"], json!([]));
    assert_eq!(r["total"], 0);
    assert_eq!(r["points_per_approval"], 20);
}
#[tokio::test]
async fn profiles_are_private_by_default_validated_atomic_and_persistent() {
    let h = Harness::new();
    let a = h.user("private-alice@example.test").await;
    let b = h.user("private-bob@example.test").await;
    let p = h.profile(&a).await;
    assert_eq!(p["handle"], Value::Null);
    assert_eq!(p["public_profile"], false);
    assert_eq!(p["total_points"], 0);
    assert_eq!(p["overall_rank"], Value::Null);
    let db = rusqlite::Connection::open(&h.path).unwrap();
    assert_eq!(
        db.query_row("SELECT COUNT(*) FROM account_profiles", [], |r| r
            .get::<_, u32>(0))
            .unwrap(),
        0
    );
    let p = h.show(&a, " Alice-One ", true).await;
    assert_eq!(p["handle"], "alice-one");
    assert_eq!(
        h.call("GET", "/v1/profiles/alice-one", None, None)
            .await
            .status,
        200
    );
    assert_eq!(
        h.board().await["total"],
        0,
        "zero-point profiles do not fill the board"
    );
    for handle in [
        "ab",
        "-edge",
        "edge-",
        "a@b",
        "a/b",
        "あいう",
        "abcdefghijklmnopqrstuvwxyz",
    ] {
        assert_eq!(
            h.call(
                "PUT",
                "/v1/me/profile",
                Some(json!({"handle":handle,"public_profile":true})),
                Some(&a)
            )
            .await
            .status,
            400
        )
    }
    for handle in ["admin", "Support", "leaderboard"] {
        let r = h
            .call(
                "PUT",
                "/v1/me/profile",
                Some(json!({"handle":handle,"public_profile":true})),
                Some(&a),
            )
            .await;
        assert_eq!(r.status, 409);
        assert_eq!(r.value["code"], "handle_unavailable")
    }
    let r = h
        .call(
            "PUT",
            "/v1/me/profile",
            Some(json!({"handle":"ALICE-ONE","public_profile":false})),
            Some(&b),
        )
        .await;
    assert_eq!(r.status, 409);
    assert_eq!(h.profile(&a).await["handle"], "alice-one");
    assert_eq!(h.profile(&b).await["handle"], Value::Null);
    let reopened = Harness::open(&h.path, h.config.clone());
    let r = request(
        &reopened,
        "GET",
        "/v1/me/profile",
        None,
        &a.cookie,
        "",
        "",
        ORIGIN,
    )
    .await;
    assert_eq!(r.value["handle"], "alice-one");
    let r = h
        .call(
            "PUT",
            "/v1/me/profile",
            Some(json!({"handle":null,"public_profile":true})),
            Some(&a),
        )
        .await;
    assert_eq!(r.status, 400);
    let r = h
        .call(
            "PUT",
            "/v1/me/profile",
            Some(json!({"handle":null,"public_profile":false})),
            Some(&a),
        )
        .await;
    assert_eq!(r.status, 200);
    assert_eq!(
        h.call("GET", "/v1/profiles/alice-one", None, None)
            .await
            .status,
        404
    );
}
#[tokio::test]
async fn profile_writes_require_verified_account_origin_and_csrf() {
    let h = Harness::new();
    let a = h.user("security@example.test").await;
    let input = json!({"handle":"safe-handle","public_profile":true});
    assert_eq!(
        h.call("GET", "/v1/me/profile", None, None).await.status,
        401
    );
    for method in ["GET", "PUT"] {
        assert_eq!(
            request(
                &h.app,
                method,
                "/v1/me/profile",
                if method == "PUT" {
                    Some(input.clone())
                } else {
                    None
                },
                "",
                "",
                LOCAL,
                ORIGIN
            )
            .await
            .status,
            401
        )
    }
    for origin in ["", "https://foreign.example.test"] {
        assert_eq!(
            request(
                &h.app,
                "PUT",
                "/v1/me/profile",
                Some(input.clone()),
                &a.cookie,
                &a.csrf,
                "",
                origin
            )
            .await
            .status,
            401
        )
    }
    assert_eq!(
        request(
            &h.app,
            "PUT",
            "/v1/me/profile",
            Some(input.clone()),
            &a.cookie,
            "",
            "",
            ORIGIN
        )
        .await
        .status,
        401
    );
    for field in ["owner", "account_id", "points"] {
        let mut forged = input.clone();
        forged[field] = json!("forged");
        assert_eq!(
            h.call("PUT", "/v1/me/profile", Some(forged), Some(&a))
                .await
                .status,
            400
        )
    }
    assert_eq!(h.profile(&a).await["handle"], Value::Null);
}
#[tokio::test]
async fn concurrent_handle_claims_have_one_winner() {
    let h = Harness::new();
    let a = h.user("claim-a@example.test").await;
    let b = h.user("claim-b@example.test").await;
    let input = Some(json!({"handle":"same-handle","public_profile":true}));
    let (x, y) = tokio::join!(
        h.call("PUT", "/v1/me/profile", input.clone(), Some(&a)),
        h.call("PUT", "/v1/me/profile", input, Some(&b))
    );
    let mut statuses = [x.status.as_u16(), y.status.as_u16()];
    statuses.sort();
    assert_eq!(statuses, [200, 409]);
}
#[tokio::test]
async fn only_active_approvals_score_and_private_rank_never_leaks() {
    let h = Harness::new();
    let a = h.user("score-alice@example.test").await;
    let b = h.user("score-bob@example.test").await;
    h.show(&a, "hidden-alice", false).await;
    h.show(&b, "public-bob", true).await;
    let pending = h.contribution(&a, 10).await;
    assert_eq!(h.profile(&a).await["total_points"], 0);
    assert_eq!(
        h.decide(pending["id"].as_str().unwrap(), "reject")
            .await
            .status,
        200
    );
    assert_eq!(h.profile(&a).await["total_points"], 0);
    let first = h.approved(&a, 11).await;
    h.approved(&a, 12).await;
    let bob = h.approved(&b, 13).await;
    assert_eq!(h.profile(&a).await["total_points"], 40);
    assert_eq!(h.profile(&b).await["total_points"], 20);
    assert_eq!(h.profile(&b).await["overall_rank"], 2);
    assert_eq!(h.profile(&b).await["public_rank"], 1);
    let board = h.board().await;
    assert_eq!(board["total"], 1);
    assert_eq!(board["items"][0]["handle"], "public-bob");
    assert_eq!(board["items"][0]["rank"], 1);
    assert_eq!(
        h.call("GET", "/v1/profiles/hidden-alice", None, None)
            .await
            .status,
        404
    );
    assert_eq!(
        h.decide(first["id"].as_str().unwrap(), "approve")
            .await
            .status,
        409
    );
    assert_eq!(h.profile(&a).await["total_points"], 40);
    let public = h.call("GET", "/v1/profiles/PUBLIC-BOB", None, None).await;
    assert_eq!(public.status, 200);
    assert_eq!(public.value["templates"].as_array().unwrap().len(), 1);
    for secret in [
        &a.email,
        &a.id,
        &b.email,
        &b.id,
        bob["template_id"].as_str().unwrap(),
    ] {
        assert!(!public.raw.contains(secret));
        assert!(!board.to_string().contains(secret));
    }
    let id = first["id"].as_str().unwrap();
    assert_eq!(
        h.call(
            "POST",
            &format!("/v1/me/contributions/{id}/withdraw"),
            None,
            Some(&a)
        )
        .await
        .status,
        200
    );
    assert_eq!(h.profile(&a).await["total_points"], 20);
    h.show(&b, "public-bob", false).await;
    assert_eq!(h.board().await["total"], 0);
    assert_eq!(
        h.call("GET", "/v1/profiles/public-bob", None, None)
            .await
            .status,
        404
    );
    let reopened = Harness::open(&h.path, h.config.clone());
    let r = request(
        &reopened,
        "GET",
        "/v1/me/profile",
        None,
        &a.cookie,
        "",
        "",
        ORIGIN,
    )
    .await;
    assert_eq!(r.value["total_points"], 20);
}
#[tokio::test]
async fn ties_and_pagination_rank_before_limiting() {
    let h = Harness::new();
    let mut users = Vec::new();
    for i in 0..21 {
        let u = h.user(&format!("page-{i}@example.test")).await;
        h.show(&u, &format!("member-{i:02}"), true).await;
        h.approved(&u, 100 + i).await;
        users.push(u);
    }
    let first = h.board().await;
    assert_eq!(first["total"], 21);
    assert_eq!(first["items"].as_array().unwrap().len(), 20);
    assert_eq!(first["next_offset"], 20);
    assert_eq!(first["items"][0]["handle"], "member-00");
    assert!(
        first["items"]
            .as_array()
            .unwrap()
            .iter()
            .all(|x| x["rank"] == 1)
    );
    let second = h.call("GET", "/v1/leaderboard?offset=20", None, None).await;
    assert_eq!(second.value["items"].as_array().unwrap().len(), 1);
    assert_eq!(second.value["items"][0]["rank"], 1);
    assert_eq!(second.value["items"][0]["handle"], "member-20");
    assert!(second.value["next_offset"].is_null());
    h.approved(&users[20], 999).await;
    let board = h.board().await;
    assert_eq!(board["items"][0]["handle"], "member-20");
    assert_eq!(board["items"][0]["rank"], 1);
    assert_eq!(board["items"][1]["rank"], 2);
    for query in ["offset=-1", "offset=no", "offset=10001", "extra=1"] {
        assert_eq!(
            h.call("GET", &format!("/v1/leaderboard?{query}"), None, None)
                .await
                .status,
            400
        )
    }
    assert_eq!(
        h.call("GET", "/v1/profiles/does-not-exist", None, None)
            .await
            .status,
        404
    );
}
