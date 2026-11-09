# Administrator session access to the contribution review API

## Inputs and expected results

| Input / action | Expected result and independent check |
|---|---|
| Request a link for `not-allowlisted@example.test` | Same `202` response as an allowed address; fake mailer records no delivery. |
| Start with `operator@example.test`, then configure `*@example.test` | Reject the wildcard with `InvalidInput`; the previous exact allowlist remains active and still delivers only to `operator@example.test`. |
| Configure ` Operator@Example.Test ` and request a link for `operator@example.test`, then explicitly POST its captured token to consume twice | The normalized allowlist match succeeds; first consume is `200`, second is `401`. Receive `dmem_admin_session` and a CSRF token. The ordinary member cookie is not set, and the token is absent from the API body. |
| Use an anonymous request, ordinary member session, or local owner Bearer token on `GET /v1/admin/contributions` | `401`; the pending contribution remains unchanged. |
| Use the administrator session on `GET /v1/admin/contributions` without an Origin header | `200`; the queue includes the synthetic pending contribution. |
| POST an approval with missing/wrong CSRF, a foreign/missing Origin, or an ordinary owner Bearer token alongside the admin cookie | `401`; the contribution remains pending and anonymous public detail returns `404`. |
| POST an approval with the administrator cookie, matching CSRF token, and exact configured Origin | `200`; contribution status becomes approved and anonymous public detail returns `200`. Replaying the decision returns `409`. |
| Reopen the same SQLite database with the same allowlist and use the session; then remove the email from the allowlist | Session works after reopen; the revoked allowlist makes the next queue request return `401`. |

## Dependency-ordered goals

| Order | Route / output | Independent check | Depends on |
|---|---|---|---|
| 1 | Define synthetic email/link/session and queue/decision inputs, status codes, and privacy boundary | Compare with `docs/spec/admin-email-starters-v1.md` and existing account tests before code edits | none |
| 2 | Add a focused Router + temporary SQLite regression that fails when the email session cannot reach the queue/decision routes | Inspect response status, pending/approved rows, and anonymous public detail independently | 1 |
| 3 | Route administrator checks through the session-aware authorization helper; preserve operator Bearer support and enforce Origin/CSRF on writes | Run the regression against the actual Router, including negative controls | 2 |
| 4 | Parent review and clean-branch verification | Run focused tests and workspace tests; inspect the exact staged diff and commit contents | 3 |

## Wildcard regression

Before the fix, `AuthConfig::set_admin_emails(["*@example.test"])` returned `Ok(())` because email normalization checked syntax but did not reject `*`. The focused `wildcard_admin_email_is_rejected_without_replacing_valid_allowlist` test records the expected result and verifies the prior exact address remains usable.

The original focused test failed before the fix (`Ok(())` instead of `Err(InvalidInput)`). That branch passed its original 35-test workspace run.

During PR #2 integration on 2026-11-09, current main already contained the guard and used a comma-separated string API. The conflict resolution keeps that API and adapts the regression to normalized ` Operator@Example.Test ` followed by `other@example.test,*@example.test`. The test checks both set size and retained exact address. Parent mutation verification temporarily removed the guard: the test failed with `Ok(())` instead of `Err(InvalidInput)`, then passed after restoration. `cargo test -p dmem-server --locked` passed on the reconciled branch. Logs: `.artifacts/branch-cleanup-20261109/pr-{wildcard-red,wildcard-green,server}.log`.
