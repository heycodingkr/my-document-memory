use axum::{Router, body::Body, http::Request};
use dmem_server::{AuthConfig, Store, router_with_auth};
use http_body_util::BodyExt;
use rusqlite::{Connection, params};
use serde_json::{Value, json};
use std::{path::PathBuf, sync::Arc};
use tower::ServiceExt;

const ALICE: &str = "synthetic-queue-alice-token";
const ADMIN: &str = "synthetic-queue-administrator-at-least-32-characters";
const ORIGIN: &str = "http://localhost:5174";
const QUEUE: &str = "/v1/admin/contributions";

struct Fixture {
    _dir: tempfile::TempDir,
    path: PathBuf,
    app: Router,
}

async fn call(app: &Router, method: &str, path: &str, token: &str, input: Option<Value>) -> (u16, Value) {
    let mut request = Request::builder().method(method).uri(path).header("Origin", ORIGIN);
    if !token.is_empty() {
        request = request.header("Authorization", format!("Bearer {token}"));
    }
    let response = app.clone().oneshot(request.header("Content-Type", "application/json")
        .body(input.map_or(Body::empty(), |v| Body::from(v.to_string()))).unwrap()).await.unwrap();
    let status = response.status().as_u16();
    let value = serde_json::from_slice(&response.into_body().collect().await.unwrap().to_bytes()).unwrap();
    (status, value)
}

impl Fixture {
    async fn new(pending: usize, rejected: usize) -> Self {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("queue.sqlite3");
        let store = Arc::new(Store::open(&path).unwrap());
        let mut auth = AuthConfig::default();
        auth.admin_token = Some(ADMIN.into());
        let app = router_with_auth(store, vec![(ALICE.into(), "alice".into())], vec![ORIGIN.into()], None, auth).unwrap();
        let (status, base) = call(&app, "POST", "/v1/templates", ALICE, Some(json!({
            "title":"Synthetic queue fixture", "summary":"A synthetic review structure",
            "form":{"provider":"docx","doc_type":"report","locale":"en-US"},
            "sections":["Queue assumptions","Queue verification"],"tags":[]
        }))).await;
        assert_eq!(status, 200, "{base}");
        let mut db = Connection::open(&path).unwrap();
        let tx = db.transaction().unwrap();
        // The withdrawal actor models a member-linked credential.
        tx.execute("INSERT OR IGNORE INTO accounts(id,email,created_at) VALUES('alice','queue-member@example.test',1)", []).unwrap();
        for (state, count, start) in [("pending", pending, 1000), ("rejected", rejected, 2000)] {
            for i in 0..count {
                let suffix = format!("{:032x}", start * 10000 + i);
                let template_id = format!("tpl_{suffix}");
                let mut private = base.clone();
                private["id"] = json!(template_id);
                private["title"] = json!(format!("Queue {state} {i:04}"));
                tx.execute("INSERT INTO records(id,owner,kind,version,payload,updated_at) VALUES(?1,'alice','template',1,?2,?3)",
                    params![template_id, private.to_string(), start + i / 7]).unwrap();
                let mut snapshot = private;
                snapshot["id"] = json!(format!("public_{suffix}"));
                snapshot["visibility"] = json!("public");
                snapshot["author"] = json!("Synthetic queue author");
                snapshot["license"] = json!("CC-BY-4.0");
                tx.execute("INSERT INTO contributions(id,owner,template_id,status,snapshot,public_id,created_at,updated_at) VALUES(?1,'alice',?2,?3,?4,NULL,?5,?5)",
                    params![format!("contrib_{suffix}"), template_id, state, snapshot.to_string(), start + i / 7]).unwrap();
            }
        }
        tx.commit().unwrap();
        Self { _dir: dir, path, app }
    }

    fn expected(&self, status: &str) -> Vec<String> {
        // Independent SQL oracle: no cursor/limit logic from the production implementation.
        let db = Connection::open(&self.path).unwrap();
        let sql = if status == "all" {
            "SELECT id FROM contributions ORDER BY created_at DESC,id ASC"
        } else {
            "SELECT id FROM contributions WHERE status=?1 ORDER BY created_at DESC,id ASC"
        };
        let mut stmt = db.prepare(sql).unwrap();
        let args: Vec<&str> = if status == "all" { vec![] } else { vec![status] };
        stmt.query_map(rusqlite::params_from_iter(args), |r| r.get(0)).unwrap().collect::<Result<_, _>>().unwrap()
    }

    async fn page(&self, query: &str) -> Value {
        let (status, value) = call(&self.app, "GET", &format!("{QUEUE}{query}"), ADMIN, None).await;
        assert_eq!(status, 200, "{value}");
        value
    }
}

fn ids(page: &Value) -> Vec<String> {
    page["items"].as_array().unwrap().iter().map(|v| v["id"].as_str().unwrap().to_string()).collect()
}

#[tokio::test]
async fn pending_filter_precedes_the_hundred_record_limit() {
    let f = Fixture::new(1, 120).await;
    let page = f.page("?status=pending").await;
    assert_eq!(ids(&page), f.expected("pending"), "older pending contribution must remain discoverable");
    assert!(page.get("next_cursor").unwrap().is_null());
}

#[tokio::test]
async fn keyset_pages_match_independent_order_with_tied_timestamps() {
    let f = Fixture::new(121, 120).await;
    let mut cursor = None;
    let mut actual = Vec::new();
    let mut sizes = Vec::new();
    loop {
        let mut query = "?status=pending&limit=25".to_string();
        if let Some(value) = cursor { query.push_str(&format!("&cursor={value}")); }
        let page = f.page(&query).await;
        let page_ids = ids(&page);
        assert!(!page_ids.is_empty());
        assert!(page["items"].as_array().unwrap().iter().all(|v| v["status"] == "pending"));
        sizes.push(page_ids.len());
        actual.extend(page_ids);
        cursor = page["next_cursor"].as_str().map(str::to_owned);
        if cursor.is_none() { break; }
        assert!(sizes.len() <= 6, "pagination must terminate");
    }
    assert_eq!(actual, f.expected("pending"));
    assert_eq!(sizes, [25, 25, 25, 25, 21]);
}

#[tokio::test]
async fn decision_and_withdrawal_do_not_invalidate_the_cursor_anchor() {
    let f = Fixture::new(9, 0).await;
    for (method_path, token, input) in [
        ("decision", ADMIN, Some(json!({"decision":"reject"}))),
        ("withdraw", ALICE, None),
    ] {
        let first = f.page("?status=pending&limit=3").await;
        let first_ids = ids(&first);
        let anchor = first_ids.last().unwrap();
        let path = if method_path == "decision" {
            format!("{QUEUE}/{anchor}/decision")
        } else {
            format!("/v1/me/contributions/{anchor}/withdraw")
        };
        let (status, _) = call(&f.app, "POST", &path, token, input).await;
        assert_eq!(status, 200);
        let query = format!("?status=pending&limit=100&cursor={}", first["next_cursor"].as_str().unwrap());
        let next = f.page(&query).await;
        let expected: Vec<_> = f.expected("pending").into_iter().filter(|id| !first_ids.contains(id)).collect();
        assert_eq!(ids(&next), expected);
    }
}

#[tokio::test]
async fn default_and_status_views_remain_bounded_and_compatible() {
    let f = Fixture::new(121, 120).await;
    let default = f.page("").await;
    assert_eq!(ids(&default), f.expected("all")[..100]);
    assert!(default["next_cursor"].is_string());
    for status in ["all", "pending", "rejected", "approved", "withdrawn"] {
        let page = f.page(&format!("?status={status}&limit=1")).await;
        let expected = f.expected(status);
        assert_eq!(ids(&page), expected.iter().take(1).cloned().collect::<Vec<_>>());
        assert_eq!(page["next_cursor"].is_string(), expected.len() > 1);
    }
}

#[tokio::test]
async fn invalid_queue_queries_are_rejected_after_administrator_authentication() {
    let f = Fixture::new(3, 0).await;
    let page = f.page("?status=pending&limit=1").await;
    let cursor = page["next_cursor"].as_str().unwrap();
    let mut queries: Vec<String> = [
        "?status=unknown", "?limit=0", "?limit=101", "?limit=-1", "?limit=no",
        "?limit=1&limit=2", "?status=pending&status=all", "?unknown=true",
        "?cursor=", "?cursor=garbage", "?status=pending&cursor=v1:pending:999999999999999999999999:contrib_x",
        "?status=pending&cursor=v1:pending:1:..",
        "?status=pending&cursor=v2:pending:1:contrib_x",
    ].iter().map(|s| s.to_string()).collect();
    queries.push(format!("?status=all&cursor={cursor}"));
    queries.push(format!("?status=pending&cursor={}", "x".repeat(200)));
    for query in queries {
        for (token, expected) in [(ADMIN, 400), (ALICE, 401), ("", 401)] {
            let (status, error) = call(&f.app, "GET", &format!("{QUEUE}{query}"), token, None).await;
            assert_eq!(status, expected, "query {query}: {error}");
            assert_eq!(error["code"], if expected == 400 { "invalid_input" } else { "auth_required" });
        }
    }
}
