use super::*;
use axum::{body::Bytes, http::HeaderMap};
use url::Url;

pub(super) async fn search(
    State(s): State<App>,
    Extension(owner): Extension<Owner>,
    input: Result<Json<WebSearchInput>, JsonRejection>,
) -> Reply<WebSearchResult> {
    Ok(Json(s.web.search(&owner.0, body(input)?).await?))
}
pub(super) async fn preview(
    State(s): State<App>,
    Extension(owner): Extension<Owner>,
    input: Result<Json<WebPreviewInput>, JsonRejection>,
) -> Reply<WebPreview> {
    Ok(Json(s.web.preview(&owner.0, body(input)?).await?))
}
pub(super) async fn import(
    State(s): State<App>,
    Extension(owner): Extension<Owner>,
    input: Result<Json<WebImportInput>, JsonRejection>,
) -> Reply<WebImportResult> {
    s.web.admit(&owner.0)?;
    let input = body(input)?;
    let snapshot = s.web.snapshot(&owner.0, &input.preview_id)?;
    Ok(Json(
        run(s, move |store| {
            store.web_import(&owner.0, snapshot, input, "fetched")
        })
        .await?,
    ))
}
pub(super) async fn origin(
    State(s): State<App>,
    Extension(owner): Extension<Owner>,
    id: Result<Path<String>, PathRejection>,
) -> Reply<WebOrigin> {
    let id = path(id)?;
    Ok(Json(
        run(s, move |store| store.web_origin(&owner.0, &id)).await?,
    ))
}
pub(super) async fn public_origin(
    State(s): State<App>,
    id: Result<Path<String>, PathRejection>,
) -> Reply<WebOrigin> {
    let id = path(id)?;
    Ok(Json(
        run(s, move |store| store.web_origin("@catalog", &id)).await?,
    ))
}
pub(super) async fn clip(
    State(s): State<App>,
    Extension(owner): Extension<Owner>,
    headers: HeaderMap,
    bytes: Bytes,
) -> Reply<WebImportResult> {
    s.web.admit(&owner.0)?;
    if bytes.len() > MAX_CONTENT + 64 * 1024 {
        return Err(Fault::PayloadTooLarge.into());
    }
    let provenance = s.web.capture_provenance(&headers, &bytes)?;
    let input: WebClipInput = serde_json::from_slice(&bytes).map_err(|_| Fault::InvalidInput)?;
    if input.url.len() > 2048 || input.html.len() > MAX_CONTENT {
        return Err(Fault::PayloadTooLarge.into());
    }
    let url = Url::parse(&input.url).map_err(|_| Fault::InvalidInput)?;
    let page = dmem_core::web::parse_html(&input.html)?;
    let snapshot = s.web.prepare(&url, page)?;
    let request = WebImportInput {
        preview_id: snapshot.preview.preview_id.clone(),
        kind: input.kind,
        title: input.title,
        form: input.form,
        copy_mode: input.copy_mode,
    };
    Ok(Json(
        run(s, move |store| {
            store.web_import(&owner.0, snapshot, request, provenance)
        })
        .await?,
    ))
}
