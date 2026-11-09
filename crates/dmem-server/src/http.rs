use crate::{AuthConfig, Store};
mod account;
use axum::{
    Extension, Json, Router,
    extract::Request,
    extract::{
        DefaultBodyLimit, Multipart, Path, Query, State,
        multipart::MultipartRejection,
        rejection::{JsonRejection, PathRejection, QueryRejection},
    },
    http::{HeaderValue, Method, StatusCode, header},
    middleware::{self, Next},
    response::{IntoResponse, Response},
    routing::get,
};
use dmem_contracts::*;
use serde::de::DeserializeOwned;
use sha2::{Digest, Sha256};
use std::{collections::HashMap, path::PathBuf, sync::Arc};
use tower_http::{cors::CorsLayer, services::ServeDir};

#[derive(Clone)]
struct App {
    store: Arc<Store>,
    tokens: Arc<HashMap<[u8; 32], String>>,
    origins: Arc<Vec<String>>,
    auth: Arc<AuthConfig>,
}
#[derive(Clone)]
struct Owner(String);
struct HttpError(Fault);
impl From<Fault> for HttpError {
    fn from(f: Fault) -> Self {
        Self(f)
    }
}
impl IntoResponse for HttpError {
    fn into_response(self) -> Response {
        (
            StatusCode::from_u16(self.0.status()).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR),
            Json(self.0.body()),
        )
            .into_response()
    }
}
type Reply<T> = Result<Json<T>, HttpError>;
fn body<T: DeserializeOwned>(r: Result<Json<T>, JsonRejection>) -> Result<T, HttpError> {
    r.map(|Json(v)| v).map_err(|e| {
        HttpError(if e.status() == StatusCode::PAYLOAD_TOO_LARGE {
            Fault::PayloadTooLarge
        } else {
            Fault::InvalidInput
        })
    })
}
fn query(r: Result<Query<Search>, QueryRejection>) -> Result<Search, HttpError> {
    r.map(|Query(v)| v).map_err(|_| Fault::InvalidInput.into())
}
fn path(r: Result<Path<String>, PathRejection>) -> Result<String, HttpError> {
    r.map(|Path(v)| v).map_err(|_| Fault::InvalidInput.into())
}
async fn run<T: Send + 'static>(
    s: App,
    f: impl FnOnce(&Store) -> Result<T, Fault> + Send + 'static,
) -> Result<T, HttpError> {
    tokio::task::spawn_blocking(move || f(&s.store))
        .await
        .map_err(|_| HttpError(Fault::Internal))?
        .map_err(Into::into)
}

pub fn router(
    store: Arc<Store>,
    credentials: Vec<(String, String)>,
    origins: Vec<String>,
    web_dir: Option<PathBuf>,
) -> Result<Router, Fault> {
    router_with_auth(store, credentials, origins, web_dir, AuthConfig::default())
}
pub fn router_with_auth(
    store: Arc<Store>,
    credentials: Vec<(String, String)>,
    origins: Vec<String>,
    web_dir: Option<PathBuf>,
    auth: AuthConfig,
) -> Result<Router, Fault> {
    if auth
        .admin_token
        .as_ref()
        .is_some_and(|t| t.len() < 32 || credentials.iter().any(|(token, _)| token == t))
    {
        return Err(Fault::InvalidInput);
    }
    if credentials.is_empty()
        || credentials
            .iter()
            .any(|(token, owner)| token.len() < 16 || owner.is_empty() || owner.starts_with('@'))
    {
        return Err(Fault::InvalidInput);
    }
    let tokens = credentials
        .into_iter()
        .map(|(t, o)| (Sha256::digest(t.as_bytes()).into(), o))
        .collect();
    let allowed: Vec<HeaderValue> = origins
        .iter()
        .map(|s| s.parse().map_err(|_| Fault::InvalidInput))
        .collect::<Result<_, _>>()?;
    let state = App {
        store,
        tokens: Arc::new(tokens),
        origins: Arc::new(origins),
        auth: Arc::new(auth),
    };
    let api = Router::new()
        .route("/status", get(status))
        .route("/templates", get(templates).post(create_template))
        .route("/templates/{id}", get(template))
        .route("/templates/{id}/copy", axum::routing::post(copy_template))
        .route("/sources", get(sources).post(import_source))
        .route("/sources/{id}", get(source))
        .route("/sources/{id}/file", get(source_file))
        .route(
            "/sources/{id}/template",
            axum::routing::post(template_from_source),
        )
        .route("/documents", get(documents).post(create_document))
        .route("/documents/{id}", get(document).put(save_document))
        .route("/documents/{id}/revisions", get(revisions))
        .route("/documents/{id}/export/{format}", get(export_document))
        .fallback(|| async { HttpError(Fault::NotFound) })
        .method_not_allowed_fallback(|| async { HttpError(Fault::InvalidInput) })
        .route_layer(middleware::from_fn_with_state(state.clone(), authenticate))
        .layer(DefaultBodyLimit::max(MAX_UPLOAD + 64 * 1024));
    let cors = CorsLayer::new()
        .allow_origin(allowed)
        .allow_methods([Method::GET, Method::POST, Method::PUT])
        .allow_headers([
            header::AUTHORIZATION,
            header::CONTENT_TYPE,
            axum::http::HeaderName::from_static("x-csrf-token"),
        ])
        .allow_credentials(true);
    let mut app = Router::new()
        .route(
            "/healthz",
            get(|| async { Json(serde_json::json!({"ready":true})) }),
        )
        .nest("/v1", api.merge(account::routes(&state)))
        .with_state(state)
        .layer(middleware::from_fn(account::no_store))
        .layer(cors);
    if let Some(dir) = web_dir {
        app = app.fallback_service(ServeDir::new(dir));
    }
    Ok(app)
}
async fn authenticate(
    State(s): State<App>,
    mut req: Request,
    next: Next,
) -> Result<Response, HttpError> {
    if let Some(origin) = req.headers().get(header::ORIGIN) {
        if !origin
            .to_str()
            .ok()
            .is_some_and(|o| s.origins.iter().any(|a| a == o))
        {
            return Err(Fault::AuthRequired.into());
        }
    }
    if req.headers().get(header::AUTHORIZATION).is_none() {
        let token =
            account::cookie(req.headers(), "dmem_session").ok_or(HttpError(Fault::AuthRequired))?;
        let owner = s.store.session(&s.auth, &token)?;
        if !matches!(*req.method(), Method::GET | Method::HEAD | Method::OPTIONS) {
            account::origin(&s, req.headers())?;
            let csrf = req
                .headers()
                .get("x-csrf-token")
                .and_then(|v| v.to_str().ok())
                .unwrap_or("");
            if !crate::identity::constant_eq(csrf, &s.auth.csrf(&token)) {
                return Err(Fault::AuthRequired.into());
            }
        }
        req.extensions_mut().insert(Owner(owner.id));
        return Ok(next.run(req).await);
    }
    let token = req
        .headers()
        .get(header::AUTHORIZATION)
        .and_then(|v| v.to_str().ok())
        .and_then(|v| v.strip_prefix("Bearer "))
        .ok_or(HttpError(Fault::AuthRequired))?;
    let digest: [u8; 32] = Sha256::digest(token.as_bytes()).into();
    let owner = s
        .tokens
        .get(&digest)
        .ok_or(HttpError(Fault::AuthRequired))?
        .clone();
    req.extensions_mut().insert(Owner(owner));
    Ok(next.run(req).await)
}
async fn status(State(s): State<App>) -> Json<serde_json::Value> {
    Json(
        serde_json::json!({"service":"my-document-memory","schema_version":SCHEMA_VERSION,"storage":"sqlite","mode":if s.auth.mailer.is_some() {"accounts"}else{"local"},"vocab":dmem_core::vocabulary(),"capabilities":{"imports":["txt","markdown","docx","pptx"],"exports":["markdown","html","docx","pptx"],"pdf":"browser_print","generation":"deterministic_outline","provider_sync":false,"sheets_editor":false}}),
    )
}
async fn templates(
    State(s): State<App>,
    Extension(Owner(o)): Extension<Owner>,
    q: Result<Query<Search>, QueryRejection>,
) -> Reply<List<Template>> {
    let q = query(q)?;
    Ok(Json(run(s, move |db| db.templates(&o, q)).await?))
}
async fn template(
    State(s): State<App>,
    Extension(Owner(o)): Extension<Owner>,
    p: Result<Path<String>, PathRejection>,
) -> Reply<Template> {
    let id = path(p)?;
    Ok(Json(run(s, move |db| db.template(&o, &id)).await?))
}
async fn create_template(
    State(s): State<App>,
    Extension(Owner(o)): Extension<Owner>,
    j: Result<Json<CreateTemplate>, JsonRejection>,
) -> Reply<Template> {
    let i = body(j)?;
    Ok(Json(run(s, move |db| db.create_template(&o, i)).await?))
}
async fn copy_template(
    State(s): State<App>,
    Extension(Owner(o)): Extension<Owner>,
    p: Result<Path<String>, PathRejection>,
) -> Reply<Template> {
    let id = path(p)?;
    Ok(Json(run(s, move |db| db.copy_template(&o, &id)).await?))
}
async fn sources(
    State(s): State<App>,
    Extension(Owner(o)): Extension<Owner>,
    q: Result<Query<Search>, QueryRejection>,
) -> Reply<List<Source>> {
    let q = query(q)?;
    Ok(Json(run(s, move |db| db.sources(&o, q)).await?))
}
async fn source(
    State(s): State<App>,
    Extension(Owner(o)): Extension<Owner>,
    p: Result<Path<String>, PathRejection>,
) -> Reply<Source> {
    let id = path(p)?;
    Ok(Json(run(s, move |db| db.source(&o, &id)).await?))
}
async fn template_from_source(
    State(s): State<App>,
    Extension(Owner(o)): Extension<Owner>,
    p: Result<Path<String>, PathRejection>,
) -> Reply<Template> {
    let id = path(p)?;
    Ok(Json(
        run(s, move |db| db.template_from_source(&o, &id)).await?,
    ))
}
async fn import_source(
    State(s): State<App>,
    Extension(Owner(o)): Extension<Owner>,
    m: Result<Multipart, MultipartRejection>,
) -> Reply<Source> {
    let mut m = m.map_err(|_| HttpError(Fault::InvalidInput))?;
    let mut title = None;
    let mut file = None;
    while let Some(field) = m.next_field().await.map_err(|e| {
        HttpError(if e.status() == StatusCode::PAYLOAD_TOO_LARGE {
            Fault::PayloadTooLarge
        } else {
            Fault::InvalidInput
        })
    })? {
        match field.name() {
            Some("title") if title.is_none() => {
                title = Some(
                    field
                        .text()
                        .await
                        .map_err(|_| HttpError(Fault::InvalidInput))?,
                );
            }
            Some("file") if file.is_none() => {
                let filename = field
                    .file_name()
                    .ok_or(HttpError(Fault::InvalidInput))?
                    .to_owned();
                let bytes = field.bytes().await.map_err(|e| {
                    HttpError(if e.status() == StatusCode::PAYLOAD_TOO_LARGE {
                        Fault::PayloadTooLarge
                    } else {
                        Fault::InvalidInput
                    })
                })?;
                if bytes.len() > MAX_UPLOAD {
                    return Err(Fault::PayloadTooLarge.into());
                }
                file = Some((filename, bytes.to_vec()));
            }
            _ => return Err(Fault::InvalidInput.into()),
        }
    }
    let (filename, bytes) = file.ok_or(HttpError(Fault::InvalidInput))?;
    let title = title.unwrap_or_else(|| filename.chars().take(120).collect());
    Ok(Json(
        run(s, move |db| db.import_source(&o, title, filename, bytes)).await?,
    ))
}
async fn source_file(
    State(s): State<App>,
    Extension(Owner(o)): Extension<Owner>,
    p: Result<Path<String>, PathRejection>,
) -> Result<Response, HttpError> {
    let id = path(p)?;
    let (source, bytes) = run(s, move |db| db.source_file(&o, &id)).await?;
    let mut response = bytes.into_response();
    response.headers_mut().insert(
        header::CONTENT_TYPE,
        HeaderValue::from_static("application/octet-stream"),
    );
    response.headers_mut().insert(
        header::CONTENT_DISPOSITION,
        format!("attachment; filename=\"original.{}\"", source.format)
            .parse()
            .map_err(|_| HttpError(Fault::Internal))?,
    );
    Ok(response)
}
async fn documents(
    State(s): State<App>,
    Extension(Owner(o)): Extension<Owner>,
    q: Result<Query<Search>, QueryRejection>,
) -> Reply<List<Document>> {
    let q = query(q)?;
    Ok(Json(run(s, move |db| db.documents(&o, q)).await?))
}
async fn document(
    State(s): State<App>,
    Extension(Owner(o)): Extension<Owner>,
    p: Result<Path<String>, PathRejection>,
) -> Reply<Document> {
    let id = path(p)?;
    Ok(Json(run(s, move |db| db.document(&o, &id)).await?))
}
async fn create_document(
    State(s): State<App>,
    Extension(Owner(o)): Extension<Owner>,
    j: Result<Json<CreateDocument>, JsonRejection>,
) -> Reply<Document> {
    let i = body(j)?;
    Ok(Json(run(s, move |db| db.create_document(&o, i)).await?))
}
async fn save_document(
    State(s): State<App>,
    Extension(Owner(o)): Extension<Owner>,
    p: Result<Path<String>, PathRejection>,
    j: Result<Json<SaveDocument>, JsonRejection>,
) -> Reply<Document> {
    let id = path(p)?;
    let i = body(j)?;
    Ok(Json(run(s, move |db| db.save_document(&o, &id, i)).await?))
}
async fn revisions(
    State(s): State<App>,
    Extension(Owner(o)): Extension<Owner>,
    p: Result<Path<String>, PathRejection>,
) -> Reply<List<Document>> {
    let id = path(p)?;
    Ok(Json(run(s, move |db| db.revisions(&o, &id)).await?))
}
async fn export_document(
    State(s): State<App>,
    Extension(Owner(o)): Extension<Owner>,
    p: Result<Path<(String, String)>, PathRejection>,
) -> Result<Response, HttpError> {
    let Path((id, format)) = p.map_err(|_| HttpError(Fault::InvalidInput))?;
    let out = run(s, move |db| {
        let doc = db.document(&o, &id)?;
        dmem_core::export(&doc.title, doc.family, &doc.content, &format)
    })
    .await?;
    let mut response = out.bytes.into_response();
    response
        .headers_mut()
        .insert(header::CONTENT_TYPE, HeaderValue::from_static(out.mime));
    response.headers_mut().insert(
        header::CONTENT_DISPOSITION,
        format!("attachment; filename=\"document.{}\"", out.extension)
            .parse()
            .map_err(|_| HttpError(Fault::Internal))?,
    );
    Ok(response)
}
