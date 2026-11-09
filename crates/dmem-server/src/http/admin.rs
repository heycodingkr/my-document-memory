use super::account::{cookie, origin};
use super::*;
use crate::{
    administrator::{LINK_SECONDS, SESSION_SECONDS, csrf},
    identity::{constant_eq, normalize_email, secret},
};
use axum::http::HeaderMap;
use serde::Deserialize;

pub(super) fn routes() -> Router<App> {
    Router::new()
        .route("/admin/auth/config", get(config))
        .route("/admin/auth/email/link", axum::routing::post(start_link))
        .route(
            "/admin/auth/email/consume",
            axum::routing::post(consume_link),
        )
        .route("/admin/auth/session", get(session))
        .route("/admin/auth/logout", axum::routing::post(logout))
        .layer(DefaultBodyLimit::max(16 * 1024))
}
fn session_identity(s: &App, headers: &HeaderMap) -> Result<(String, String, u64), HttpError> {
    let token = cookie(headers, "dmem_admin_session").ok_or(HttpError(Fault::AuthRequired))?;
    let (email, expires) = s.store.admin_session(&s.auth, &token)?;
    Ok((email, token, expires))
}
fn verify_csrf(s: &App, headers: &HeaderMap, token: &str) -> Result<(), HttpError> {
    let mut values = headers.get_all("x-csrf-token").iter();
    let supplied = values.next().and_then(|v| v.to_str().ok()).unwrap_or("");
    if values.next().is_some() || !constant_eq(supplied, &csrf(&s.auth, token)) {
        return Err(Fault::AuthRequired.into());
    }
    Ok(())
}
pub(super) fn authorize(s: &App, headers: &HeaderMap, write: bool) -> Result<String, HttpError> {
    if write || headers.contains_key(header::ORIGIN) {
        origin(s, headers)?;
    }
    if headers.contains_key(header::AUTHORIZATION) {
        let mut values = headers.get_all(header::AUTHORIZATION).iter();
        let token = values
            .next()
            .and_then(|v| v.to_str().ok())
            .and_then(|v| v.strip_prefix("Bearer "))
            .unwrap_or("");
        if values.next().is_some()
            || !s
                .auth
                .admin_token
                .as_ref()
                .is_some_and(|expected| constant_eq(expected, token))
        {
            return Err(Fault::AuthRequired.into());
        }
        return Ok("operator-token".into());
    }
    let (email, token, _) = session_identity(s, headers)?;
    if write {
        verify_csrf(s, headers, &token)?;
    }
    Ok(format!(
        "admin:{}",
        s.auth.digest(&format!("admin-actor:{email}"))
    ))
}
async fn config(State(s): State<App>) -> Json<serde_json::Value> {
    Json(serde_json::json!({"enabled":s.auth.mailer.is_some() && !s.auth.admin_emails.is_empty()}))
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Start {
    email: String,
}
async fn start_link(
    State(s): State<App>,
    headers: HeaderMap,
    input: Result<Json<Start>, JsonRejection>,
) -> Result<Response, HttpError> {
    origin(&s, &headers)?;
    let email = normalize_email(&body(input)?.email)?;
    if let Some(mailer) = s
        .auth
        .mailer
        .clone()
        .filter(|_| s.auth.admin_emails.contains(&email))
    {
        let challenge = secret();
        let verifier = secret();
        let (auth, address, c, v) = (
            s.auth.clone(),
            email.clone(),
            challenge.clone(),
            verifier.clone(),
        );
        let created = run(s.clone(), move |db| {
            db.begin_admin_link(&auth, &address, &c, &v)
        })
        .await?;
        if created {
            let mut url = reqwest::Url::parse(
                headers
                    .get(header::ORIGIN)
                    .and_then(|v| v.to_str().ok())
                    .ok_or(HttpError(Fault::AuthRequired))?,
            )
            .map_err(|_| HttpError(Fault::InvalidInput))?;
            url.set_path("/");
            url.set_query(None);
            url.set_fragment(Some(&format!("admin-sign-in={challenge}.{verifier}")));
            if mailer
                .send_link(email, url.to_string(), challenge.clone())
                .await
                .is_ok()
            {
                let auth = s.auth.clone();
                run(s, move |db| db.admin_link_delivered(&auth, &challenge)).await?;
            }
        }
    }
    // Identical status/body/headers for permitted, unknown and rate-limited addresses.
    Ok((
        StatusCode::ACCEPTED,
        Json(serde_json::json!({"accepted":true,"expires_in":LINK_SECONDS,"retry_after":60})),
    )
        .into_response())
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Consume {
    token: String,
}
async fn consume_link(
    State(s): State<App>,
    headers: HeaderMap,
    input: Result<Json<Consume>, JsonRejection>,
) -> Result<Response, HttpError> {
    origin(&s, &headers)?;
    let input = body(input)?;
    let (challenge, verifier) = input
        .token
        .split_once('.')
        .ok_or(HttpError(Fault::AuthRequired))?;
    let (challenge, verifier, auth) = (challenge.to_owned(), verifier.to_owned(), s.auth.clone());
    let (email, token) = run(s.clone(), move |db| {
        db.finish_admin_link(&auth, &challenge, &verifier)
    })
    .await?;
    let mut response = Json(serde_json::json!({"email":email,"csrf_token":csrf(&s.auth, &token),"expires_in":SESSION_SECONDS})).into_response();
    response.headers_mut().insert(
        header::SET_COOKIE,
        HeaderValue::from_str(&s.auth.cookie("dmem_admin_session", &token, SESSION_SECONDS))
            .map_err(|_| HttpError(Fault::Internal))?,
    );
    Ok(response)
}
async fn session(State(s): State<App>, headers: HeaderMap) -> Reply<serde_json::Value> {
    if headers.contains_key(header::ORIGIN) {
        origin(&s, &headers)?;
    }
    let (email, token, expires) = session_identity(&s, &headers)?;
    Ok(Json(
        serde_json::json!({"email":email,"csrf_token":csrf(&s.auth, &token),"expires_in":expires.saturating_sub(s.auth.now())}),
    ))
}
async fn logout(State(s): State<App>, headers: HeaderMap) -> Result<Response, HttpError> {
    origin(&s, &headers)?;
    let (_, token, _) = session_identity(&s, &headers)?;
    verify_csrf(&s, &headers, &token)?;
    let auth = s.auth.clone();
    run(s.clone(), move |db| db.admin_logout(&auth, &token)).await?;
    let mut response = Json(serde_json::json!({"signed_out":true})).into_response();
    response.headers_mut().insert(
        header::SET_COOKIE,
        HeaderValue::from_str(&s.auth.cookie("dmem_admin_session", "", 0))
            .map_err(|_| HttpError(Fault::Internal))?,
    );
    Ok(response)
}
