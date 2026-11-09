CREATE TABLE IF NOT EXISTS admin_email_challenges (
 id_hash TEXT PRIMARY KEY, email TEXT NOT NULL, verifier_hash TEXT NOT NULL,
 created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL,
 delivered INTEGER NOT NULL DEFAULT 0, consumed INTEGER NOT NULL DEFAULT 0,
 attempts INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS admin_email_challenges_email ON admin_email_challenges(email,created_at);
CREATE TABLE IF NOT EXISTS admin_sessions (
 token_hash TEXT PRIMARY KEY, email TEXT NOT NULL, expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS admin_decision_audit (
 contribution_id TEXT PRIMARY KEY REFERENCES contributions(id),
 actor TEXT NOT NULL, decision TEXT NOT NULL CHECK(decision IN ('approve','reject')),
 previous_status TEXT NOT NULL, next_status TEXT NOT NULL, decided_at INTEGER NOT NULL
);
