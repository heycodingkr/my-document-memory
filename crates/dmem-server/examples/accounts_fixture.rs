//! Synthetic email capture for real browser tests; never loaded by the production binary.
use dmem_server::{AuthConfig, Delivery, EmailSender, Store, router_with_auth};
use std::{path::PathBuf, sync::Arc};
struct Mailbox(PathBuf);
impl EmailSender for Mailbox {
    fn send_link(&self, email: String, url: String, _: String) -> Delivery {
        let path = self.0.clone();
        Box::pin(async move {
            if !email.ends_with("@example.test") {
                return Err(dmem_contracts::Fault::InvalidInput);
            }
            std::fs::write(
                path,
                serde_json::json!({"email":email,"url":url}).to_string(),
            )
            .map_err(|_| dmem_contracts::Fault::Internal)?;
            Ok(())
        })
    }
    fn send_code(&self, email: String, code: String, _: String) -> Delivery {
        let path = self.0.clone();
        Box::pin(async move {
            if !email.ends_with("@example.test") {
                return Err(dmem_contracts::Fault::InvalidInput);
            }
            std::fs::write(
                path,
                serde_json::json!({"email":email,"code":code}).to_string(),
            )
            .map_err(|_| dmem_contracts::Fault::Internal)?;
            Ok(())
        })
    }
}
#[tokio::main]
async fn main() {
    let addr = std::env::var("DMEM_E2E_ADDR")
        .expect("isolated loopback address")
        .parse::<std::net::SocketAddr>()
        .unwrap();
    assert!(addr.ip().is_loopback());
    let mut config = AuthConfig::new(
        "synthetic-e2e-secret-at-least-32-characters".into(),
        Arc::new(Mailbox(std::env::var("DMEM_E2E_MAILBOX").unwrap().into())),
    )
    .unwrap();
    config.admin_token = Some("synthetic-e2e-admin-token-at-least-32-characters".into());
    config
        .set_admin_emails(
            "reviewer@example.test,reviewer-blocked@example.test,reviewer-cross@example.test,reviewer-queue@example.test",
        )
        .unwrap();
    let db = std::env::var("DMEM_E2E_DATABASE").unwrap();
    let web = std::env::var("DMEM_E2E_WEB_DIR").unwrap();
    let store = Arc::new(Store::open(&db).unwrap());
    let connection = rusqlite::Connection::open(&db).unwrap();
    for owner in ["local", "bob"] {
        connection
            .execute(
                "INSERT OR IGNORE INTO accounts(id,email,created_at) VALUES(?1,?2,1)",
                rusqlite::params![owner, format!("fixture-{owner}@example.test")],
            )
            .unwrap();
    }
    drop(connection);
    let app = router_with_auth(
        store,
        vec![
            (
                "automated-smoke-token-not-production".into(),
                "local".into(),
            ),
            ("automated-bob-token-not-production".into(), "bob".into()),
        ],
        vec![format!("http://{addr}")],
        Some(web.into()),
        config,
    )
    .unwrap();
    axum::serve(tokio::net::TcpListener::bind(addr).await.unwrap(), app)
        .await
        .unwrap();
}
