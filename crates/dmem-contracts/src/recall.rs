use crate::{Form, Provider};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RecallQuery {
    pub url: String,
    #[serde(default)]
    pub doc_type: Option<String>,
    #[serde(default)]
    pub locale: Option<String>,
    #[serde(default)]
    pub provider: Option<String>,
    #[serde(default)]
    pub keywords: Vec<String>,
    #[serde(default)]
    pub kind: Option<String>,
    #[serde(default)]
    pub scope: Option<String>,
    #[serde(default)]
    pub limit: Option<u8>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
#[serde(deny_unknown_fields)]
pub struct RecallForm {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub provider: Option<Provider>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub doc_type: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub locale: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RecallOutline {
    pub level: u8,
    pub text: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HintScope {
    pub url_patterns: Vec<String>,
    pub route: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HintSource {
    pub tier: String,
    pub author_handle: Option<String>,
    pub license: String,
    pub copy_policy: String,
    pub origin: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Hint {
    pub memory_id: String,
    pub version: u32,
    pub kind: String,
    pub title: String,
    pub summary: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub outline: Option<Vec<RecallOutline>>,
    pub form: Form,
    pub scope: HintScope,
    pub source: HintSource,
    pub matched_on: Vec<String>,
    pub locale_match: String,
    pub freshness: String,
    pub warnings: Vec<serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RecallCache {
    pub state: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RecallResult {
    pub schema_version: u32,
    pub untrusted: bool,
    pub framing: String,
    pub canonical_url: String,
    pub form: RecallForm,
    pub hints: Vec<Hint>,
    pub reason: Option<String>,
    pub cache: RecallCache,
}
