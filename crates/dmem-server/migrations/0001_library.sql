PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS records (
 id TEXT PRIMARY KEY,
 owner TEXT NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('template','source','document')),
 version INTEGER NOT NULL CHECK(version>0),
 payload TEXT NOT NULL,
 updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS records_owner_kind ON records(owner,kind,updated_at DESC);
CREATE TABLE IF NOT EXISTS revisions (
 document_id TEXT NOT NULL REFERENCES records(id),
 owner TEXT NOT NULL,
 version INTEGER NOT NULL,
 payload TEXT NOT NULL,
 PRIMARY KEY(document_id,version)
);
CREATE TABLE IF NOT EXISTS source_files (
 source_id TEXT PRIMARY KEY REFERENCES records(id),
 original BLOB NOT NULL
);
