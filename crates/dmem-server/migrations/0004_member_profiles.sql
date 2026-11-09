CREATE TABLE IF NOT EXISTS account_profiles (
 account_id TEXT PRIMARY KEY NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
 handle TEXT UNIQUE COLLATE NOCASE CHECK(handle IS NULL OR length(handle) BETWEEN 3 AND 24),
 public_profile INTEGER NOT NULL DEFAULT 0 CHECK(public_profile IN (0,1)),
 updated_at INTEGER NOT NULL,
 CHECK(public_profile=0 OR handle IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS account_profiles_public ON account_profiles(public_profile,handle);
