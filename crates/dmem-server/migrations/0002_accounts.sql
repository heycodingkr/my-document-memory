CREATE TABLE IF NOT EXISTS accounts (
 id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS email_challenges (
 id_hash TEXT PRIMARY KEY, email TEXT NOT NULL, code_hash TEXT NOT NULL,
 browser_hash TEXT NOT NULL, created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL,
 attempts INTEGER NOT NULL DEFAULT 0, delivered INTEGER NOT NULL DEFAULT 0,
 consumed INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS email_challenges_email ON email_challenges(email,created_at);
CREATE INDEX IF NOT EXISTS email_challenges_browser ON email_challenges(browser_hash,created_at);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id), expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS contributions (
 id TEXT PRIMARY KEY, owner TEXT NOT NULL, template_id TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('pending','approved','rejected','withdrawn')),
 snapshot TEXT NOT NULL, public_id TEXT UNIQUE, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS contributions_owner ON contributions(owner,created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS contributions_active ON contributions(owner,template_id) WHERE status IN ('pending','approved');
