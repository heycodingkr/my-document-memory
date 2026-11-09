use crate::{Form, FormInput, Provider};
use serde::{Deserialize, Serialize};

pub const WEB_MAX_BYTES: usize = 5 * 1024 * 1024;
pub const PREVIEW_TTL: u64 = 15 * 60;
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct WebPreviewInput {
    pub url: String,
}
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct WebSearchInput {
    pub query: String,
    pub locale: Option<String>,
    pub limit: Option<usize>,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum WebKind {
    Template,
    Reference,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CopyMode {
    StructureOnly,
    Full,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WebImportInput {
    pub preview_id: String,
    pub kind: WebKind,
    pub title: Option<String>,
    pub form: Option<FormInput>,
    pub copy_mode: Option<CopyMode>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WebClipInput {
    pub url: String,
    pub html: String,
    pub kind: WebKind,
    pub title: Option<String>,
    pub form: Option<FormInput>,
    pub copy_mode: Option<CopyMode>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebPreview {
    pub preview_id: String,
    pub canonical_url: String,
    pub title: String,
    pub provider: Provider,
    pub form: Form,
    pub outline: Vec<String>,
    pub table_headers: Vec<Vec<String>>,
    pub license: String,
    pub copy_policy_default: CopyMode,
    pub content_hash: String,
    pub warnings: Vec<String>,
    pub fetched_at: u64,
    pub expires_at: u64,
    pub untrusted: bool,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebOrigin {
    pub record_id: String,
    pub canonical_url: String,
    pub form: Form,
    pub license: String,
    pub copy_policy: CopyMode,
    pub provenance: String,
    pub content_hash: String,
    pub retrieved_at: u64,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebImportResult {
    pub id: String,
    pub kind: WebKind,
    pub version: u32,
    pub created: bool,
    pub origin: WebOrigin,
    pub warnings: Vec<String>,
    pub body_chars_removed: usize,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebSearchHit {
    pub title: String,
    pub url: String,
    pub snippet: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebSearchResult {
    pub items: Vec<WebSearchHit>,
    pub untrusted: bool,
}
