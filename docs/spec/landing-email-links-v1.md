# English Svelte landing and email link sign-in

Date: 2026-11-09. User scope: make mydocumentmemory.com open in English; bring the landing closer to Web Agentic Memory with GitHub, How it works, Arise download, Chrome, CLI and MCP; implement sign-in by a Resend email link within the Svelte web app.

## Findings and design

The public root currently serves lang=ko and an older asset bundle; its /v1/auth/session returns 404. The current local app is Svelte 5, already has an English landing and owner-scoped accounts, but the landing hides setup in a disclosure, has no Chrome or CLI entry, and keeps GitHub only in the footer. Existing Resend auth sends a six-digit code rather than a link. At initial inspection the production server had no email configuration. A concurrent operations release configured Resend during this task; the final live checks use that configuration. Preserve existing accounts, sessions, ownership, CSRF, community review, editor state, local token access and other uncommitted work.

Use the existing Svelte app, components and green/paper visual system. Expose product/use cases, How it works, Connect your agent and GitHub in navigation. Show three explicit connection paths (web app, CLI, MCP), usable copy controls, real command/config examples and a browser setup row linking Arise download and Chrome. Keep the distinction between document-memory tools and browser tools clear. Public library and email sign-in remain first-class app actions. Reference: WAM Landing.svelte:85-131 (hero resources, browser setup and workflow), not its unrelated benchmark results or remote MCP endpoint. DMEM currently supports local stdio MCP; do not claim a public remote MCP or built-in LLM.

## Dependency-ordered atomic goals

| Order / route | Output | Independent parent check | Depends on |
|---|---|---|---|
| 1 / inline | Status/diff, current landing/App/auth/tests, WAM structure and canonical install links | Read actual source; compare public root and auth responses | none |
| 2 / inline | This spec, focused failing browser/API tests and synthetic inputs | Run the regressions against the unchanged implementation and retain failure output | 1 |
| 3 / inline | Email-link issuing/consumption, English Resend message and captured-mail fixture | Direct code review; API tests for expiry/replay/failed delivery/origin/ownership | 2 |
| 4 / inline | Svelte email-link callback/confirmation and sign-in UI | Actual fixture-backed browser login from a fresh browser context, reload and logout | 3 |
| 5 / inline | English Svelte landing with visible GitHub/How/browser/CLI/MCP routes | Desktop/mobile navigation, exact command/config copy, existing onboarding/editor regressions | 2 |
| 6 / inline | Tested production artifact, configuration and reversible release | Parent runs build/test, reviews diff and inspects rendered images; live root/assets/auth checks | 4,5 |

Core design, source changes, builds, browser loops, tests and final review stay inline. No bulk mechanical change or discovery sweep is required. Reuse development server PID 68076 (web :5174) and PID 68074 (API :3847); use isolated databases for automated auth tests. Never print or commit email keys, login proofs, auth secrets or production tokens. Production data is persistent outside releases; take a consistent backup before an account migration. Resend delivery can be enabled only with an available key and verified sender.

## Email link contract

- POST /v1/auth/email/link accepts {email}; validates the request Origin against configured origins, normalizes the address, applies the existing cooldown/email/browser/global limits and returns generic 202 metadata after accepted delivery. The body never contains the link or proof.
- Generate independent cryptographically random 64-hex challenge and verifier values (two UUIDv4 values each, over 240 bits of entropy). Store keyed hashes using the existing challenge table, with a 10-minute expiry and delivered/consumed state. The URL uses the allowed request origin and fragment /#sign-in=<challenge>.<verifier>, so the proof is absent from server request URLs.
- The Svelte callback immediately removes the proof from browser history and presents a Continue to my space button. GET/opening the link alone does not create a session or consume the token; this also leaves ordinary email link previews harmless.
- POST /v1/auth/email/consume accepts {token}; requires an allowed Origin and a valid 64-hex challenge/verifier, atomically consumes it and returns the existing HttpOnly/SameSite session cookie plus CSRF token. It works in the browser that opens the email, without the original requesting browser's cookies. Expired/reused/incorrect/undelivered links fail closed.
- Keep existing code endpoints compatible, and use email links in the public UI. Existing private account ownership and session/logout behavior remain unchanged.
- Resend requests use the documented /emails API with a per-challenge Idempotency-Key and English plain-text/HTML content, fixed subject, from/to and an explicit expiry. A provider failure does not report success or enable consumption.

## Test inputs and expected results

| ID | Input/action | Expected result |
|---|---|---|
| LL-01 | Fresh anonymous root with Korean browser locale | English lang/title/landing; no automatic language redirect; public library and sign-in available |
| LL-02 | Desktop and 390/320px navigation | GitHub and How it works visible and reachable; no horizontal overflow; Arise download and Chrome use official URLs |
| LL-03 | Choose Web app / CLI / MCP connection tabs and copy | Matching setup shown, correct local commands/stdio config copied exactly; no secrets or unsupported remote endpoint |
| ML-01 | Valid mixed-case email and allowed Origin | 202, normalized recipient, English sign-in URL only in captured email; API body contains no proof |
| ML-02 | Open captured link in a different browser context | URL fragment removed, confirmation visible; no session until confirmation; then My page, reload persistence and logout |
| ML-03 | Reuse, alter verifier, advance fake clock 600s, consume after send failure | 401, no session or account created |
| ML-04 | Missing/foreign Origin, invalid email or malformed token | Rejected; no extra mail or sessions; resend cooldown still enforced |
| ML-05 | Inspect temporary DB and API bodies | Only keyed hashes of challenges/verifiers; no raw proof |
| ML-06 | Existing code/account/community/editor tests | Existing ownership, CSRF, private data, contribution review, editor/save/export behavior pass |
| LIVE-01 | Public HTTPS after reversible deployment | English assets and landing, health 200, auth config/session endpoints exist; no production content mutation during smoke |

## Verification

Implemented and verified. Svelte check/build passed; 33 Rust tests passed on macOS and Linux; 19 isolated browser scenarios and three live public/provider checks passed. The current public root is English and email sign-in is enabled. Details, independent source hashes, screenshots, deployment and data-preservation evidence are recorded in [docs/test/landing-email-links-v1.md](../test/landing-email-links-v1.md). GitHub remains private; access/publication is tracked separately in issue #393.
