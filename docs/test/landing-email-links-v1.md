# English Svelte landing and Resend email links — verified

Date: 2026-11-09. Spec: [landing-email-links-v1.md](../spec/landing-email-links-v1.md). Issue: #392.

## Result and root cause

The public site initially served an older Korean bundle (`lang=ko`) and returned 404 for `/v1/auth/session`. The local Svelte 5 app was already English, but it kept GitHub in the footer, had no Chrome/CLI entry, and hid MCP setup in a disclosure. Existing Resend authentication required a six-digit code.

The existing Svelte app now exposes GitHub, How it works, browser downloads, and Web app / CLI / MCP connection tabs with working copy controls. The public default remains English even with a Korean browser locale. Public library, sign-in and private workspace remain connected to the existing app.

Email-link authentication issues an independent 64-hex challenge and verifier, stores keyed hashes, expires after 10 minutes, and consumes the pair atomically once. Links work in another browser. The Svelte app removes the fragment from history and asks the user to continue before POST consumption. Initial load and same-document hash changes are both handled. Existing account ownership, CSRF, session cookies, logout and code endpoints remain supported.

## Reproduced before implementation

- Focused Rust regression: `/v1/auth/email/link` returned 404 instead of 202.
- Focused browser regressions: header GitHub and the Send sign-in link control were absent.
- Browser login flow exposed a same-document navigation bug: changing an already-open page to `/#sign-in=...` did not rerun onMount. Added a hash-change handler and protected pending initialization and unsaved editor state.
- Additional connection tabs required existing onboarding tests to select their named tablist/panel. Updated selectors without removing their assertions.
- Visual inspection found the 320px Sign in button wrapping. Widened its navigation column and verified again.

## Checks and evidence

| Check | Actual result |
|---|---|
| Frozen Svelte snapshot `pnpm check` | 0 errors, 0 warnings |
| Frozen Svelte production build | Passed |
| `cargo test --workspace`, macOS and Linux | 33 passed on each platform |
| Actual-API browser suite: landing-links, onboarding, workspace, agent-handoff | 16 passed |
| Captured synthetic email + actual Rust API + Svelte accounts suite | 3 passed; cross-browser link, confirmation, replay rejection, reload, logout, ownership and contribution flow |
| Final narrow-layout/onboarding check after CSS change | 8 passed |
| Live public landing and connection-copy tests | 2 passed against https://mydocumentmemory.com |
| Opt-in live email-delivery test | 1 passed: production Svelte form → Resend accepted request, 202; recipient was an official `delivered+...@resend.dev` simulation address |
| Fresh public root / auth configuration / anonymous session | lang=en / email_enabled=true / 401 |
| Existing production records compared with consistent pre-deployment backup | All 23 records, 4 revisions and 6 original files retained unchanged |

The live email check proves provider acceptance and UI behavior. It did not send to a person's inbox. Cross-browser link consumption and session behavior were verified end to end with the isolated captured-mail fixture.

Commands used for the frozen source under `.artifacts/landing-email-links/release`:

```sh
pnpm --dir .artifacts/landing-email-links/release/web check
pnpm --dir .artifacts/landing-email-links/release/web build
CARGO_TARGET_DIR="$PWD/target" cargo test --manifest-path .artifacts/landing-email-links/release/Cargo.toml --workspace
python3 .artifacts/landing-email-links/release/tests/smoke/accounts-v1.py
python3 .artifacts/landing-email-links/release/tests/smoke/runtime-v1.py --browser --browser-spec tests/landing-links.spec.ts --browser-spec tests/onboarding.spec.ts --browser-spec tests/workspace.spec.ts --browser-spec tests/agent-handoff.spec.ts
DMEM_E2E_URL=https://mydocumentmemory.com pnpm --dir .artifacts/landing-email-links/release/web test:e2e tests/landing-links.spec.ts --grep='English landing|connection examples'
DMEM_LIVE_EMAIL_TEST=1 DMEM_E2E_URL=https://mydocumentmemory.com pnpm --dir .artifacts/landing-email-links/release/web test:e2e tests/email-delivery.spec.ts
```

Screenshots were returned by the image inspection tool and visually reviewed: desktop hero, How it works, agent connection panel, 320px hero, synthetic email sign-in, live public hero and live Resend request result. Evidence is in `.artifacts/landing-email-links/{runtime-browser,final-browser,live-browser,live-email}` and the frozen source's `target/e2e-logs/accounts-*` directories. The accounts fixture deliberately chooses its own output directory.

## Production and concurrent work

This task froze complete source for verification because another session was constructing a multi-output demo component and service logos. It preserved the working tree and omitted the then-unattached incomplete component from its initial source snapshot. It did not overwrite that other work.

Linux tests and release build passed on `jason-4090`. Reviewed archive SHA-256: `176b11b1d7a3f5ffb8c47f54336bd1b9dd468662bec8868108783e46c6bc1694`. Activation held a deployment lock, required the expected previous release, took and checked a consistent SQLite backup, switched the symlink atomically and retained an application rollback path.

- This task activated `20261109T022211Z-landing` after `20261109T011532Z`.
- Consistent backup: `/var/lib/my-document-memory/backups/library.before-20261109T022211Z-landing.sqlite3`.
- A concurrent operations task subsequently activated `20261109T022729Z-13901` and configured Resend, a stable auth secret and the sender `My Document Memory <help@mydocumentmemory.com>`.
- This task preserved that newer release, compared its identity.rs/account.rs SHA-256 values to the reviewed snapshot (both exactly matched), and ran the live landing and Resend checks against it. No credential value was printed or committed.
- Existing local dev processes at :5174 and :3847 were reused. No new development server was started or stopped.

Production and account data remained outside release archives. No Git commit/push or repository visibility change was performed.

## Review and remaining repository access issue

Reviewed the request-origin check, fragment handling, proof shape, hash-only persistence, failure paths, rate limits, delivered state, expiry, single-use transaction, session/CSRF boundary, Svelte callback, CLI/stdio examples and official browser URLs. Existing editor and agent-handoff regressions passed. WAM's unrelated performance results and remote MCP endpoint were not carried over.

`gh repo view` confirmed the GitHub repository is PRIVATE; anonymous access returns 404. The canonical GitHub link is present and local setup notes explain that access is required. Issue #393 tracks the owner's source-publication/access decision. Repository visibility was preserved.

Primary provider reference: [Resend Send Email API](https://resend.com/docs/api-reference/emails/send-email), [Resend test recipients](https://resend.com/docs/dashboard/emails/send-test-emails).
