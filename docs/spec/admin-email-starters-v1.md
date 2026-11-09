# Allowlisted administrator email login and starter memories v1

Issue: #402. User requested WAM-style administrators who receive sign-in links only at explicitly permitted email addresses and manage contributed memories, plus useful public starter templates/memories.

## Behavior

Ordinary member email sign-in remains available. Administrator sign-in is a separate flow: a server-side exact normalized email allowlist, a generic request response, delivery only to allowed addresses, an explicit POST to confirm a ten-minute single-use link, and a short-lived HttpOnly administrator session. Recheck the allowlist at consumption and on every protected request. Empty allowlist disables browser administration. Never infer an administrator from an email sender, public profile, normal member cookie or local library bearer. Preserve the distinct operator bearer for existing CLI automation. All administrator responses are no-store; writes require the exact configured Origin and session CSRF. Secrets and magic-link tokens never enter persistent browser storage, logs or public responses.

Administrators can inspect submitted structure snapshots and review findings, then explicitly approve or reject. Existing blocked-review checks and private-source exclusion remain enforced. Signing out/locking clears the administrator session and visible queue. Personal account logout does not silently become an administrator credential.

Add original English and Korean starter structures and reusable writing/review guidance with stable IDs, explicit author/license and useful sections. Retain all existing IDs and versions. Seed additions are idempotent and must not overwrite community entries, private records or saved documents. Expose them through the real public catalog and verify private copying/draft creation. No private reference or user contribution is published automatically.

## Dependency-ordered atomic goals

| Goal | Route / output contract | Independent parent check | Depends on |
|---|---|---|---|
| WAM reference gathering | codex:gpt-6-luna background read-only; short file:line map of admin allowlist, email-link/session and contribution review patterns; no edits, builds, credentials or external writes | Parent opens cited source before adopting any behavior; parent owns design | Existing code/test inspection and this spec |
| Administrator backend | Inline; focused failing integration test, allowlist configuration, purpose-separated link/session authorization and protected contribution decisions | Parent runs denial, replay, expiry, revocation, Origin/CSRF and existing account/contribution tests | Confirmed parent authorization contract; WAM source crosscheck before final review |
| Administrator UI | Inline; email request/explicit confirmation/session restore/logout integrated into existing review view without browser operator tokens | Parent runs real browser E2E against isolated capture mailer; inspect rendered page and mobile overflow | Backend contract |
| Curated starter pack | Inline content/design judgment; bounded original catalog dataset and additive seed loader | Parent inspects every entry, validates normalization, stable IDs/idempotence/privacy, public search/copy/create | Existing seed inventory |
| Deploy starter pack and admin implementation | Inline; frozen tested source/archive and release, administrator access disabled until permitted addresses are supplied | Parent inspects current live release/locks, deploys without replacing secrets/data, reruns HTTPS/API/admin/catalog checks and records evidence; preserve shared Git index and other sessions' pending changes | Passing backend/UI/catalog checks |
| Activate administrator access | Inline; apply only the user-confirmed email allowlist to the private production environment | Parent verifies configured email count, enabled admin configuration, non-allowed rejection and unchanged ordinary member access; never print credential values | Deployment plus user-provided administrator addresses |

## Scope and concurrency

The shared tree contains active account/leaderboard (#401), community review (#397) and landing (#399) work. Keep their edits; reread shared integration files before editing. Use separate admin modules/tests and a dedicated seed dataset where practical. Builds, tests, deployment, root cause and final review remain with the parent. Use the existing deployment lock and compare the expected live release before promotion. Do not change repository visibility, DNS or the application listener to a public bind.
