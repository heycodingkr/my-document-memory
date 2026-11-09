#![forbid(unsafe_code)]
use dmem_contracts::{ApiError, RecallQuery};
use reqwest::{Client, Method};
use serde::{Serialize, de::DeserializeOwned};
pub struct DmemClient {
    http: Client,
    base: String,
    token: String,
    origin: Option<String>,
}
#[derive(Debug)]
pub struct ClientError {
    pub code: String,
}
impl std::fmt::Display for ClientError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.code)
    }
}
impl std::error::Error for ClientError {}
fn unavailable(_: impl std::fmt::Debug) -> ClientError {
    ClientError {
        code: "server_unavailable".into(),
    }
}
impl DmemClient {
    pub async fn capture<T: DeserializeOwned>(&self, body:&impl Serialize, secret:&str)->Result<T,ClientError>{
        use hmac::{Hmac,Mac};use sha2::Sha256;
        if secret.len()<32{return Err(ClientError{code:"capture_not_configured".into()});}
        let bytes=serde_json::to_vec(body).map_err(|_|ClientError{code:"invalid_input".into()})?;
        let time=std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).map_err(unavailable)?.as_secs().to_string();
        let mut mac=Hmac::<Sha256>::new_from_slice(secret.as_bytes()).map_err(unavailable)?;mac.update(time.as_bytes());mac.update(b"\n");mac.update(&bytes);
        let proof=mac.finalize().into_bytes().iter().map(|b|format!("{b:02x}")).collect::<String>();
        Self::decode(self.request(Method::POST,"/v1/web/clip",true).header("content-type","application/json").header("x-dmem-capture-time",time).header("x-dmem-capture-proof",proof).body(bytes).send().await.map_err(unavailable)?).await
    }
    pub fn new(base: &str, token: String) -> Result<Self, ClientError> {
        let parsed = reqwest::Url::parse(base).map_err(unavailable)?;
        if !["http", "https"].contains(&parsed.scheme())
            || !parsed.username().is_empty()
            || parsed.password().is_some()
            || parsed.query().is_some()
            || parsed.fragment().is_some()
            || parsed.path() != "/"
        {
            return Err(ClientError {
                code: "invalid_input".into(),
            });
        }
        let local = parsed
            .host_str()
            .is_some_and(|h| h == "localhost" || h == "127.0.0.1" || h == "[::1]" || h == "::1");
        if parsed.scheme() == "http" && !local {
            return Err(ClientError {
                code: "invalid_input".into(),
            });
        }
        let http = Client::builder()
            .redirect(reqwest::redirect::Policy::none())
            .timeout(std::time::Duration::from_secs(30))
            .build()
            .map_err(unavailable)?;
        Ok(Self {
            http,
            base: base.trim_end_matches('/').into(),
            token,
            origin: None,
        })
    }
    async fn decode<T: DeserializeOwned>(response: reqwest::Response) -> Result<T, ClientError> {
        if !response.status().is_success() {
            let error = response.json::<ApiError>().await.map_err(unavailable)?;
            return Err(ClientError { code: error.code });
        }
        response.json().await.map_err(unavailable)
    }
    pub fn with_origin(mut self, origin: &str) -> Result<Self, ClientError> {
        let parsed = reqwest::Url::parse(origin).map_err(unavailable)?;
        if !["http", "https"].contains(&parsed.scheme())
            || parsed.origin().ascii_serialization() != origin.trim_end_matches('/')
        {
            return Err(ClientError {
                code: "invalid_input".into(),
            });
        }
        self.origin = Some(parsed.origin().ascii_serialization());
        Ok(self)
    }
    fn request(&self, method: Method, path: &str, authenticated: bool) -> reqwest::RequestBuilder {
        let mut request = self.http.request(method, format!("{}{path}", self.base));
        if authenticated && !self.token.is_empty() {
            request = request.bearer_auth(&self.token);
        }
        if let Some(origin) = &self.origin {
            request = request.header(reqwest::header::ORIGIN, origin);
        }
        request
    }
    pub async fn public_get<T: DeserializeOwned>(&self, path: &str) -> Result<T, ClientError> {
        Self::decode(
            self.request(Method::GET, path, false)
                .send()
                .await
                .map_err(unavailable)?,
        )
        .await
    }
    pub async fn get<T: DeserializeOwned>(&self, path: &str) -> Result<T, ClientError> {
        Self::decode(
            self.request(Method::GET, path, true)
                .send()
                .await
                .map_err(unavailable)?,
        )
        .await
    }
    pub async fn send<T: DeserializeOwned>(
        &self,
        method: Method,
        path: &str,
        body: &impl Serialize,
    ) -> Result<T, ClientError> {
        Self::decode(
            self.request(method, path, true)
                .json(body)
                .send()
                .await
                .map_err(unavailable)?,
        )
        .await
    }
    pub async fn post<T: DeserializeOwned>(
        &self,
        path: &str,
        body: &impl Serialize,
    ) -> Result<T, ClientError> {
        self.send(Method::POST, path, body).await
    }
    pub async fn put<T: DeserializeOwned>(
        &self,
        path: &str,
        body: &impl Serialize,
    ) -> Result<T, ClientError> {
        self.send(Method::PUT, path, body).await
    }
    pub async fn upload<T: DeserializeOwned>(
        &self,
        title: String,
        filename: String,
        bytes: Vec<u8>,
    ) -> Result<T, ClientError> {
        let form = reqwest::multipart::Form::new().text("title", title).part(
            "file",
            reqwest::multipart::Part::bytes(bytes).file_name(filename),
        );
        Self::decode(
            self.request(Method::POST, "/v1/sources", true)
                .multipart(form)
                .send()
                .await
                .map_err(unavailable)?,
        )
        .await
    }
    pub async fn download(&self, path: &str) -> Result<Vec<u8>, ClientError> {
        let response = self
            .request(Method::GET, path, true)
            .send()
            .await
            .map_err(unavailable)?;
        if !response.status().is_success() {
            let error = response.json::<ApiError>().await.map_err(unavailable)?;
            return Err(ClientError { code: error.code });
        }
        Ok(response.bytes().await.map_err(unavailable)?.to_vec())
    }
}
pub fn search_path(resource: &str, query: &str) -> String {
    let mut url = reqwest::Url::parse("http://localhost").expect("static URL");
    url.query_pairs_mut().append_pair("q", query);
    format!("/v1/{resource}?{}", url.query().unwrap_or(""))
}
pub fn contribution_queue_path(status: &str, cursor: Option<&str>, limit: u16) -> String {
    let mut url = reqwest::Url::parse("http://localhost").expect("static URL");
    {
        let mut pairs = url.query_pairs_mut();
        pairs.append_pair("status", status).append_pair("limit", &limit.to_string());
        if let Some(cursor) = cursor {
            pairs.append_pair("cursor", cursor);
        }
    }
    format!("/v1/admin/contributions?{}", url.query().unwrap_or(""))
}
pub fn recall_path(q: &RecallQuery) -> String {
    let mut url = reqwest::Url::parse("http://localhost").expect("static URL");
    {
        let mut pairs = url.query_pairs_mut();
        pairs.append_pair("url", &q.url);
        for (name, value) in [
            ("doc_type", q.doc_type.as_deref()),
            ("locale", q.locale.as_deref()),
            ("provider", q.provider.as_deref()),
            ("kind", q.kind.as_deref()),
            ("scope", q.scope.as_deref()),
        ] {
            if let Some(value) = value {
                pairs.append_pair(name, value);
            }
        }
        if !q.keywords.is_empty() {
            pairs.append_pair("keywords", &q.keywords.join(","));
        }
        if let Some(limit) = q.limit {
            pairs.append_pair("limit", &limit.to_string());
        }
    }
    format!("/v1/recall?{}", url.query().unwrap_or(""))
}
#[cfg(test)]
mod tests {
    use super::safe_id;
    #[test]
    fn rejects_url_dot_segments_but_preserves_dotted_seed_ids() {
        assert!(!safe_id("."));
        assert!(!safe_id(".."));
        assert!(safe_id("meeting.minutes.en"));
    }
}
pub fn safe_id(id: &str) -> bool {
    !id.is_empty()
        && !matches!(id, "." | "..")
        && id.len() <= 100
        && id
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-' || b == b'.')
}
