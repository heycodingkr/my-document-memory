# Administrator email login and starter memories design review

Issue: #402.

## Root cause

The existing contribution review API has a separate operator bearer but the browser view asks the operator to enter that long-lived credential. General email account sign-in does not create administrator authority. There is no configured email allowlist, administrator-specific link/session lifecycle or browser session-based review access. The original starter catalog covers common documents but has little explicit reusable writing/review guidance.

## Design and review obligations

Inspect WAM source as a reference and independently verify every adopted pattern. Separate administrator link/session purpose from ordinary member login, validate normalized exact email allowlists, and recheck authorization on every request. Generic request responses must not reveal whether an address is permitted. Keep one-use/expiry/Origin/CSRF and no-store boundaries. Existing operator bearer remains only for API/CLI use; remove its requirement from the product browser flow.

Inspect all curated content for practical sections, original provenance, neutral writing guidance and privacy. Use additive stable IDs and do not alter existing seeded or user-owned records. Reproduce failures in focused tests, test locally as parent, freeze a reviewed release before deployment, and compare production health/data before and after.

## Verified reference and implementation

The reference collector (job 165, codex:gpt-6-luna) exhausted its token budget and returned a partial map. That summary was not accepted as evidence and was not retried. The parent independently opened WAM identity/admin.rs:133-216, http/admin_routes.rs:85-191, identity/store/admin.rs:205-264 and durable/admin.rs:9-65. The parent also read identity/admin.rs:15-16 directly: links last 600 seconds and administrator sessions two hours. WAM normalizes an exact configured email, uses generic accepted request responses, separates customer and administrator credentials, validates Origin/CSRF, and has explicit contribution review records.

The target adopts exact normalized allowlists, generic issuance responses, purpose-separated challenge/session HMACs, ten-minute links, two-hour HttpOnly sessions, revocation checks, Origin/CSRF guards and explicit reviewed decisions. MDM supports multiple configured reviewer addresses and portable email links, using its existing same-origin app rather than WAM's distinct admin origin/browser binding. It uses the existing synchronous Resend sender rather than claiming WAM's durable delivery outbox; undelivered links are unusable. Existing operator bearer support is retained for CLI/API compatibility and removed from the browser flow. Decisions and pseudonymous reviewer audit rows commit in the same SQLite transaction.

The new public dataset contains 24 original entries (16 document/presentation templates and 8 writing/review memories), 12 per language. Existing 18 starter IDs/payloads are preserved with INSERT OR IGNORE. The public search contract remains bounded by MAX_RESULTS=20: tests check every entry by exact ID and a title search, not an unsupported unbounded response count. Private copying preserves CC0 provenance; drafts and database reopen/idempotence were verified.

## Outcome

Parent checks passed: 92 Rust tests, full workspace build, frontend check with zero errors/warnings, production web build, and 11 real browser account/member/admin scenarios. Desktop administrator email login and narrow-screen blocked-review/rejection screenshots were opened with image inspection. Production release 20261109T034500Z-admin-starters is live. Independent public checks matched all 24 additions/searches and exact frozen frontend bytes; all 56 preexisting records and the private environment were unchanged. A 0600 SQLite backup passed integrity checking. Public API/web smoke passed, Linux admin/starter tests passed 8+2, and the broader editor/runtime browser suite passed 30 scenarios after correcting two stale About-copy assertions without changing product behavior. Administrator activation is still awaiting user-confirmed email addresses; the empty allowlist remains disabled and ordinary email sign-in remains enabled.
