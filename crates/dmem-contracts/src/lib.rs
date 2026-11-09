#![forbid(unsafe_code)]
use serde::{Deserialize, Serialize};
mod recall;
pub use recall::*;
mod web;
pub use web::*;
pub const MAX_UPLOAD: usize = 10 * 1024 * 1024;
pub const MAX_CONTENT: usize = 1024 * 1024;
pub const MAX_RESULTS: usize = 20;
pub const SCHEMA_VERSION: u32 = 1;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Family {
    Document,
    Deck,
    Sheet,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Provider {
    GoogleDocs,
    GoogleSlides,
    GoogleSheets,
    Notion,
    Docx,
    Pptx,
    Xlsx,
    Pdf,
    Markdown,
    Txt,
    Html,
    Other,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Page {
    pub size: String,
    pub orientation: String,
    #[serde(default)]
    pub margins_mm: Option<[u8; 4]>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FormInput {
    pub provider: String,
    pub doc_type: String,
    pub locale: String,
    #[serde(default)]
    pub region: Option<String>,
    #[serde(default)]
    pub variant: Option<String>,
    #[serde(default)]
    pub page: Option<Page>,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Form {
    pub provider: Provider,
    pub family: Family,
    pub doc_type: String,
    pub locale: String,
    pub region: Option<String>,
    pub variant: Option<String>,
    pub page: Option<Page>,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Visibility {
    Private,
    Public,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Origin {
    pub template_id: String,
    pub version: u32,
    pub author: String,
    pub license: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Template {
    pub id: String,
    pub version: u32,
    pub title: String,
    pub summary: String,
    pub form: Form,
    pub tags: Vec<String>,
    pub sections: Vec<String>,
    pub author: String,
    pub license: String,
    pub visibility: Visibility,
    pub origin: Option<Origin>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub attributions: Vec<Origin>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CreateTemplate {
    pub title: String,
    pub summary: String,
    pub form: FormInput,
    pub sections: Vec<String>,
    #[serde(default)]
    pub tags: Vec<String>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Citation {
    pub source_id: String,
    pub source_version: u32,
    pub span_id: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case", deny_unknown_fields)]
pub enum Block {
    Heading {
        text: String,
        level: u8,
    },
    Paragraph {
        text: String,
    },
    List {
        items: Vec<String>,
    },
    Table {
        rows: Vec<Vec<String>>,
    },
    Quote {
        text: String,
        citation: Option<Citation>,
    },
}
impl Block {
    pub fn text(&self) -> String {
        match self {
            Self::Heading { text, .. } | Self::Paragraph { text } | Self::Quote { text, .. } => {
                text.clone()
            }
            Self::List { items } => items.join("\n"),
            Self::Table { rows } => rows
                .iter()
                .map(|r| r.join(" | "))
                .collect::<Vec<_>>()
                .join("\n"),
        }
    }
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Slide {
    pub title: String,
    pub body: String,
    #[serde(default)]
    pub citations: Vec<Citation>,
}
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Content {
    #[serde(default)]
    pub blocks: Vec<Block>,
    #[serde(default)]
    pub slides: Vec<Slide>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourceSpan {
    pub id: String,
    pub location: String,
    pub text: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Source {
    pub id: String,
    pub version: u32,
    pub title: String,
    pub filename: String,
    pub format: String,
    pub checksum: String,
    pub spans: Vec<SourceSpan>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourceVersion {
    pub source_id: String,
    pub version: u32,
    pub title: String,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Document {
    pub id: String,
    pub version: u32,
    pub title: String,
    pub family: Family,
    pub template: Origin,
    pub source_versions: Vec<SourceVersion>,
    pub content: Content,
    pub created_at: u64,
    pub updated_at: u64,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CreateDocument {
    pub title: String,
    pub template_id: String,
    #[serde(default)]
    pub source_ids: Vec<String>,
    #[serde(default)]
    pub outline_approved: bool,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SaveDocument {
    pub base_version: u32,
    pub title: String,
    pub content: Content,
}
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Search {
    #[serde(default)]
    pub q: String,
    pub family: Option<Family>,
    pub visibility: Option<Visibility>,
    pub locale: Option<String>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct List<T> {
    pub items: Vec<T>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiError {
    pub code: String,
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reason: Option<String>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Fault {
    InvalidInput,
    InvalidForm(&'static str),
    UrlRejected(&'static str),
    PayloadTooLarge,
    UnsupportedFormat,
    ExtractEmpty(&'static str),
    AuthRequired,
    NotFound,
    VersionConflict,
    LicenseForbids,
    ReviewBlocked,
    Internal,
    ServerUnavailable,
    RateLimited,
    HandleUnavailable,
    FetchBlocked(&'static str),
    FetchFailed(&'static str),
    SearchUnavailable,
}
impl Fault {
    pub fn code(&self) -> &'static str {
        match self {
            Self::InvalidInput => "invalid_input",
            Self::InvalidForm(_) => "invalid_form",
            Self::UrlRejected(_) => "url_rejected",
            Self::PayloadTooLarge => "payload_too_large",
            Self::UnsupportedFormat => "unsupported_format",
            Self::ExtractEmpty(_) => "extract_empty",
            Self::AuthRequired => "auth_required",
            Self::NotFound => "not_found",
            Self::VersionConflict => "version_conflict",
            Self::LicenseForbids => "license_forbids",
            Self::ReviewBlocked => "review_blocked",
            Self::Internal => "internal",
            Self::ServerUnavailable => "server_unavailable",
            Self::RateLimited => "rate_limited",
            Self::HandleUnavailable => "handle_unavailable",
            Self::FetchBlocked(_) => "fetch_blocked",
            Self::FetchFailed(_) => "fetch_failed",
            Self::SearchUnavailable => "search_unavailable",
        }
    }
    pub fn status(&self) -> u16 {
        match self {
            Self::InvalidInput => 400,
            Self::AuthRequired => 401,
            Self::LicenseForbids => 403,
            Self::NotFound => 404,
            Self::VersionConflict | Self::HandleUnavailable => 409,
            Self::PayloadTooLarge => 413,
            Self::UnsupportedFormat => 415,
            Self::ReviewBlocked => 422,
            Self::InvalidForm(_)
            | Self::UrlRejected(_)
            | Self::ExtractEmpty(_)
            | Self::FetchBlocked(_) => 422,
            Self::FetchFailed(_) => 502,
            Self::SearchUnavailable => 503,
            Self::Internal => 500,
            Self::ServerUnavailable => 503,
            Self::RateLimited => 429,
        }
    }
    pub fn body(&self) -> ApiError {
        let message = match self {
            Self::InvalidInput => "Invalid request.",
            Self::InvalidForm(_) => "Invalid form.",
            Self::UrlRejected(_) => "URL rejected.",
            Self::PayloadTooLarge => "Payload too large.",
            Self::UnsupportedFormat => "Unsupported format.",
            Self::ExtractEmpty(_) => "No text extracted.",
            Self::AuthRequired => "Authentication required.",
            Self::NotFound => "Resource not found.",
            Self::VersionConflict => "Document has a newer version.",
            Self::LicenseForbids => "License does not allow copying.",
            Self::ReviewBlocked => {
                "The contribution failed deterministic review. Read its review findings."
            }
            Self::Internal => "Internal error.",
            Self::ServerUnavailable => "Server unavailable.",
            Self::RateLimited => "Too many requests.",
            Self::HandleUnavailable => "This handle is unavailable.",
            Self::FetchBlocked(_) => {
                "Cannot fetch this page. Try a file upload or an owned browser tab."
            }
            Self::FetchFailed(_) => "The remote page could not be read.",
            Self::SearchUnavailable => {
                "Web search is not configured. Paste a document URL instead."
            }
        };
        let reason = match self {
            Self::InvalidForm(r)
            | Self::UrlRejected(r)
            | Self::ExtractEmpty(r)
            | Self::FetchBlocked(r)
            | Self::FetchFailed(r) => Some((*r).into()),
            _ => None,
        };
        ApiError {
            code: self.code().into(),
            message: message.into(),
            reason,
        }
    }
}
impl std::fmt::Display for Fault {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(self.code())
    }
}
impl std::error::Error for Fault {}
