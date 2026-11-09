#![forbid(unsafe_code)]
use dmem_contracts::ApiError;
use reqwest::{Client, Method};
use serde::{Serialize, de::DeserializeOwned};
pub struct DmemClient {
    http: Client,
    base: String,
    token: String,
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
        })
    }
    async fn decode<T: DeserializeOwned>(response: reqwest::Response) -> Result<T, ClientError> {
        if !response.status().is_success() {
            let error = response.json::<ApiError>().await.map_err(unavailable)?;
            return Err(ClientError { code: error.code });
        }
        response.json().await.map_err(unavailable)
    }
    pub async fn get<T: DeserializeOwned>(&self, path: &str) -> Result<T, ClientError> {
        Self::decode(
            self.http
                .get(format!("{}{path}", self.base))
                .bearer_auth(&self.token)
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
            self.http
                .request(method, format!("{}{path}", self.base))
                .bearer_auth(&self.token)
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
            self.http
                .post(format!("{}/v1/sources", self.base))
                .bearer_auth(&self.token)
                .multipart(form)
                .send()
                .await
                .map_err(unavailable)?,
        )
        .await
    }
    pub async fn download(&self, path: &str) -> Result<Vec<u8>, ClientError> {
        let response = self
            .http
            .get(format!("{}{path}", self.base))
            .bearer_auth(&self.token)
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
pub fn safe_id(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= 100
        && id
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-' || b == b'.')
}
