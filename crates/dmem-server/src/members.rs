use crate::Store;
use dmem_contracts::{Fault, MAX_RESULTS, Template};
use rusqlite::{OptionalExtension, params};
use serde::{Deserialize, Serialize};

pub(crate) const POINTS_PER_APPROVAL: u64 = 20;
// Derive points from the same committed rows that authorize public visibility.
// Inactive, withdrawn and unverified local-owner contributions cannot earn points.
const SCORES:&str="WITH scores AS (
 SELECT a.id AS account_id, COUNT(c.id) AS approved_contributions, COUNT(c.id)*20 AS total_points
 FROM accounts a LEFT JOIN contributions c ON c.owner=a.id AND c.status='approved'
 AND EXISTS(SELECT 1 FROM records r WHERE r.id=c.public_id AND r.owner='@catalog' AND r.kind='template')
 GROUP BY a.id
), ranked AS (
 SELECT p.handle,s.total_points,s.approved_contributions,
 RANK() OVER (ORDER BY s.total_points DESC) AS rank
 FROM scores s JOIN account_profiles p ON p.account_id=s.account_id
 WHERE p.public_profile=1 AND p.handle IS NOT NULL AND s.total_points>0
)";
#[derive(Debug, Serialize)]
pub(crate) struct MemberProfile {
    pub handle: Option<String>,
    pub public_profile: bool,
    pub total_points: u64,
    pub approved_contributions: u64,
    pub overall_rank: Option<u64>,
    pub public_rank: Option<u64>,
    pub points_per_approval: u64,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct ProfileUpdate {
    #[serde(default)]
    pub handle: Option<String>,
    pub public_profile: bool,
}
#[derive(Debug, Serialize)]
pub(crate) struct RankedMember {
    pub handle: String,
    pub total_points: u64,
    pub approved_contributions: u64,
    pub rank: u64,
}
#[derive(Debug, Serialize)]
pub(crate) struct Leaderboard {
    pub items: Vec<RankedMember>,
    pub total: u64,
    pub next_offset: Option<u32>,
    pub points_per_approval: u64,
}
#[derive(Debug, Serialize)]
pub(crate) struct PublicProfile {
    pub handle: String,
    pub total_points: u64,
    pub approved_contributions: u64,
    pub rank: Option<u64>,
    pub templates: Vec<Template>,
}
#[derive(Default, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct BoardQuery {
    #[serde(default)]
    pub offset: u32,
}
fn internal(_: impl std::fmt::Debug) -> Fault {
    Fault::Internal
}
fn normalize_handle(value: &str) -> Result<String, Fault> {
    let value = value.trim().to_ascii_lowercase();
    let bytes = value.as_bytes();
    if !(3..=24).contains(&bytes.len())
        || !bytes[0].is_ascii_alphanumeric()
        || !bytes[bytes.len() - 1].is_ascii_alphanumeric()
        || !bytes
            .iter()
            .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || *c == b'-')
    {
        return Err(Fault::InvalidInput);
    }
    if [
        "admin",
        "administrator",
        "account",
        "accounts",
        "api",
        "auth",
        "help",
        "support",
        "root",
        "system",
        "me",
        "leaderboard",
        "profiles",
        "profile",
        "public",
        "login",
        "signup",
        "signin",
        "www",
    ]
    .contains(&value.as_str())
    {
        return Err(Fault::HandleUnavailable);
    }
    Ok(value)
}
fn own_profile(db: &rusqlite::Connection, owner: &str) -> Result<MemberProfile, Fault> {
    db.query_row(&format!("{SCORES}
 SELECT p.handle,COALESCE(p.public_profile,0),s.total_points,s.approved_contributions,
 CASE WHEN s.total_points>0 THEN 1+(SELECT COUNT(*) FROM scores x WHERE x.total_points>s.total_points) END,
 (SELECT rank FROM ranked WHERE handle=p.handle)
 FROM scores s LEFT JOIN account_profiles p ON p.account_id=s.account_id WHERE s.account_id=?1"),params![owner],|r|Ok(MemberProfile{handle:r.get(0)?,public_profile:r.get(1)?,total_points:r.get(2)?,approved_contributions:r.get(3)?,overall_rank:r.get(4)?,public_rank:r.get(5)?,points_per_approval:POINTS_PER_APPROVAL})).optional().map_err(internal)?.ok_or(Fault::AuthRequired)
}
impl Store {
    pub(crate) fn member_profile(&self, owner: &str) -> Result<MemberProfile, Fault> {
        own_profile(&*self.db.lock().map_err(internal)?, owner)
    }
    pub(crate) fn save_member_profile(
        &self,
        owner: &str,
        input: ProfileUpdate,
        now: u64,
    ) -> Result<MemberProfile, Fault> {
        let handle = input.handle.map(|s| normalize_handle(&s)).transpose()?;
        if input.public_profile && handle.is_none() {
            return Err(Fault::InvalidInput);
        }
        let mut db = self.db.lock().map_err(internal)?;
        let tx = db.transaction().map_err(internal)?;
        // Account existence is required even when an operator supplied a Bearer credential.
        own_profile(&tx, owner)?;
        tx.execute("INSERT INTO account_profiles(account_id,handle,public_profile,updated_at) VALUES(?1,?2,?3,?4)
   ON CONFLICT(account_id) DO UPDATE SET handle=excluded.handle,public_profile=excluded.public_profile,updated_at=excluded.updated_at",params![owner,handle,input.public_profile,now]).map_err(|e|match e{rusqlite::Error::SqliteFailure(e,_) if e.code==rusqlite::ErrorCode::ConstraintViolation=>Fault::HandleUnavailable,_=>Fault::Internal})?;
        let result = own_profile(&tx, owner)?;
        tx.commit().map_err(internal)?;
        Ok(result)
    }
    pub(crate) fn leaderboard(&self, offset: u32) -> Result<Leaderboard, Fault> {
        if offset > 10_000 {
            return Err(Fault::InvalidInput);
        }
        let db = self.db.lock().map_err(internal)?;
        let total: u64 = db
            .query_row(&format!("{SCORES} SELECT COUNT(*) FROM ranked"), [], |r| {
                r.get(0)
            })
            .map_err(internal)?;
        let mut stmt=db.prepare(&format!("{SCORES} SELECT handle,total_points,approved_contributions,rank FROM ranked ORDER BY total_points DESC,handle COLLATE NOCASE LIMIT ?1 OFFSET ?2")).map_err(internal)?;
        let items = stmt
            .query_map(params![MAX_RESULTS as u32, offset], |r| {
                Ok(RankedMember {
                    handle: r.get(0)?,
                    total_points: r.get(1)?,
                    approved_contributions: r.get(2)?,
                    rank: r.get(3)?,
                })
            })
            .map_err(internal)?
            .collect::<Result<Vec<_>, _>>()
            .map_err(internal)?;
        let end = offset as u64 + items.len() as u64;
        let next_offset = if end < total { Some(end as u32) } else { None };
        Ok(Leaderboard {
            items,
            total,
            next_offset,
            points_per_approval: POINTS_PER_APPROVAL,
        })
    }
    pub(crate) fn public_member(&self, handle: &str) -> Result<PublicProfile, Fault> {
        let handle = normalize_handle(handle).map_err(|_| Fault::NotFound)?;
        let db = self.db.lock().map_err(internal)?;
        let row:Option<(String,u64,u64,Option<u64>)>=db.query_row(&format!("{SCORES} SELECT s.account_id,s.total_points,s.approved_contributions,(SELECT rank FROM ranked WHERE handle=p.handle)
   FROM account_profiles p JOIN scores s ON s.account_id=p.account_id WHERE p.handle=?1 AND p.public_profile=1"),params![handle],|r|Ok((r.get(0)?,r.get(1)?,r.get(2)?,r.get(3)?))).optional().map_err(internal)?;
        let (owner, total_points, approved_contributions, rank) = row.ok_or(Fault::NotFound)?;
        let mut stmt=db.prepare("SELECT r.payload FROM contributions c JOIN records r ON r.id=c.public_id AND r.owner='@catalog' AND r.kind='template' WHERE c.owner=?1 AND c.status='approved' ORDER BY c.updated_at DESC,c.id LIMIT ?2").map_err(internal)?;
        let raw = stmt
            .query_map(params![owner, MAX_RESULTS as u32], |r| {
                r.get::<_, String>(0)
            })
            .map_err(internal)?;
        let templates = raw
            .map(|r| serde_json::from_str(&r.map_err(internal)?).map_err(internal))
            .collect::<Result<Vec<Template>, Fault>>()?;
        Ok(PublicProfile {
            handle,
            total_points,
            approved_contributions,
            rank,
            templates,
        })
    }
}
