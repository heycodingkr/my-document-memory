# Administrator session review access

## Root cause

The contribution review handlers in `http/account.rs` used a local `admin()` check that required an `Authorization: Bearer` administrator token for every request. It also required an Origin header for queue reads. The email-link administrator flow issued a separate `dmem_admin_session` cookie, but the queue and decision handlers never checked that session. As a result, a correctly authenticated allowlisted administrator received 401 from the review API.

## Design

Route queue reads and decisions through `http/admin.rs::authorize`, which accepts either the existing configured operator Bearer token or a valid allowlisted administrator session. Queue reads pass `write=false`; decisions pass `write=true`. Writes require the configured Origin and an HMAC-bound CSRF token for cookie sessions. A queue GET may omit Origin, while any supplied Origin must match the configured list.

Administrator email challenges and sessions are stored separately from member challenges and sessions. The allowlist is normalized through `AuthConfig::set_admin_emails` and populated from comma-separated `DMEM_ADMIN_EMAILS`. The server checks the allowlist when consuming a challenge and on every session use, so removing an address revokes existing sessions. Challenge verifiers and session tokens are stored as HMAC digests.

## Regression inputs and review

`docs/test/admin-session-review-access.md` defines the request inputs and expected outputs. The Router + temporary SQLite test covers normalized allowlist matching, a non-allowlisted address with the same response but no mail delivery, single-use link consumption, member and local-owner denials, no-Origin queue reads, CSRF and Origin rejection, successful approval, replay rejection, database reopen, and allowlist revocation. It also checks that the member cookie is not set and that pending contributions stay private until approval.

The existing operator Bearer approval test remains in the accounts integration suite. This preserves the older CLI/operator path while sharing the decision endpoint.

## Verification

The regression test failed before the route change at the queue request with status 401 (expected 200). After the fix:

- `cargo test -p dmem-server --test accounts allowlisted_admin_session_can_review_contributions_with_csrf_and_origin -- --nocapture`: passed.
- `cargo test -p dmem-server --locked`: passed.
- `cargo test --workspace --locked`: passed (34 tests).
- `cargo fmt --all -- --check` and `git diff --check`: passed.
