CREATE TABLE IF NOT EXISTS contribution_reviews (
    contribution_id TEXT PRIMARY KEY REFERENCES contributions(id),
    report TEXT NOT NULL,
    decided_at INTEGER NOT NULL
);
