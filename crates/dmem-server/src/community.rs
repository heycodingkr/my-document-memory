use crate::Store;
use dmem_contracts::{Fault, List, Template, Visibility};
use dmem_core::review::{ReviewReport, review_snapshot};
use rusqlite::{OptionalExtension, params};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Contribution {
    pub id: String,
    pub template_id: String,
    pub status: String,
    pub snapshot: Template,
    pub public_id: Option<String>,
    pub created_at: u64,
    pub updated_at: u64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub review: Option<ReviewReport>,
}
#[derive(Default, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct ContributionQueueQuery {
    status: Option<String>,
    limit: Option<u16>,
    cursor: Option<String>,
}
#[derive(Serialize)]
pub(crate) struct ContributionPage {
    items: Vec<Contribution>,
    next_cursor: Option<String>,
}
fn queue_anchor<'a>(cursor: &'a str, status: &str) -> Result<(i64, &'a str), Fault> {
    if cursor.len() > 160 {
        return Err(Fault::InvalidInput);
    }
    let parts: Vec<_> = cursor.split(':').collect();
    if parts.len() != 4
        || parts[0] != "v1"
        || parts[1] != status
        || parts[2].is_empty()
        || !parts[2].bytes().all(|b| b.is_ascii_digit())
        || !parts[3].starts_with("contrib_")
        || parts[3].len() <= 8
        || parts[3].len() > 100
        || !parts[3]
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
    {
        return Err(Fault::InvalidInput);
    }
    Ok((parts[2].parse().map_err(|_| Fault::InvalidInput)?, parts[3]))
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct Submission {
    pub template_id: String,
    pub author: String,
    pub license: String,
    pub rights_confirmed: bool,
}
fn internal(_: impl std::fmt::Debug) -> Fault {
    Fault::Internal
}
fn decode(row: &rusqlite::Row<'_>) -> rusqlite::Result<Contribution> {
    let raw: String = row.get(3)?;
    let snapshot = serde_json::from_str(&raw).map_err(|e| {
        rusqlite::Error::FromSqlConversionFailure(3, rusqlite::types::Type::Text, Box::new(e))
    })?;
    Ok(Contribution {
        id: row.get(0)?,
        template_id: row.get(1)?,
        status: row.get(2)?,
        snapshot,
        public_id: row.get(4)?,
        created_at: row.get(5)?,
        updated_at: row.get(6)?,
        review: None,
    })
}
fn saved_review(db: &rusqlite::Connection, id: &str) -> Result<Option<ReviewReport>, Fault> {
    let raw: Option<String> = db
        .query_row(
            "SELECT report FROM contribution_reviews WHERE contribution_id=?1",
            params![id],
            |row| row.get(0),
        )
        .optional()
        .map_err(internal)?;
    raw.map(|text| serde_json::from_str(&text).map_err(internal))
        .transpose()
}
fn check_snapshot(db: &rusqlite::Connection, c: &Contribution) -> Result<ReviewReport, Fault> {
    // Read all catalog candidates; user-facing search is capped and is not a review oracle.
    let mut stmt = db
        .prepare("SELECT payload FROM records WHERE owner='@catalog' AND kind='template'")
        .map_err(internal)?;
    let rows = stmt
        .query_map([], |r| r.get::<_, String>(0))
        .map_err(internal)?;
    let catalog: Vec<Template> = rows
        .map(|r| serde_json::from_str(&r.map_err(internal)?).map_err(internal))
        .collect::<Result<_, Fault>>()?;
    Ok(review_snapshot(&c.id, &c.snapshot, &catalog))
}
impl Store {
    pub(crate) fn review_contribution(
        &self,
        owner: Option<&str>,
        id: &str,
    ) -> Result<ReviewReport, Fault> {
        let db = self.db.lock().map_err(internal)?;
        let c = db.query_row(
            "SELECT id,template_id,status,snapshot,public_id,created_at,updated_at FROM contributions WHERE id=?1 AND (?2 IS NULL OR owner=?2)",
            params![id, owner], decode,
        ).optional().map_err(internal)?.ok_or(Fault::NotFound)?;
        if let Some(report) = saved_review(&db, id)? {
            return Ok(report);
        }
        let mut report = check_snapshot(&db, &c)?;
        report.stages[5].status = c.status;
        Ok(report)
    }
    pub(crate) fn dashboard(&self, owner: &str) -> Result<serde_json::Value, Fault> {
        let db = self.db.lock().map_err(internal)?;
        let count = |kind: &str| {
            db.query_row(
                "SELECT count(*) FROM records WHERE owner=?1 AND kind=?2",
                params![owner, kind],
                |r| r.get::<_, u64>(0),
            )
            .map_err(internal)
        };
        let contributions: u64 = db
            .query_row(
                "SELECT count(*) FROM contributions WHERE owner=?1",
                params![owner],
                |r| r.get(0),
            )
            .map_err(internal)?;
        Ok(
            serde_json::json!({"templates":count("template")?,"sources":count("source")?,"documents":count("document")?,"contributions":contributions}),
        )
    }
    pub(crate) fn submit(
        &self,
        owner: &str,
        input: Submission,
        now: u64,
    ) -> Result<Contribution, Fault> {
        let author = input.author.trim();
        if !input.rights_confirmed
            || !["CC0-1.0", "CC-BY-4.0"].contains(&input.license.as_str())
            || author.is_empty()
            || author.chars().count() > 80
            || author.contains(['@', '\r', '\n'])
        {
            return Err(Fault::InvalidInput);
        }
        let mut db = self.db.lock().map_err(internal)?;
        let tx = db.transaction().map_err(internal)?;
        let raw: Option<String> = tx
            .query_row(
                "SELECT payload FROM records WHERE id=?1 AND owner=?2 AND kind='template'",
                params![input.template_id, owner],
                |r| r.get(0),
            )
            .optional()
            .map_err(internal)?;
        let mut snapshot: Template =
            serde_json::from_str(&raw.ok_or(Fault::NotFound)?).map_err(internal)?;
        let web_origin = crate::web_store::origin(&tx, owner, &input.template_id)?;
        if web_origin.as_ref().is_some_and(|o| {
            !["CC0-1.0", "CC-BY-4.0"].contains(&o.license.as_str())
                || (o.license == "CC-BY-4.0" && input.license != "CC-BY-4.0")
        }) {
            return Err(Fault::LicenseForbids);
        }
        if (snapshot
            .origin
            .as_ref()
            .is_some_and(|o| o.license == "CC-BY-4.0")
            || snapshot
                .attributions
                .iter()
                .any(|o| o.license == "CC-BY-4.0"))
            && input.license != "CC-BY-4.0"
        {
            return Err(Fault::LicenseForbids);
        }
        let active:bool=tx.query_row("SELECT EXISTS(SELECT 1 FROM contributions WHERE owner=?1 AND template_id=?2 AND status IN ('pending','approved'))",params![owner,input.template_id],|r|r.get(0)).map_err(internal)?;
        if active {
            return Err(Fault::VersionConflict);
        }
        // Only reusable structure enters the snapshot; source files and document content never do.
        snapshot.id = format!("public_{}", Uuid::new_v4().simple());
        snapshot.visibility = Visibility::Public;
        snapshot.author = author.into();
        snapshot.license = input.license;
        if let Some(o) = &snapshot.origin {
            if !crate::store::public_origin(&tx, o)? {
                snapshot.origin = None;
            }
        }
        let lineage = std::mem::take(&mut snapshot.attributions);
        for o in lineage {
            if crate::store::public_origin(&tx, &o)? {
                snapshot.attributions.push(o);
            }
        }
        if snapshot.attributions.len() > 16 {
            return Err(Fault::LicenseForbids);
        }
        let c = Contribution {
            id: format!("contrib_{}", Uuid::new_v4().simple()),
            template_id: input.template_id,
            status: "pending".into(),
            snapshot,
            public_id: None,
            created_at: now,
            updated_at: now,
            review: None,
        };
        tx.execute("INSERT INTO contributions(id,owner,template_id,status,snapshot,created_at,updated_at) VALUES(?1,?2,?3,'pending',?4,?5,?5)",params![c.id,owner,c.template_id,serde_json::to_string(&c.snapshot).map_err(internal)?,now]).map_err(internal)?;
        if let Some(mut origin) = web_origin {
            origin.record_id = c.snapshot.id.clone();
            tx.execute(
                "INSERT INTO web_contribution_origins(contribution_id,payload) VALUES(?1,?2)",
                params![c.id, serde_json::to_string(&origin).map_err(internal)?],
            )
            .map_err(internal)?;
        }
        tx.commit().map_err(internal)?;
        Ok(c)
    }
    pub(crate) fn contribution_queue(
        &self,
        query: ContributionQueueQuery,
    ) -> Result<ContributionPage, Fault> {
        let status = query.status.as_deref().unwrap_or("all");
        let limit = query.limit.unwrap_or(100);
        if !["all", "pending", "approved", "rejected", "withdrawn"].contains(&status)
            || !(1..=100).contains(&limit)
        {
            return Err(Fault::InvalidInput);
        }
        let anchor = query
            .cursor
            .as_deref()
            .map(|c| queue_anchor(c, status))
            .transpose()?;
        let db = self.db.lock().map_err(internal)?;
        let mut stmt = db
            .prepare(
                "SELECT id,template_id,status,snapshot,public_id,created_at,updated_at
             FROM contributions
             WHERE (?1='all' OR status=?1)
               AND (?2 IS NULL OR created_at < ?2 OR (created_at=?2 AND id > ?3))
             ORDER BY created_at DESC,id ASC LIMIT ?4",
            )
            .map_err(internal)?;
        let mut items = stmt
            .query_map(
                params![
                    status,
                    anchor.map(|a| a.0),
                    anchor.map(|a| a.1),
                    i64::from(limit) + 1
                ],
                decode,
            )
            .map_err(internal)?
            .collect::<Result<Vec<_>, _>>()
            .map_err(internal)?;
        let has_more = items.len() > usize::from(limit);
        items.truncate(usize::from(limit));
        let next_cursor = if has_more {
            items
                .last()
                .map(|c| format!("v1:{status}:{}:{}", c.created_at, c.id))
        } else {
            None
        };
        for c in &mut items {
            c.review = saved_review(&db, &c.id)?;
        }
        Ok(ContributionPage { items, next_cursor })
    }
    pub(crate) fn contributions(&self, owner: Option<&str>) -> Result<List<Contribution>, Fault> {
        let db = self.db.lock().map_err(internal)?;
        let mut stmt=db.prepare("SELECT id,template_id,status,snapshot,public_id,created_at,updated_at FROM contributions WHERE (?1 IS NULL OR owner=?1) ORDER BY created_at DESC,id LIMIT 100").map_err(internal)?;
        let mut items = stmt
            .query_map(params![owner], decode)
            .map_err(internal)?
            .collect::<Result<Vec<_>, _>>()
            .map_err(internal)?;
        for c in &mut items {
            c.review = saved_review(&db, &c.id)?;
        }
        Ok(List { items })
    }
    pub(crate) fn withdraw(&self, owner: &str, id: &str, now: u64) -> Result<Contribution, Fault> {
        let mut db = self.db.lock().map_err(internal)?;
        let tx = db.transaction().map_err(internal)?;
        let mut c=tx.query_row("SELECT id,template_id,status,snapshot,public_id,created_at,updated_at FROM contributions WHERE id=?1 AND owner=?2",params![id,owner],decode).optional().map_err(internal)?.ok_or(Fault::NotFound)?;
        if !["pending", "approved"].contains(&c.status.as_str()) {
            return Err(Fault::VersionConflict);
        }
        if let Some(public_id) = &c.public_id {
            tx.execute(
                "DELETE FROM records WHERE id=?1 AND owner='@catalog'",
                params![public_id],
            )
            .map_err(internal)?;
        }
        c.review = saved_review(&tx, id)?;
        c.status = "withdrawn".into();
        c.updated_at = now;
        tx.execute(
            "UPDATE contributions SET status='withdrawn',updated_at=?2 WHERE id=?1",
            params![id, now],
        )
        .map_err(internal)?;
        tx.commit().map_err(internal)?;
        Ok(c)
    }
    pub(crate) fn decide(
        &self,
        id: &str,
        approve: bool,
        now: u64,
        actor: &str,
    ) -> Result<Contribution, Fault> {
        let mut db = self.db.lock().map_err(internal)?;
        let tx = db.transaction().map_err(internal)?;
        let mut c=tx.query_row("SELECT id,template_id,status,snapshot,public_id,created_at,updated_at FROM contributions WHERE id=?1",params![id],decode).optional().map_err(internal)?.ok_or(Fault::NotFound)?;
        if c.status != "pending" {
            return Err(Fault::VersionConflict);
        }
        // Checks and publication share the SQLite transaction, so a changed catalog or
        // original private record cannot bypass review of this immutable snapshot.
        let mut report = check_snapshot(&tx, &c)?;
        if approve && report.verdict == "blocked" {
            return Err(Fault::ReviewBlocked);
        }
        report.decision = Some(if approve { "approve" } else { "reject" }.into());
        report.decided_at = Some(now);
        report.stages[5].status = if approve { "approved" } else { "rejected" }.into();
        tx.execute(
            "INSERT INTO contribution_reviews(contribution_id,report,decided_at) VALUES(?1,?2,?3)",
            params![id, serde_json::to_string(&report).map_err(internal)?, now],
        )
        .map_err(internal)?;
        c.review = Some(report);
        c.status = if approve { "approved" } else { "rejected" }.into();
        c.updated_at = now;
        if approve {
            tx.execute("INSERT INTO records(id,owner,kind,version,payload,updated_at) VALUES(?1,'@catalog','template',?2,?3,?4)",params![c.snapshot.id,c.snapshot.version,serde_json::to_string(&c.snapshot).map_err(internal)?,now]).map_err(internal)?;
            let web_origin: Option<String> = tx
                .query_row(
                    "SELECT payload FROM web_contribution_origins WHERE contribution_id=?1",
                    params![c.id],
                    |r| r.get(0),
                )
                .optional()
                .map_err(internal)?;
            if let Some(raw) = web_origin {
                let value: dmem_contracts::WebOrigin =
                    serde_json::from_str(&raw).map_err(internal)?;
                crate::web_store::save_origin(&tx, "@catalog", &value)?;
            }
            c.public_id = Some(c.snapshot.id.clone());
        }
        tx.execute(
            "UPDATE contributions SET status=?2,public_id=?3,updated_at=?4 WHERE id=?1",
            params![id, c.status, c.public_id, now],
        )
        .map_err(internal)?;
        tx.execute(
            "INSERT INTO admin_decision_audit(contribution_id,actor,decision,previous_status,next_status,decided_at) VALUES(?1,?2,?3,'pending',?4,?5)",
            params![id, actor, if approve { "approve" } else { "reject" }, c.status, now],
        ).map_err(internal)?;
        tx.commit().map_err(internal)?;
        Ok(c)
    }
}
