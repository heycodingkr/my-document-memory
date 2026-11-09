//! Bounded remote intake. A resolved destination is pinned before every connection.
use dmem_contracts::*;
use dmem_core::{
    normalize_form, normalize_url,
    web::{WebExtract, clean, document_parts, parse_html, public_ip, safe_fetch_url},
};
use hmac::{Hmac, Mac};
use reqwest::redirect::Policy;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{
    collections::{HashMap, VecDeque},
    net::SocketAddr,
    sync::Mutex,
    time::{Duration, SystemTime, UNIX_EPOCH},
};
use tokio::sync::Semaphore;
use url::Url;
use uuid::Uuid;

pub(crate) fn now() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}
#[derive(Clone, Default)]
pub struct WebConfig {
    pub search_key: Option<String>,
    pub capture_secret: Option<String>,
    fixture: Option<SocketAddr>,
    pub preview_ttl: Option<u64>,
}
impl WebConfig {
    pub fn from_env() -> Result<Self, Fault> {
        let config = Self {
            search_key: std::env::var("DMEM_BRAVE_API_KEY")
                .ok()
                .filter(|s| !s.is_empty()),
            capture_secret: std::env::var("DMEM_CAPTURE_SECRET")
                .ok()
                .filter(|s| !s.is_empty()),
            ..Self::default()
        };
        if config.capture_secret.as_ref().is_some_and(|s| s.len() < 32) {
            return Err(Fault::InvalidInput);
        }
        Ok(config)
    }
    /// Explicit dependency injection for disposable loopback fixtures; never enabled by an input URL.
    pub fn isolated_fixture(address: SocketAddr) -> Self {
        assert!(address.ip().is_loopback());
        Self {
            fixture: Some(address),
            ..Self::default()
        }
    }
    fn is_fixture(&self, url: &Url) -> bool {
        self.fixture.is_some_and(|a| {
            url.scheme() == "http"
                && url.port_or_known_default() == Some(a.port())
                && match url.host() {
                    Some(url::Host::Ipv4(ip)) => std::net::IpAddr::V4(ip) == a.ip(),
                    Some(url::Host::Ipv6(ip)) => std::net::IpAddr::V6(ip) == a.ip(),
                    _ => false,
                }
        })
    }
    fn logical_url(&self, url: &Url) -> Url {
        if self.is_fixture(url) {
            for (prefix, host) in [
                ("/p/google-docs", "https://docs.google.com"),
                ("/p/google-slides", "https://docs.google.com"),
            ] {
                if let Some(path) = url.path().strip_prefix(prefix) {
                    if path.starts_with('/') {
                        if let Ok(logical) = Url::parse(&format!("{host}{path}")) {
                            return logical;
                        }
                    }
                }
            }
        }
        url.clone()
    }
    fn target(&self, url: &Url) -> Result<Url, Fault> {
        if !url.username().is_empty() || url.password().is_some() {
            return Err(Fault::FetchBlocked("credentials"));
        }
        if self.is_fixture(url) {
            return Ok(url.clone());
        }
        if matches!(url.host(), Some(url::Host::Ipv4(_) | url::Host::Ipv6(_))) {
            return Err(Fault::FetchBlocked("private_address"));
        }
        let mut checked = safe_fetch_url(url.as_str())?;
        checked.set_query(url.query());
        Ok(checked)
    }
    pub(crate) fn canonical(&self, url: &Url) -> Result<(String, Provider), Fault> {
        let logical = self.logical_url(url);
        if logical.as_str() != url.as_str() {
            let safe = normalize_url(logical.as_str())?;
            return Ok((safe.pattern, safe.provider));
        }
        if self.is_fixture(url) {
            let safe = normalize_url(&format!("https://fixture.example{}", url.path()))?;
            return Ok((safe.pattern, safe.provider));
        }
        let normalized = normalize_url(url.as_str())?;
        Ok((normalized.pattern, normalized.provider))
    }
}
#[derive(Clone)]
pub(crate) struct Snapshot {
    pub preview: WebPreview,
    pub page: WebExtract,
}
pub(crate) struct WebService {
    pub config: WebConfig,
    snapshots: Mutex<HashMap<String, (String, Snapshot)>>,
    requests: Mutex<HashMap<String, VecDeque<u64>>>,
    in_flight: Semaphore,
}
impl WebService {
    pub fn new(config: WebConfig) -> Self {
        Self {
            config,
            snapshots: Mutex::new(HashMap::new()),
            requests: Mutex::new(HashMap::new()),
            in_flight: Semaphore::new(4),
        }
    }
    pub fn admit(&self, owner: &str) -> Result<(), Fault> {
        let time = now();
        let mut all = self.requests.lock().map_err(|_| Fault::Internal)?;
        all.retain(|_, r| r.back().is_some_and(|t| time.saturating_sub(*t) < 60));
        if all.len() >= 1024 && !all.contains_key(owner) {
            return Err(Fault::RateLimited);
        }
        let requests = all.entry(owner.into()).or_default();
        while requests
            .front()
            .is_some_and(|t| time.saturating_sub(*t) >= 60)
        {
            requests.pop_front();
        }
        if requests.len() >= 30 {
            return Err(Fault::RateLimited);
        }
        requests.push_back(time);
        Ok(())
    }
    pub fn snapshot(&self, owner: &str, id: &str) -> Result<Snapshot, Fault> {
        let mut cache = self.snapshots.lock().map_err(|_| Fault::Internal)?;
        cache.retain(|_, (_, s)| s.preview.expires_at > now());
        cache
            .get(id)
            .filter(|(who, _)| who == owner)
            .map(|(_, s)| s.clone())
            .ok_or(Fault::NotFound)
    }
    pub fn prepare(&self, url: &Url, page: WebExtract) -> Result<Snapshot, Fault> {
        let (canonical_url, detected_provider) = self.config.canonical(url)?;
        let provider = match detected_provider {
            Provider::Other => Provider::Html,
            p => p,
        };
        let spelling = page.locale.replace('_', "-");
        let locale = [
            "en-US", "en-GB", "ko-KR", "ja-JP", "de-DE", "fr-FR", "zh-CN",
        ]
        .into_iter()
        .find(|s| s.eq_ignore_ascii_case(&spelling))
        .unwrap_or_else(|| match spelling.split('-').next().unwrap_or("") {
            "ko" => "ko-KR",
            "ja" => "ja-JP",
            "de" => "de-DE",
            "fr" => "fr-FR",
            "zh" => "zh-CN",
            _ => "en-US",
        });
        let title = page.title.to_lowercase();
        let doc_type = if provider == Provider::GoogleSlides {
            "report_deck"
        } else if ["resume", "이력서", "履歴書"]
            .iter()
            .any(|s| title.contains(s))
        {
            "resume"
        } else {
            "report"
        };
        let form = normalize_form(FormInput {
            provider: serde_json::to_value(provider)
                .map_err(|_| Fault::Internal)?
                .as_str()
                .unwrap_or("html")
                .into(),
            doc_type: doc_type.into(),
            locale: locale.into(),
            region: None,
            variant: None,
            page: None,
        })?;
        let content_hash = format!(
            "{:x}",
            Sha256::digest(serde_json::to_vec(&page).map_err(|_| Fault::Internal)?)
        );
        let time = now();
        let preview = WebPreview {
            preview_id: format!("preview_{}", Uuid::new_v4().simple()),
            canonical_url,
            title: page.title.clone(),
            provider,
            form,
            outline: page.outline.clone(),
            table_headers: page.table_headers.clone(),
            license: page.license.clone(),
            copy_policy_default: if page.full_copy_allowed() {
                CopyMode::Full
            } else {
                CopyMode::StructureOnly
            },
            content_hash,
            warnings: page.warnings.clone(),
            fetched_at: time,
            expires_at: time
                + self
                    .config
                    .preview_ttl
                    .unwrap_or(PREVIEW_TTL)
                    .min(PREVIEW_TTL),
            untrusted: true,
        };
        Ok(Snapshot { preview, page })
    }
    pub async fn preview(&self, owner: &str, input: WebPreviewInput) -> Result<WebPreview, Fault> {
        self.admit(owner)?;
        let _permit = self
            .in_flight
            .try_acquire()
            .map_err(|_| Fault::RateLimited)?;
        let mut url = Url::parse(&input.url).map_err(|_| Fault::FetchBlocked("url"))?;
        if input.url.len() > 2048 || input.url.chars().any(char::is_control) {
            return Err(Fault::InvalidInput);
        }
        url.set_query(None);
        url.set_fragment(None);
        self.config.target(&url)?;
        self.config.canonical(&url)?;
        let logical = self.config.logical_url(&url);
        let mut target = logical.clone();
        let mut file = None;
        if logical.host_str() == Some("docs.google.com") {
            let parts: Vec<_> = logical.path_segments().into_iter().flatten().collect();
            if parts.len() >= 3
                && parts[1] == "d"
                && parts[2]
                    .bytes()
                    .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
            {
                match parts[0] {
                    "document" => {
                        target.set_path(&format!("/document/d/{}/export", parts[2]));
                        target.set_query(Some("format=docx"));
                        file = Some("document.docx");
                    }
                    "presentation" => {
                        target.set_path(&format!("/presentation/d/{}/export", parts[2]));
                        target.set_query(Some("format=pptx"));
                        file = Some("slides.pptx");
                    }
                    _ => {}
                }
            }
        }
        if self.config.is_fixture(&url) && logical.as_str() != url.as_str() {
            let path = target.path().to_owned();
            let query = target.query().map(String::from);
            target = url.clone();
            let prefix = if logical.path().starts_with("/presentation/") {
                "/p/google-slides"
            } else {
                "/p/google-docs"
            };
            target.set_path(&format!("{prefix}{path}"));
            target.set_query(query.as_deref());
        }
        let (bytes, mime) = self.fetch(target, None).await?;
        let page = if let Some(filename) = file {
            if mime.contains("text/html") {
                return Err(Fault::FetchBlocked("login_required"));
            }
            let extracted = dmem_core::extract(filename, &bytes)?;
            let outline = extracted
                .blocks
                .iter()
                .filter_map(|b| {
                    if let Block::Heading { text, .. } = b {
                        Some(text.clone())
                    } else {
                        None
                    }
                })
                .chain(extracted.slides.iter().map(|s| s.title.clone()))
                .collect();
            WebExtract {
                title: if filename.ends_with("pptx") {
                    extracted
                        .slides
                        .first()
                        .map(|s| s.title.clone())
                        .unwrap_or_else(|| "Imported slides".into())
                } else {
                    "Imported Google document".into()
                },
                locale: "en-US".into(),
                outline,
                table_headers: vec![],
                paragraphs: extracted.spans.iter().map(|s| s.text.clone()).collect(),
                parts: document_parts(&extracted.blocks, &extracted.slides),
                license: "unknown".into(),
                warnings: vec!["styles_approximated".into()],
            }
            .sanitize()?
        } else if mime == "text/html" {
            parse_html(
                std::str::from_utf8(&bytes).map_err(|_| Fault::FetchBlocked("content_type"))?,
            )?
        } else if mime == "text/plain" || mime == "text/markdown" {
            let extracted = dmem_core::extract(
                if mime == "text/markdown" {
                    "web.md"
                } else {
                    "web.txt"
                },
                &bytes,
            )?;
            WebExtract {
                title: "Imported document".into(),
                locale: "en-US".into(),
                outline: extracted
                    .blocks
                    .iter()
                    .filter_map(|b| {
                        if let Block::Heading { text, .. } = b {
                            Some(text.clone())
                        } else {
                            None
                        }
                    })
                    .collect(),
                table_headers: vec![],
                paragraphs: extracted.spans.iter().map(|s| s.text.clone()).collect(),
                parts: document_parts(&extracted.blocks, &extracted.slides),
                license: "unknown".into(),
                warnings: vec![],
            }
            .sanitize()?
        } else {
            return Err(Fault::FetchBlocked("content_type"));
        };
        let snapshot = self.prepare(&url, page)?;
        let result = snapshot.preview.clone();
        let mut cache = self.snapshots.lock().map_err(|_| Fault::Internal)?;
        cache.retain(|_, (_, s)| s.preview.expires_at > now());
        if cache.len() >= 64 || cache.values().filter(|(who, _)| who == owner).count() >= 16 {
            return Err(Fault::RateLimited);
        }
        cache.insert(result.preview_id.clone(), (owner.into(), snapshot));
        Ok(result)
    }
    async fn fetch(
        &self,
        mut url: Url,
        search_key: Option<&str>,
    ) -> Result<(Vec<u8>, String), Fault> {
        tokio::time::timeout(Duration::from_secs(10), async {
            for hop in 0..=3 {
                url = self.config.target(&url)?;
                let host = url.host_str().ok_or(Fault::FetchBlocked("url"))?.to_owned();
                let port = url
                    .port_or_known_default()
                    .ok_or(Fault::FetchBlocked("port"))?;
                let addresses: Vec<_> = tokio::net::lookup_host((host.as_str(), port))
                    .await
                    .map_err(|_| Fault::FetchFailed("dns"))?
                    .collect();
                if addresses.is_empty() {
                    return Err(Fault::FetchFailed("dns"));
                }
                let fixture = self
                    .config
                    .fixture
                    .is_some_and(|a| addresses.iter().all(|v| *v == a) && url.scheme() == "http");
                if !fixture && addresses.iter().any(|a| !public_ip(a.ip())) {
                    return Err(Fault::FetchBlocked("private_address"));
                }
                let client = reqwest::Client::builder()
                    .redirect(Policy::none())
                    .no_proxy()
                    .referer(false)
                    .user_agent("dmem/0.1")
                    .timeout(Duration::from_secs(10))
                    .resolve_to_addrs(&host, &addresses)
                    .build()
                    .map_err(|_| Fault::Internal)?;
                let mut request = client.get(url.clone());
                if let Some(key) = search_key {
                    request = request.header("X-Subscription-Token", key);
                }
                let mut response = request
                    .send()
                    .await
                    .map_err(|_| Fault::FetchFailed("connection"))?;
                if !response
                    .remote_addr()
                    .is_some_and(|address| addresses.contains(&address))
                {
                    return Err(Fault::FetchBlocked("private_address"));
                }
                if response.status().is_redirection() {
                    if hop == 3 || search_key.is_some() {
                        return Err(Fault::FetchBlocked("redirect_limit"));
                    }
                    let location = response
                        .headers()
                        .get("location")
                        .and_then(|v| v.to_str().ok())
                        .ok_or(Fault::FetchFailed("redirect"))?;
                    url = url.join(location).map_err(|_| Fault::FetchBlocked("url"))?;
                    if url
                        .host_str()
                        .is_some_and(|h| h == "accounts.google.com" || h.starts_with("login."))
                    {
                        return Err(Fault::FetchBlocked("login_required"));
                    }
                    continue;
                }
                if [401, 403].contains(&response.status().as_u16()) {
                    return Err(Fault::FetchBlocked("login_required"));
                }
                if !response.status().is_success() {
                    return Err(Fault::FetchFailed("status"));
                }
                if response
                    .headers()
                    .get("x-robots-tag")
                    .is_some_and(|v| v.to_str().unwrap_or("").to_lowercase().contains("noai"))
                {
                    return Err(Fault::FetchBlocked("signal_noai"));
                }
                if response.headers().contains_key("content-encoding") {
                    return Err(Fault::FetchBlocked("content_type"));
                }
                if response
                    .content_length()
                    .is_some_and(|n| n > WEB_MAX_BYTES as u64)
                {
                    return Err(Fault::FetchBlocked("size"));
                }
                let mime = response
                    .headers()
                    .get("content-type")
                    .and_then(|v| v.to_str().ok())
                    .unwrap_or("")
                    .split(';')
                    .next()
                    .unwrap_or("")
                    .trim()
                    .to_lowercase();
                let mut data = Vec::new();
                while let Some(chunk) = response
                    .chunk()
                    .await
                    .map_err(|_| Fault::FetchFailed("connection"))?
                {
                    if data.len() + chunk.len() > WEB_MAX_BYTES {
                        return Err(Fault::FetchBlocked("size"));
                    }
                    data.extend_from_slice(&chunk);
                }
                return Ok((data, mime));
            }
            Err(Fault::FetchBlocked("redirect_limit"))
        })
        .await
        .map_err(|_| Fault::FetchBlocked("timeout"))?
    }
    pub async fn search(
        &self,
        owner: &str,
        input: WebSearchInput,
    ) -> Result<WebSearchResult, Fault> {
        self.admit(owner)?;
        if input.query.trim().is_empty()
            || input.query.chars().count() > 200
            || input.limit.is_some_and(|n| n == 0 || n > 10)
            || dmem_core::review::contains_secret(&input.query)
        {
            return Err(Fault::InvalidInput);
        }
        let key = self
            .config
            .search_key
            .as_deref()
            .ok_or(Fault::SearchUnavailable)?;
        let endpoint = self
            .config
            .fixture
            .map(|a| format!("http://{a}/search"))
            .unwrap_or_else(|| "https://api.search.brave.com/res/v1/web/search".into());
        let mut url = Url::parse(&endpoint).map_err(|_| Fault::Internal)?;
        let locale = input
            .locale
            .map(|locale| {
                normalize_form(FormInput {
                    provider: "html".into(),
                    doc_type: "report".into(),
                    locale,
                    region: None,
                    variant: None,
                    page: None,
                })
            })
            .transpose()?;
        {
            let mut q = url.query_pairs_mut();
            q.append_pair("q", &input.query)
                .append_pair("count", &input.limit.unwrap_or(5).to_string());
            if let Some(form) = locale {
                q.append_pair("search_lang", form.locale.split('-').next().unwrap_or("en"));
                if let Some(country) = form.region {
                    q.append_pair("country", &country);
                }
            }
        }
        let _permit = self
            .in_flight
            .try_acquire()
            .map_err(|_| Fault::RateLimited)?;
        let (bytes, _) = self.fetch(url, Some(key)).await?;
        let result: Value =
            serde_json::from_slice(&bytes).map_err(|_| Fault::FetchFailed("content_type"))?;
        let items = result["web"]["results"]
            .as_array()
            .into_iter()
            .flatten()
            .filter_map(|r| {
                let url = safe_fetch_url(r["url"].as_str()?).ok()?;
                if normalize_url(url.as_str()).is_err()
                    || dmem_core::review::contains_secret(&r.to_string())
                    || dmem_core::review::contains_injection(&r.to_string())
                {
                    return None;
                }
                Some(WebSearchHit {
                    title: clean(r["title"].as_str().unwrap_or("Document"))
                        .chars()
                        .take(120)
                        .collect(),
                    url: url.to_string(),
                    snippet: clean(r["description"].as_str().unwrap_or(""))
                        .chars()
                        .take(240)
                        .collect(),
                })
            })
            .take(input.limit.unwrap_or(5))
            .collect();
        Ok(WebSearchResult {
            items,
            untrusted: true,
        })
    }
    pub fn capture_provenance(
        &self,
        headers: &axum::http::HeaderMap,
        body: &[u8],
    ) -> Result<&'static str, Fault> {
        let proof = headers.get("x-dmem-capture-proof");
        let timestamp = headers.get("x-dmem-capture-time");
        if proof.is_none() && timestamp.is_none() {
            return Ok("claimed");
        }
        let secret = self
            .config
            .capture_secret
            .as_deref()
            .filter(|s| s.len() >= 32)
            .ok_or(Fault::FetchBlocked("capture_not_configured"))?;
        let time = timestamp
            .and_then(|v| v.to_str().ok())
            .ok_or(Fault::AuthRequired)?;
        if time
            .parse::<u64>()
            .ok()
            .is_none_or(|t| t > now() + 5 || now().saturating_sub(t) > 60)
        {
            return Err(Fault::AuthRequired);
        }
        let proof = proof
            .and_then(|v| v.to_str().ok())
            .filter(|s| s.len() == 64 && s.bytes().all(|b| b.is_ascii_hexdigit()))
            .ok_or(Fault::AuthRequired)?;
        let bytes: Vec<u8> = (0..proof.len())
            .step_by(2)
            .map(|n| u8::from_str_radix(&proof[n..n + 2], 16).map_err(|_| Fault::AuthRequired))
            .collect::<Result<_, _>>()?;
        let mut mac =
            Hmac::<Sha256>::new_from_slice(secret.as_bytes()).map_err(|_| Fault::Internal)?;
        mac.update(time.as_bytes());
        mac.update(b"\n");
        mac.update(body);
        mac.verify_slice(&bytes).map_err(|_| Fault::AuthRequired)?;
        Ok("captured")
    }
}
