CREATE TABLE IF NOT EXISTS web_origins (
 record_id TEXT PRIMARY KEY REFERENCES records(id) ON DELETE CASCADE,
 owner TEXT NOT NULL,
 payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS web_origins_owner ON web_origins(owner,record_id);
CREATE TABLE IF NOT EXISTS web_import_keys (
 owner TEXT NOT NULL,
 fingerprint TEXT NOT NULL,
 record_id TEXT NOT NULL REFERENCES records(id) ON DELETE CASCADE,
 PRIMARY KEY(owner,fingerprint)
);
CREATE TABLE IF NOT EXISTS web_contribution_origins (
 contribution_id TEXT PRIMARY KEY REFERENCES contributions(id) ON DELETE CASCADE,
 payload TEXT NOT NULL
);
