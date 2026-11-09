# Landing, README and main-feature smoke audit: inputs and expected results

Contract: [landing-readme-smoke-audit-v1](../spec/landing-readme-smoke-audit-v1.md).

| ID | Input/action | Expected result and independent oracle |
|---|---|---|
| AUD-01 | `cargo test --workspace --locked`; build workspace and accounts fixture | All tests pass on current source; binary compilation exits zero |
| AUD-02 | `pnpm --dir web check` then `pnpm --dir web build` | No Svelte/type errors; production assets generated from current source |
| AUD-03 | Runtime smoke with workspace, agent-handoff, onboarding and landing browser specs | Unauthorized access rejected; file bytes preserved; template copy and evidence-backed document creation work; stale save rejected; DOCX XML valid and overwrite refused; MCP framing/errors safe; history survives restart; UI copy/fallback, outline approval, editing/export and mobile overflow assertions pass |
| AUD-04 | Account fixture with account, review, queue, member, admin-email and loading browser specs | Synthetic email links, separate owners, public/private boundaries, explicit review/blocked approval, opt-in profile and deterministic loading failures are asserted without sending real mail |
| AUD-05 | `python3 tests/smoke/community-v1.py` | Private CLI/MCP round trips, anonymous public reads, owner isolation, contribution checks/approval/rejection/withdrawal, SQLite/catalog state agree |
| AUD-06 | `python3 -I tests/smoke/recall-v1.py` | Actual HTTP/CLI/MCP recall cases pass, including ownership and fixed safe errors; no double-only pass substituted |
| AUD-07 | Read-only `public-api-v1.py` with existing excluded credentials, if available | HTTPS/readiness/catalog/auth/CORS/Origin checks pass; no deployed data mutations or credential output |
| AUD-08 | README links, command dependencies and scoped diff | Hosted start links match App route handling; browser suites select the correct fixture; future/external capabilities and benchmarks remain qualified; concurrent changes preserved |
| AUD-09 | Fresh landing setup screenshot and anonymous GitHub read, then English/Korean setup notes after copy edit | Before: public source still accompanied by an access warning. After: hosted no-install path and source-build requirement are clear in both languages; existing language and setup-copy regressions pass |

## Results

Date: 2026-11-09 (UTC). All checks were executed by the parent. Evidence directory: [`target/landing-readme-smoke-audit-20261109/`](../../target/landing-readme-smoke-audit-20261109/).

| Check | Result | Evidence |
|---|---|---|
| Rust workspace | Initial 110 passed; later 113 passed, 0 failed, for the tested source snapshot | `rust-tests.log`, `rust-tests-final.log` |
| Workspace and account-fixture builds | PASS, both runs | `rust-build.log`, `rust-build-final.log` |
| Svelte check/build | PASS before and after copy edit; 0 errors / 0 warnings | `web-check*.log`, `web-build*.log` |
| Runtime and landing browser subset | PASS 35 cases, including final run; real HTTP/CLI/MCP runtime smoke also passed | `runtime-browser-final.log` |
| Copy-only regression subset | PASS 9 existing cases: languages, persistence, 320px, real clipboard and connection examples | `post-copy-browser.log` |
| Account/review/member browser subset | Initial PASS 12; latest run **10 passed, 2 failed** | `accounts-browser.log`, `accounts-browser-final.log` |
| Real CLI/MCP community smoke | Initial PASS; latest **FAIL at valid contribution submission: auth_required**. Private save/read, revisions and anonymous public reads passed first | `community.log`, `community-final.log` |
| Real recall | PASS 44/44, including final run and 59-output sentinel scan | `recall-final.log` |
| Hosted full read-only smoke | **FAIL twice**: HTTP redirect response timeout, then TLS handshake timeout during auth-config comparison | `public-api.log`, `public-api-retry.log` |
| Separate hosted probes | API HTTP308; API/web health and web root HTTPS200; 0.477–0.537 seconds | `public-probes.json` |
| Rust formatting gate | **FAIL**, differences in 21 files from concurrent integration | `rust-fmt.log` |
| Touched-file whitespace and local Markdown targets | PASS | Parent `git diff --check` and link-existence checks |

The latest main browser runs total **45 passed / 2 failed**. The 9 copy regressions overlap and are not additional distinct coverage. The Rust 113-test log completed at04:44:06UTC; shared account-route source changed afterward. It is a pass for its tested snapshot, not certification of subsequent concurrent edits. No whole-tree all-green claim is made.

## Contribution integration failure (#411)

The account routes now wrap `/me/contributions` with `require_member`, which calls `Store::is_member`; that query requires an `accounts` row for the authenticated owner. The synthetic account fixture maps its bearer tokens to `local` and `bob`, without corresponding member rows.

- In `web/tests/review.spec.ts`, private template creation succeeds but contribution preparation returns401 instead of200. MC-12 and MC-13 fail before the administrator UI decisions.
- In `community-v1.py`, a valid CLI `contribute ... --rights-confirmed` call at line120 fails with `auth_required` (exit1 rather than0).
- The signed-in-member browser contribution flow AC-18 passed in the same latest account run. This distinguishes the nonmember-token fixture path from the working member path.

Registered workspace issue #411 with source locations, commands and expected results. Authorization was not weakened to make tests pass. Aligning member/token provisioning, fixtures and the contribution contract remains a separate integration change.

## Landing and README changes

README now starts with hosted app/free-template links, a short current-capability explanation and quick-start-first navigation. Verification instructions include the account-fixture build and separate runtime/account/community/recall commands with coverage boundaries. English and Korean setup notes now explain hosted no-install use and source-build prerequisites.

Anonymous [GitHub repository access](https://github.com/heycodingkr/my-document-memory) works; the former private-repository premise in #393 is historical. Issue #393 was resolved with verification notes. Fresh pre/post setup screenshots and the desktop hero were actually opened with the image inspection tool; the new copy was inspected in the post-edit screenshot.

## Remaining boundaries

- Intermittent hosted response/TLS delays are recorded in #409. Fast separate health probes do not turn the failed full smoke into a pass; no definitive network-versus-server root cause established.
- Formatting differences were registered as #410 and left to the owners of the concurrent Rust changes.
- Temporary databases, synthetic identities and captured email only. No live inbox delivery, production contributions, external-provider editing, native Office layout or model-quality/savings verification.
- README and landing copy changes remain local. No commit, push or deployment was performed.

Root causes, review and further landing recommendations: [design review](../design/landing-readme-smoke-audit-v1-review.md).
