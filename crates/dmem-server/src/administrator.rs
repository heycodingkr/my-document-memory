//! Administrator-only email challenges and sessions. Member credentials have no authority here.
use crate::{
    AuthConfig, Store,
    identity::{constant_eq, secret},
};
use dmem_contracts::Fault;
use rusqlite::{OptionalExtension, params};

pub(crate) const LINK_SECONDS: u64 = 600;
pub(crate) const SESSION_SECONDS: u64 = 2 * 3600;
fn internal(_: impl std::fmt::Debug) -> Fault {
    Fault::Internal
}
fn valid_secret(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|b| b.is_ascii_hexdigit())
}
pub(crate) fn csrf(auth: &AuthConfig, token: &str) -> String {
    auth.digest(&format!("admin-csrf:{token}"))
}
impl Store {
    pub(crate) fn begin_admin_link(
        &self,
        auth: &AuthConfig,
        email: &str,
        challenge: &str,
        verifier: &str,
    ) -> Result<bool, Fault> {
        if !auth.admin_emails.contains(email) {
            return Ok(false);
        }
        let now = auth.now();
        let mut db = self.db.lock().map_err(internal)?;
        let tx = db.transaction().map_err(internal)?;
        let (count, latest): (u64, Option<u64>) = tx.query_row(
            "SELECT count(*),max(created_at) FROM admin_email_challenges WHERE email=?1 AND created_at>=?2",
            params![email, now.saturating_sub(3600)], |r| Ok((r.get(0)?, r.get(1)?)),
        ).map_err(internal)?;
        if count >= 5 || latest.is_some_and(|last| now < last.saturating_add(60)) {
            return Ok(false);
        }
        tx.execute(
            "DELETE FROM admin_email_challenges WHERE created_at<?1",
            params![now.saturating_sub(86400)],
        )
        .map_err(internal)?;
        tx.execute(
            "DELETE FROM admin_sessions WHERE expires_at<=?1",
            params![now],
        )
        .map_err(internal)?;
        tx.execute("INSERT INTO admin_email_challenges(id_hash,email,verifier_hash,created_at,expires_at) VALUES(?1,?2,?3,?4,?5)",
            params![auth.digest(&format!("admin-link:{challenge}")), email, auth.digest(&format!("admin-verifier:{verifier}")), now, now + LINK_SECONDS]).map_err(internal)?;
        tx.commit().map_err(internal)?;
        Ok(true)
    }
    pub(crate) fn admin_link_delivered(
        &self,
        auth: &AuthConfig,
        challenge: &str,
    ) -> Result<(), Fault> {
        self.db
            .lock()
            .map_err(internal)?
            .execute(
                "UPDATE admin_email_challenges SET delivered=1 WHERE id_hash=?1",
                params![auth.digest(&format!("admin-link:{challenge}"))],
            )
            .map_err(internal)?;
        Ok(())
    }
    pub(crate) fn finish_admin_link(
        &self,
        auth: &AuthConfig,
        challenge: &str,
        verifier: &str,
    ) -> Result<(String, String), Fault> {
        if !valid_secret(challenge) || !valid_secret(verifier) {
            return Err(Fault::AuthRequired);
        }
        let now = auth.now();
        let mut db = self.db.lock().map_err(internal)?;
        let tx = db.transaction().map_err(internal)?;
        let id = auth.digest(&format!("admin-link:{challenge}"));
        let row: Option<(String, String, u64, bool, bool, u32)> = tx.query_row(
            "SELECT email,verifier_hash,expires_at,delivered,consumed,attempts FROM admin_email_challenges WHERE id_hash=?1",
            params![id], |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?, r.get(3)?, r.get(4)?, r.get(5)?)),
        ).optional().map_err(internal)?;
        let (email, expected, expires, delivered, consumed, attempts) =
            row.ok_or(Fault::AuthRequired)?;
        if !delivered
            || consumed
            || now >= expires
            || attempts >= 5
            || !auth.admin_emails.contains(&email)
        {
            return Err(Fault::AuthRequired);
        }
        if !constant_eq(
            &expected,
            &auth.digest(&format!("admin-verifier:{verifier}")),
        ) {
            tx.execute(
                "UPDATE admin_email_challenges SET attempts=attempts+1 WHERE id_hash=?1",
                params![id],
            )
            .map_err(internal)?;
            tx.commit().map_err(internal)?;
            return Err(Fault::AuthRequired);
        }
        let token = secret();
        tx.execute(
            "UPDATE admin_email_challenges SET consumed=1 WHERE id_hash=?1 AND consumed=0",
            params![id],
        )
        .map_err(internal)?;
        tx.execute(
            "INSERT INTO admin_sessions(token_hash,email,expires_at) VALUES(?1,?2,?3)",
            params![
                auth.digest(&format!("admin-session:{token}")),
                email,
                now + SESSION_SECONDS
            ],
        )
        .map_err(internal)?;
        tx.commit().map_err(internal)?;
        Ok((email, token))
    }
    pub(crate) fn admin_session(
        &self,
        auth: &AuthConfig,
        token: &str,
    ) -> Result<(String, u64), Fault> {
        if !valid_secret(token) {
            return Err(Fault::AuthRequired);
        }
        let row: Option<(String, u64)> = self
            .db
            .lock()
            .map_err(internal)?
            .query_row(
                "SELECT email,expires_at FROM admin_sessions WHERE token_hash=?1",
                params![auth.digest(&format!("admin-session:{token}"))],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .optional()
            .map_err(internal)?;
        let (email, expires) = row.ok_or(Fault::AuthRequired)?;
        if expires <= auth.now() || !auth.admin_emails.contains(&email) {
            return Err(Fault::AuthRequired);
        }
        Ok((email, expires))
    }
    pub(crate) fn admin_logout(&self, auth: &AuthConfig, token: &str) -> Result<(), Fault> {
        self.db
            .lock()
            .map_err(internal)?
            .execute(
                "DELETE FROM admin_sessions WHERE token_hash=?1",
                params![auth.digest(&format!("admin-session:{token}"))],
            )
            .map_err(internal)?;
        Ok(())
    }
}
