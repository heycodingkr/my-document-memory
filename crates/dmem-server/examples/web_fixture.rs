//! Explicit isolated service composition for web/MCP/browser acceptance tests.
use dmem_server::{AuthConfig, Store, WebConfig, router_with_services};
use std::{net::SocketAddr, path::PathBuf, sync::Arc};
#[tokio::main]
async fn main() {
    let addr: SocketAddr = std::env::var("DMEM_ADDR")
        .expect("test address")
        .parse()
        .unwrap();
    assert!(addr.ip().is_loopback());
    let remote: SocketAddr = std::env::var("DMEM_FIXTURE_ADDR")
        .expect("one fixture address")
        .parse()
        .unwrap();
    assert!(remote.ip().is_loopback());
    let mut web = WebConfig::isolated_fixture(remote);
    web.capture_secret = std::env::var("DMEM_CAPTURE_SECRET").ok();
    let token = std::env::var("DMEM_TOKEN").expect("test token");
    let app = router_with_services(
        Arc::new(Store::open(std::env::var("DMEM_DATABASE").unwrap()).unwrap()),
        vec![
            (token, "local".into()),
            ("synthetic-web-bob-token-at-least-32".into(), "bob".into()),
        ],
        vec![format!("http://{addr}")],
        Some(PathBuf::from(std::env::var("DMEM_WEB_DIR").unwrap())),
        AuthConfig::default(),
        web,
    )
    .unwrap();
    axum::serve(tokio::net::TcpListener::bind(addr).await.unwrap(), app)
        .await
        .unwrap();
}
