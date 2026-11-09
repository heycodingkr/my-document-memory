use dmem_server::{AuthConfig, ResendEmailSender, Store, WebConfig, router_with_services};
use std::{path::PathBuf, sync::Arc};
#[tokio::main]
async fn main() {
    if let Err(e) = start().await {
        eprintln!("dmem-server: {e}");
        std::process::exit(1)
    }
}
async fn start() -> Result<(), Box<dyn std::error::Error>> {
    let token = std::env::var("DMEM_TOKEN")
        .map_err(|_| "DMEM_TOKEN is required (at least 16 characters).")?;
    if token.len() < 16 {
        return Err("DMEM_TOKEN must contain at least 16 characters.".into());
    }
    let addr = std::env::var("DMEM_ADDR")
        .unwrap_or_else(|_| "127.0.0.1:3847".into())
        .parse::<std::net::SocketAddr>()?;
    if !addr.ip().is_loopback() {
        return Err("Local runtime must bind to a loopback address.".into());
    }
    let path = std::env::var("DMEM_DATABASE").unwrap_or_else(|_| "data/dmem.sqlite3".into());
    if let Some(parent) = std::path::Path::new(&path)
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
    {
        std::fs::create_dir_all(parent)?
    }
    let store = Arc::new(Store::open(path)?);
    let origins = vec![
        std::env::var("DMEM_WEB_ORIGIN").unwrap_or_else(|_| "http://127.0.0.1:5174".into()),
        format!("http://{addr}"),
    ];
    let web = Some(PathBuf::from(
        std::env::var("DMEM_WEB_DIR").unwrap_or_else(|_| "web/dist".into()),
    ));
    let secret_file = |name: &str, path: &str| -> Result<Option<String>, std::io::Error> {
        if let Ok(value) = std::env::var(name) {
            return Ok(Some(value));
        }
        match std::fs::read_to_string(path) {
            Ok(v) => Ok(Some(v.trim().to_string())),
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(None),
            Err(e) => Err(e),
        }
    };
    let key = secret_file("DMEM_RESEND_API_KEY", "credentials/resend-api-key")?;
    let mut auth = if let Some(key) = key {
        let secret = secret_file("DMEM_AUTH_SECRET", "credentials/auth-secret")?
            .ok_or("DMEM_AUTH_SECRET or credentials/auth-secret is required for email login")?;
        let from = std::env::var("DMEM_EMAIL_FROM")
            .unwrap_or_else(|_| "My Document Memory <help@mydocumentmemory.com>".into());
        AuthConfig::new(secret, Arc::new(ResendEmailSender::new(key, from)?))?
    } else {
        AuthConfig::default()
    };
    auth.secure_cookies = origins[0].starts_with("https://");
    auth.admin_token = secret_file("DMEM_ADMIN_TOKEN", "credentials/admin-token")?;
    auth.set_admin_emails(&std::env::var("DMEM_ADMIN_EMAILS").unwrap_or_default())?;
    let app = router_with_services(store, vec![(token, "local".into())], origins, web, auth, WebConfig::from_env()?)?;
    let listener = tokio::net::TcpListener::bind(addr).await?;
    eprintln!("My Document Memory API: http://{addr}");
    axum::serve(listener, app)
        .with_graceful_shutdown(async {
            let _ = tokio::signal::ctrl_c().await;
        })
        .await?;
    Ok(())
}
