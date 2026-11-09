use super::*;
use crate::{
    community::Submission,
    identity::{constant_eq, normalize_email, secret},
};
use axum::http::HeaderMap;
use serde::Deserialize;

pub(super) fn routes(s: &App) -> Router<App> {
    let contributions = Router::new()
        .route("/me/contributions", get(contributions).post(submit))
        .route("/me/contributions/{id}/review", get(own_review))
        .route(
            "/me/contributions/{id}/withdraw",
            axum::routing::post(withdraw),
        )
        .route_layer(middleware::from_fn_with_state(s.clone(), require_member));
    let personal = Router::new()
        .route("/me", get(dashboard))
        .route("/me/profile", get(member_profile).put(save_member_profile))
        .merge(contributions)
        .route_layer(middleware::from_fn_with_state(s.clone(), authenticate));
    Router::new()
        .route("/auth/config", get(config))
        .route("/leaderboard", get(leaderboard))
        .route("/profiles/{handle}", get(public_member))
        .route("/auth/email/start", axum::routing::post(start))
        .route("/auth/email/verify", axum::routing::post(verify))
        .route("/auth/email/link", axum::routing::post(start_link))
        .route("/auth/email/consume", axum::routing::post(consume_link))
        .route("/auth/session", get(session))
        .route("/auth/logout", axum::routing::post(logout))
        .route("/public/templates", get(public_templates))
        .route("/public/templates/{id}", get(public_template))
        .route("/public/templates/{id}/origin", get(super::web::public_origin))
        .route("/admin/contributions", get(queue))
        .route("/admin/contributions/{id}/review", get(review))
        .route(
            "/admin/contributions/{id}/decision",
            axum::routing::post(decision),
        )
        .merge(personal)
        .layer(DefaultBodyLimit::max(16 * 1024))
}
async fn require_member(
    State(s): State<App>,
    Extension(Owner(owner)): Extension<Owner>,
    req: Request,
    next: Next,
) -> Result<Response, HttpError> {
    if !run(s, move |db| db.is_member(&owner)).await? {
        return Err(Fault::AuthRequired.into());
    }
    Ok(next.run(req).await)
}
pub(super) async fn no_store(req: Request, next: Next) -> Response {
    let mut r = next.run(req).await;
    r.headers_mut()
        .insert(header::CACHE_CONTROL, HeaderValue::from_static("no-store"));
    r
}
pub(super) fn cookie(headers: &HeaderMap, name: &str) -> Option<String> {
    let prefix = format!("{name}=");
    let mut found = None;
    for value in headers.get_all(header::COOKIE) {
        for pair in value.to_str().ok()?.split(';') {
            if let Some(value) = pair.trim().strip_prefix(&prefix) {
                if found.is_some() || value.len() > 128 {
                    return None;
                }
                found = Some(value.to_string());
            }
        }
    }
    found
}
pub(super) fn origin(s: &App, headers: &HeaderMap) -> Result<(), HttpError> {
    let mut origins = headers.get_all(header::ORIGIN).iter();
    if !origins
        .next()
        .and_then(|v| v.to_str().ok())
        .is_some_and(|o| s.origins.iter().any(|a| a == o))
        || origins.next().is_some()
    {
        return Err(Fault::AuthRequired.into());
    }
    Ok(())
}
fn cookies(mut r: Response, s: &App, values: &[(&str, &str, u64)]) -> Result<Response, HttpError> {
    for (name, value, age) in values {
        r.headers_mut().append(
            header::SET_COOKIE,
            HeaderValue::from_str(&s.auth.cookie(name, value, *age))
                .map_err(|_| HttpError(Fault::Internal))?,
        );
    }
    Ok(r)
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Start {
    email: String,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Verify {
    code: String,
}
async fn member_profile(
    State(s): State<App>,
    Extension(Owner(owner)): Extension<Owner>,
) -> Reply<crate::members::MemberProfile> {
    Ok(Json(run(s, move |db| db.member_profile(&owner)).await?))
}
async fn save_member_profile(
    State(s): State<App>,
    Extension(Owner(owner)): Extension<Owner>,
    input: Result<Json<crate::members::ProfileUpdate>, JsonRejection>,
) -> Reply<crate::members::MemberProfile> {
    let input = body(input)?;
    let now = s.auth.now();
    Ok(Json(
        run(s, move |db| db.save_member_profile(&owner, input, now)).await?,
    ))
}
async fn leaderboard(
    State(s): State<App>,
    q: Result<Query<crate::members::BoardQuery>, QueryRejection>,
) -> Reply<crate::members::Leaderboard> {
    let Query(q) = q.map_err(|_| HttpError(Fault::InvalidInput))?;
    Ok(Json(run(s, move |db| db.leaderboard(q.offset)).await?))
}
async fn public_member(
    State(s): State<App>,
    p: Result<Path<String>, PathRejection>,
) -> Reply<crate::members::PublicProfile> {
    let handle = path(p)?;
    Ok(Json(run(s, move |db| db.public_member(&handle)).await?))
}
async fn config(State(s): State<App>) -> Json<serde_json::Value> {
    Json(serde_json::json!({"email_enabled":s.auth.mailer.is_some()}))
}
async fn start(
    State(s): State<App>,
    headers: HeaderMap,
    input: Result<Json<Start>, JsonRejection>,
) -> Result<Response, HttpError> {
    send_email(s, headers, body(input)?, false).await
}
async fn start_link(
    State(s): State<App>,
    headers: HeaderMap,
    input: Result<Json<Start>, JsonRejection>,
) -> Result<Response, HttpError> {
    send_email(s, headers, body(input)?, true).await
}
async fn send_email(
    s: App,
    headers: HeaderMap,
    input: Start,
    link: bool,
) -> Result<Response, HttpError> {
    origin(&s, &headers)?;
    let email = normalize_email(&input.email)?;
    let mailer = s
        .auth
        .mailer
        .as_ref()
        .ok_or(HttpError(Fault::ServerUnavailable))?
        .clone();
    let browser = cookie(&headers, "dmem_browser")
        .filter(|v| v.len() == 64 && v.bytes().all(|b| b.is_ascii_hexdigit()))
        .unwrap_or_else(secret);
    let challenge = secret();
    let code = if link {
        secret()
    } else {
        loop {
            let raw = UuidCode::random();
            if raw < 4_294_000_000 {
                break format!("{:06}", raw % 1_000_000);
            }
        }
    };
    let (db, auth) = (s.store.clone(), s.auth.clone());
    let (e, b, c, k) = (
        email.clone(),
        browser.clone(),
        challenge.clone(),
        code.clone(),
    );
    tokio::task::spawn_blocking(move || db.begin_email(&auth, &e, &b, &c, &k))
        .await
        .map_err(|_| HttpError(Fault::Internal))??;
    let delivery = if link {
        // The request origin was matched against configured origins above; never use Host.
        let mut url = reqwest::Url::parse(
            headers
                .get(header::ORIGIN)
                .and_then(|v| v.to_str().ok())
                .ok_or(HttpError(Fault::AuthRequired))?,
        )
        .map_err(|_| HttpError(Fault::InvalidInput))?;
        url.set_path("/");
        url.set_query(None);
        url.set_fragment(Some(&format!("sign-in={challenge}.{code}")));
        mailer.send_link(email, url.to_string(), challenge.clone())
    } else {
        mailer.send_code(email, code, challenge.clone())
    };
    if delivery.await.is_err() {
        return Err(Fault::ServerUnavailable.into());
    }
    s.store.email_delivered(&s.auth, &challenge, true)?;
    cookies(
        (
            StatusCode::ACCEPTED,
            Json(serde_json::json!({"sent":true,"expires_in":600,"retry_after":60})),
        )
            .into_response(),
        &s,
        &[
            ("dmem_challenge", &challenge, 600),
            ("dmem_browser", &browser, 86400),
        ],
    )
}
struct UuidCode;
impl UuidCode {
    fn random() -> u32 {
        let u = uuid::Uuid::new_v4();
        u32::from_le_bytes(u.as_bytes()[0..4].try_into().expect("four bytes"))
    }
}
async fn verify(
    State(s): State<App>,
    headers: HeaderMap,
    input: Result<Json<Verify>, JsonRejection>,
) -> Result<Response, HttpError> {
    origin(&s, &headers)?;
    let input = body(input)?;
    let challenge = cookie(&headers, "dmem_challenge").ok_or(HttpError(Fault::AuthRequired))?;
    let browser = cookie(&headers, "dmem_browser").ok_or(HttpError(Fault::AuthRequired))?;
    let (db, auth) = (s.store.clone(), s.auth.clone());
    let (account, token) = tokio::task::spawn_blocking(move || {
        db.finish_email(&auth, &challenge, &browser, &input.code)
    })
    .await
    .map_err(|_| HttpError(Fault::Internal))??;
    signed_in(&s, account, token)
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ConsumeLink {
    token: String,
}
async fn consume_link(
    State(s): State<App>,
    headers: HeaderMap,
    input: Result<Json<ConsumeLink>, JsonRejection>,
) -> Result<Response, HttpError> {
    origin(&s, &headers)?;
    let token = body(input)?.token;
    let (challenge, verifier) = token
        .split_once('.')
        .filter(|(c, v)| {
            c.len() == 64
                && v.len() == 64
                && c.bytes().chain(v.bytes()).all(|b| b.is_ascii_hexdigit())
        })
        .ok_or(HttpError(Fault::AuthRequired))?;
    let (challenge, verifier) = (challenge.to_owned(), verifier.to_owned());
    let (db, auth) = (s.store.clone(), s.auth.clone());
    let (account, token) =
        tokio::task::spawn_blocking(move || db.finish_email_link(&auth, &challenge, &verifier))
            .await
            .map_err(|_| HttpError(Fault::Internal))??;
    signed_in(&s, account, token)
}
fn signed_in(
    s: &App,
    account: crate::identity::Account,
    token: String,
) -> Result<Response, HttpError> {
    cookies(
        Json(serde_json::json!({"account":account,"csrf_token":s.auth.csrf(&token)}))
            .into_response(),
        &s,
        &[
            ("dmem_session", &token, 30 * 86400),
            ("dmem_challenge", "", 0),
        ],
    )
}
async fn session(State(s): State<App>, headers: HeaderMap) -> Reply<serde_json::Value> {
    let token = cookie(&headers, "dmem_session").ok_or(HttpError(Fault::AuthRequired))?;
    let account = s.store.session(&s.auth, &token)?;
    Ok(Json(
        serde_json::json!({"account":account,"csrf_token":s.auth.csrf(&token)}),
    ))
}
async fn logout(State(s): State<App>, headers: HeaderMap) -> Result<Response, HttpError> {
    origin(&s, &headers)?;
    let token = cookie(&headers, "dmem_session").ok_or(HttpError(Fault::AuthRequired))?;
    s.store.session(&s.auth, &token)?;
    if !constant_eq(
        headers
            .get("x-csrf-token")
            .and_then(|v| v.to_str().ok())
            .unwrap_or(""),
        &s.auth.csrf(&token),
    ) {
        return Err(Fault::AuthRequired.into());
    }
    s.store.logout(&s.auth, &token)?;
    cookies(
        Json(serde_json::json!({"signed_out":true})).into_response(),
        &s,
        &[("dmem_session", "", 0), ("dmem_challenge", "", 0)],
    )
}
async fn public_templates(
    State(s): State<App>,
    q: Result<Query<Search>, QueryRejection>,
) -> Reply<List<Template>> {
    let mut q = query(q)?;
    q.visibility = Some(Visibility::Public);
    Ok(Json(run(s, move |db| db.templates("@catalog", q)).await?))
}
async fn public_template(
    State(s): State<App>,
    p: Result<Path<String>, PathRejection>,
) -> Reply<Template> {
    let id = path(p)?;
    Ok(Json(run(s, move |db| db.template("@catalog", &id)).await?))
}
async fn dashboard(
    State(s): State<App>,
    Extension(Owner(owner)): Extension<Owner>,
) -> Reply<serde_json::Value> {
    Ok(Json(run(s, move |db| db.dashboard(&owner)).await?))
}
async fn contributions(
    State(s): State<App>,
    Extension(Owner(owner)): Extension<Owner>,
) -> Reply<List<crate::community::Contribution>> {
    Ok(Json(
        run(s, move |db| db.contributions(Some(&owner))).await?,
    ))
}
async fn submit(
    State(s): State<App>,
    Extension(Owner(owner)): Extension<Owner>,
    input: Result<Json<Submission>, JsonRejection>,
) -> Reply<crate::community::Contribution> {
    let input = body(input)?;
    let now = s.auth.now();
    Ok(Json(run(s, move |db| db.submit(&owner, input, now)).await?))
}
async fn withdraw(
    State(s): State<App>,
    Extension(Owner(owner)): Extension<Owner>,
    p: Result<Path<String>, PathRejection>,
) -> Reply<crate::community::Contribution> {
    let id = path(p)?;
    let now = s.auth.now();
    Ok(Json(run(s, move |db| db.withdraw(&owner, &id, now)).await?))
}
async fn own_review(
    State(s): State<App>,
    Extension(Owner(owner)): Extension<Owner>,
    p: Result<Path<String>, PathRejection>,
) -> Reply<dmem_core::review::ReviewReport> {
    let id = path(p)?;
    Ok(Json(
        run(s, move |db| db.review_contribution(Some(&owner), &id)).await?,
    ))
}
async fn review(
    State(s): State<App>,
    headers: HeaderMap,
    p: Result<Path<String>, PathRejection>,
) -> Reply<dmem_core::review::ReviewReport> {
    admin(&s, &headers, false)?;
    let id = path(p)?;
    Ok(Json(
        run(s, move |db| db.review_contribution(None, &id)).await?,
    ))
}
fn admin(s: &App, headers: &HeaderMap, write: bool) -> Result<String, HttpError> {
    super::admin::authorize(s, headers, write)
}
async fn queue(
    State(s): State<App>,
    headers: HeaderMap,
    q: Result<Query<crate::community::ContributionQueueQuery>, QueryRejection>,
) -> Reply<crate::community::ContributionPage> {
    admin(&s, &headers, false)?;
    let Query(q) = q.map_err(|_| HttpError(Fault::InvalidInput))?;
    Ok(Json(run(s, move |db| db.contribution_queue(q)).await?))
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Decision {
    decision: String,
}
async fn decision(
    State(s): State<App>,
    headers: HeaderMap,
    p: Result<Path<String>, PathRejection>,
    input: Result<Json<Decision>, JsonRejection>,
) -> Reply<crate::community::Contribution> {
    let actor = admin(&s, &headers, true)?;
    let id = path(p)?;
    let input = body(input)?;
    if !["approve", "reject"].contains(&input.decision.as_str()) {
        return Err(Fault::InvalidInput.into());
    }
    let now = s.auth.now();
    Ok(Json(
        run(s, move |db| {
            db.decide(&id, input.decision == "approve", now, &actor)
        })
        .await?,
    ))
}
