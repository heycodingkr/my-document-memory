use crate::Store;
use dmem_contracts::Fault;
use hmac::{Hmac, Mac};
use rusqlite::{OptionalExtension, params};
use serde::Serialize;
use sha2::Sha256;
use std::{
    future::Future,
    pin::Pin,
    sync::Arc,
    time::{SystemTime, UNIX_EPOCH},
};
use uuid::Uuid;

pub type Delivery = Pin<Box<dyn Future<Output = Result<(), Fault>> + Send>>;
pub trait EmailSender: Send + Sync {
    fn send_code(&self, email: String, code: String, request_id: String) -> Delivery;
    fn send_link(&self, _email: String, _url: String, _request_id: String) -> Delivery {
        Box::pin(async { Err(Fault::ServerUnavailable) })
    }
}
pub struct ResendEmailSender {
    client: reqwest::Client,
    key: String,
    from: String,
}
impl ResendEmailSender {
    pub fn new(key: String, from: String) -> Result<Self, Fault> {
        if key.trim().is_empty() || key.contains(['\r', '\n']) || from.contains(['\r', '\n']) {
            return Err(Fault::InvalidInput);
        }
        let address = from
            .split_once('<')
            .map(|(_, tail)| tail.strip_suffix('>'))
            .unwrap_or(Some(&from))
            .ok_or(Fault::InvalidInput)?;
        normalize_email(address)?;
        let client = reqwest::Client::builder()
            .redirect(reqwest::redirect::Policy::none())
            .timeout(std::time::Duration::from_secs(8))
            .build()
            .map_err(|_| Fault::Internal)?;
        Ok(Self { client, key, from })
    }
    fn deliver(
        &self,
        email: String,
        subject: &str,
        text: String,
        html: Option<String>,
        request_id: String,
    ) -> Delivery {
        let client = self.client.clone();
        let key = self.key.clone();
        let mut body =
            serde_json::json!({"from":self.from,"to":[email],"subject":subject,"text":text});
        if let Some(html) = html {
            body["html"] = serde_json::Value::String(html);
        }
        Box::pin(async move {
            let res = client
                .post("https://api.resend.com/emails")
                .bearer_auth(key)
                .header("Idempotency-Key", format!("dmem-login/{request_id}"))
                .json(&body)
                .send()
                .await
                .map_err(|_| Fault::ServerUnavailable)?;
            if !res.status().is_success() {
                return Err(Fault::ServerUnavailable);
            }
            let receipt: serde_json::Value =
                res.json().await.map_err(|_| Fault::ServerUnavailable)?;
            if receipt["id"].as_str().is_none_or(str::is_empty) {
                return Err(Fault::ServerUnavailable);
            }
            Ok(())
        })
    }
}
impl EmailSender for ResendEmailSender {
    fn send_code(&self, email: String, code: String, request_id: String) -> Delivery {
        self.deliver(email, "Your My Document Memory sign-in code", format!("Your sign-in code: {code}\n\nEnter it in the browser that requested it within 10 minutes. If you did not request this email, you can ignore it."), None, request_id)
    }
    fn send_link(&self, email: String, url: String, request_id: String) -> Delivery {
        let safe_url = url
            .replace('&', "&amp;")
            .replace('"', "&quot;")
            .replace('<', "&lt;")
            .replace('>', "&gt;");
        let text = format!(
            "Sign in to My Document Memory\n\nOpen this link to continue to your private space:\n{url}\n\nThis link expires in 10 minutes and can be used once. If you did not request it, you can ignore this email."
        );
        let html = format!(
            "<div style=\"font-family:Arial,sans-serif;line-height:1.7;color:#263e32;max-width:520px;margin:40px auto\"><p>MY DOCUMENT MEMORY</p><h1>Your next document starts here.</h1><p>Continue to your private templates, references, and documents.</p><p><a href=\"{safe_url}\" style=\"display:inline-block;padding:12px 22px;background:#284f3c;color:white;border-radius:6px;text-decoration:none\">Sign in to my space</a></p><p>This link expires in 10 minutes and can be used once.</p><p>If you did not request it, you can ignore this email.</p></div>"
        );
        self.deliver(
            email,
            "Sign in to My Document Memory",
            text,
            Some(html),
            request_id,
        )
    }
}
#[derive(Clone)]
pub struct AuthConfig {
    pub(crate) secret: String,
    pub mailer: Option<Arc<dyn EmailSender>>,
    pub secure_cookies: bool,
    pub admin_token: Option<String>,
    pub clock: Arc<dyn Fn() -> u64 + Send + Sync>,
}
impl Default for AuthConfig {
    fn default() -> Self {
        Self {
            secret: format!("{}{}", Uuid::new_v4().simple(), Uuid::new_v4().simple()),
            mailer: None,
            secure_cookies: false,
            admin_token: None,
            clock: Arc::new(|| {
                SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap_or_default()
                    .as_secs()
            }),
        }
    }
}
impl AuthConfig {
    pub fn new(secret: String, mailer: Arc<dyn EmailSender>) -> Result<Self, Fault> {
        if secret.len() < 32 {
            return Err(Fault::InvalidInput);
        }
        Ok(Self {
            secret,
            mailer: Some(mailer),
            ..Self::default()
        })
    }
    pub(crate) fn now(&self) -> u64 {
        (self.clock)()
    }
    pub(crate) fn digest(&self, value: &str) -> String {
        let mut mac = Hmac::<Sha256>::new_from_slice(self.secret.as_bytes())
            .expect("HMAC accepts all key lengths");
        mac.update(value.as_bytes());
        format!("{:x}", mac.finalize().into_bytes())
    }
    pub(crate) fn csrf(&self, session: &str) -> String {
        self.digest(&format!("csrf:{session}"))
    }
    pub(crate) fn cookie(&self, name: &str, value: &str, age: u64) -> String {
        format!(
            "{name}={value}; Path=/; HttpOnly; SameSite=Lax; Max-Age={age}{}",
            if self.secure_cookies { "; Secure" } else { "" }
        )
    }
}
pub(crate) fn secret() -> String {
    format!("{}{}", Uuid::new_v4().simple(), Uuid::new_v4().simple())
}
pub(crate) fn normalize_email(value: &str) -> Result<String, Fault> {
    let value = value.trim().to_ascii_lowercase();
    if value.len() > 254 || !value.is_ascii() || value.bytes().any(|b| b <= 32 || b == 127) {
        return Err(Fault::InvalidInput);
    }
    let (local, domain) = value.split_once('@').ok_or(Fault::InvalidInput)?;
    if local.is_empty()
        || local.len() > 64
        || local.starts_with('.')
        || local.ends_with('.')
        || local.contains("..")
        || !local
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b".!#$%&'*+-/=?^_`{|}~".contains(&b))
        || !domain.contains('.')
        || domain.split('.').any(|s| {
            s.is_empty()
                || s.len() > 63
                || s.starts_with('-')
                || s.ends_with('-')
                || !s.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-')
        })
    {
        return Err(Fault::InvalidInput);
    }
    Ok(value)
}
#[derive(Debug, Clone, Serialize)]
pub struct Account {
    pub id: String,
    pub email: String,
}
impl Store {
    pub(crate) fn begin_email(
        &self,
        auth: &AuthConfig,
        email: &str,
        browser: &str,
        challenge: &str,
        code: &str,
    ) -> Result<(), Fault> {
        let mut db = self.db.lock().map_err(|_| Fault::Internal)?;
        let tx = db.transaction().map_err(|_| Fault::Internal)?;
        let now = auth.now();
        let browser = auth.digest(&format!("browser:{browser}"));
        let recent:(u64,u64)=tx.query_row("SELECT COUNT(*), COALESCE(MAX(created_at),0) FROM email_challenges WHERE email=?1 AND created_at>?2",params![email,now.saturating_sub(3600)],|r|Ok((r.get(0)?,r.get(1)?))).map_err(|_|Fault::Internal)?;
        let browser_count: u64 = tx
            .query_row(
                "SELECT COUNT(*) FROM email_challenges WHERE browser_hash=?1 AND created_at>?2",
                params![browser, now.saturating_sub(3600)],
                |r| r.get(0),
            )
            .map_err(|_| Fault::Internal)?;
        // A global cap also bounds requests made with freshly cleared cookies.
        let global_count: u64 = tx
            .query_row(
                "SELECT COUNT(*) FROM email_challenges WHERE created_at>?1",
                params![now.saturating_sub(3600)],
                |r| r.get(0),
            )
            .map_err(|_| Fault::Internal)?;
        if (recent.0 > 0 && recent.1.saturating_add(60) > now)
            || recent.0 >= 10
            || browser_count >= 20
            || global_count >= 200
        {
            return Err(Fault::RateLimited);
        }
        // Only invalidate this browser's prior codes; another device cannot cancel a sign-in.
        tx.execute(
            "UPDATE email_challenges SET consumed=1 WHERE browser_hash=?1",
            params![browser],
        )
        .map_err(|_| Fault::Internal)?;
        tx.execute(
            "DELETE FROM email_challenges WHERE created_at<?1",
            params![now.saturating_sub(86400)],
        )
        .map_err(|_| Fault::Internal)?;
        tx.execute("INSERT INTO email_challenges(id_hash,email,code_hash,browser_hash,created_at,expires_at) VALUES(?1,?2,?3,?4,?5,?6)",params![auth.digest(challenge),email,auth.digest(&format!("code:{challenge}:{code}")),browser,now,now+600]).map_err(|_|Fault::Internal)?;
        tx.commit().map_err(|_| Fault::Internal)
    }
    pub(crate) fn email_delivered(
        &self,
        auth: &AuthConfig,
        challenge: &str,
        delivered: bool,
    ) -> Result<(), Fault> {
        self.db
            .lock()
            .map_err(|_| Fault::Internal)?
            .execute(
                "UPDATE email_challenges SET delivered=?2 WHERE id_hash=?1",
                params![auth.digest(challenge), delivered],
            )
            .map_err(|_| Fault::Internal)?;
        Ok(())
    }
    pub(crate) fn finish_email(
        &self,
        auth: &AuthConfig,
        challenge: &str,
        browser: &str,
        code: &str,
    ) -> Result<(Account, String), Fault> {
        self.finish_login(auth, challenge, Some(browser), code)
    }
    pub(crate) fn finish_email_link(
        &self,
        auth: &AuthConfig,
        challenge: &str,
        verifier: &str,
    ) -> Result<(Account, String), Fault> {
        self.finish_login(auth, challenge, None, verifier)
    }
    fn finish_login(
        &self,
        auth: &AuthConfig,
        challenge: &str,
        browser: Option<&str>,
        code: &str,
    ) -> Result<(Account, String), Fault> {
        let mut db = self.db.lock().map_err(|_| Fault::Internal)?;
        let tx = db.transaction().map_err(|_| Fault::Internal)?;
        let row:Option<(String,String,String,u64,u32,bool,bool)>=tx.query_row("SELECT email,code_hash,browser_hash,expires_at,attempts,delivered,consumed FROM email_challenges WHERE id_hash=?1",params![auth.digest(challenge)],|r|Ok((r.get(0)?,r.get(1)?,r.get(2)?,r.get(3)?,r.get(4)?,r.get(5)?,r.get(6)?))).optional().map_err(|_|Fault::Internal)?;
        let Some((email, expected, bound, expires, attempts, delivered, consumed)) = row else {
            return Err(Fault::AuthRequired);
        };
        if consumed
            || !delivered
            || expires <= auth.now()
            || attempts >= 5
            || browser.is_some_and(|value| {
                !constant_eq(&bound, &auth.digest(&format!("browser:{value}")))
            })
        {
            return Err(Fault::AuthRequired);
        }
        tx.execute(
            "UPDATE email_challenges SET attempts=attempts+1 WHERE id_hash=?1",
            params![auth.digest(challenge)],
        )
        .map_err(|_| Fault::Internal)?;
        let valid_shape = if browser.is_some() {
            code.len() == 6 && code.bytes().all(|b| b.is_ascii_digit())
        } else {
            code.len() == 64 && code.bytes().all(|b| b.is_ascii_hexdigit())
        };
        if !valid_shape
            || !constant_eq(&expected, &auth.digest(&format!("code:{challenge}:{code}")))
        {
            tx.commit().map_err(|_| Fault::Internal)?;
            return Err(Fault::AuthRequired);
        }
        tx.execute(
            "UPDATE email_challenges SET consumed=1 WHERE id_hash=?1",
            params![auth.digest(challenge)],
        )
        .map_err(|_| Fault::Internal)?;
        let account = Account {
            id: format!("acct_{}", Uuid::new_v4().simple()),
            email,
        };
        tx.execute(
            "INSERT OR IGNORE INTO accounts(id,email,created_at) VALUES(?1,?2,?3)",
            params![account.id, account.email, auth.now()],
        )
        .map_err(|_| Fault::Internal)?;
        let account = tx
            .query_row(
                "SELECT id,email FROM accounts WHERE email=?1",
                params![account.email],
                |r| {
                    Ok(Account {
                        id: r.get(0)?,
                        email: r.get(1)?,
                    })
                },
            )
            .map_err(|_| Fault::Internal)?;
        let token = secret();
        tx.execute(
            "DELETE FROM sessions WHERE expires_at<=?1",
            params![auth.now()],
        )
        .map_err(|_| Fault::Internal)?;
        tx.execute(
            "INSERT INTO sessions(token_hash,account_id,expires_at) VALUES(?1,?2,?3)",
            params![auth.digest(&token), account.id, auth.now() + 30 * 86400],
        )
        .map_err(|_| Fault::Internal)?;
        tx.commit().map_err(|_| Fault::Internal)?;
        Ok((account, token))
    }
    pub(crate) fn session(&self, auth: &AuthConfig, token: &str) -> Result<Account, Fault> {
        self.db.lock().map_err(|_|Fault::Internal)?.query_row("SELECT a.id,a.email FROM sessions s JOIN accounts a ON a.id=s.account_id WHERE s.token_hash=?1 AND s.expires_at>?2",params![auth.digest(token),auth.now()],|r|Ok(Account{id:r.get(0)?,email:r.get(1)?})).optional().map_err(|_|Fault::Internal)?.ok_or(Fault::AuthRequired)
    }
    pub(crate) fn logout(&self, auth: &AuthConfig, token: &str) -> Result<(), Fault> {
        self.db
            .lock()
            .map_err(|_| Fault::Internal)?
            .execute(
                "DELETE FROM sessions WHERE token_hash=?1",
                params![auth.digest(token)],
            )
            .map_err(|_| Fault::Internal)?;
        Ok(())
    }
}
pub(crate) fn constant_eq(a: &str, b: &str) -> bool {
    if a.len() != b.len() {
        return false;
    }
    a.bytes()
        .zip(b.bytes())
        .fold(0u8, |diff, (a, b)| diff | (a ^ b))
        == 0
}
