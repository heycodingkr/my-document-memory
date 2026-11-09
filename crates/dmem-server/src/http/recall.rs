use super::{App, Extension, Owner, State};
use axum::{
    Json,
    extract::RawQuery,
    http::StatusCode,
    response::{IntoResponse, Response},
};
use dmem_contracts::{Fault, RecallQuery, RecallResult};
use serde_json::Value;

fn parse(raw: Option<&str>) -> Result<RecallQuery, Fault> {
    let url = reqwest::Url::parse(&format!("http://localhost/?{}", raw.unwrap_or("")))
        .map_err(|_| Fault::InvalidInput)?;
    let mut values = serde_json::Map::new();
    for (key, value) in url.query_pairs() {
        if ![
            "url", "doc_type", "locale", "provider", "keywords", "kind", "scope", "limit",
        ]
        .contains(&key.as_ref())
            || values.contains_key(key.as_ref())
        {
            return Err(Fault::InvalidInput);
        }
        if key == "keywords" {
            values.insert(
                key.into_owned(),
                Value::Array(value.split(',').map(|s| Value::String(s.into())).collect()),
            );
        } else if key == "limit" {
            let n = value.parse::<u8>().map_err(|_| Fault::InvalidInput)?;
            values.insert(key.into_owned(), Value::Number(n.into()));
        } else {
            values.insert(key.into_owned(), Value::String(value.into_owned()));
        }
    }
    serde_json::from_value(Value::Object(values)).map_err(|_| Fault::InvalidInput)
}
fn response_error(f: Fault) -> Response {
    let status = match f {
        Fault::InvalidForm(_) | Fault::UrlRejected(_) => StatusCode::BAD_REQUEST,
        _ => StatusCode::from_u16(f.status()).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR),
    };
    (status, Json(f.body())).into_response()
}
pub(super) async fn handler(
    State(s): State<App>,
    Extension(Owner(owner)): Extension<Owner>,
    RawQuery(raw): RawQuery,
) -> Response {
    let q = match parse(raw.as_deref()) {
        Ok(q) => q,
        Err(e) => return response_error(e),
    };
    let result = tokio::task::spawn_blocking(move || {
        let candidates = s.store.recall_candidates(&owner)?;
        let mut result = dmem_core::recall(&candidates, &q)?;
        for hint in &mut result.hints {
            match s.store.web_origin(&owner, &hint.memory_id) {
                Ok(origin) => dmem_core::web::apply_origin(hint, &origin),
                Err(Fault::NotFound) => {}
                Err(error) => return Err(error),
            }
        }
        Ok(result)
    })
    .await;
    match result {
        Ok(Ok(value)) => Json::<RecallResult>(value).into_response(),
        Ok(Err(e)) => response_error(e),
        Err(_) => response_error(Fault::Internal),
    }
}
