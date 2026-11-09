# Bugfix publication candidate verification v1

Date: 2026-11-09. User authorized commit, push and production deployment after the initial bugfix review.

The publication checkout starts at origin/main `964a39faa478e9f6eef29f83a032715f47898a3a`. Its untouched frontend matches all13 production frontend files byte-for-byte in release `20261109T050859Z-18544`. The candidate adds only #398's two responsive CSS corrections, six regression cases/default smoke registration, #411's fixture/member contract clarification and these task records. Ongoing shared web-memory, administrator-queue, formatting, demo and landing-UX work is excluded.

## Order, outputs and independent verification

| Order / route | Output | Parent check |
|---|---|---|
| 1 / parent | Isolated current-main checkout and live baseline | Direct git/source review and13-file SHA-256 match |
| 2 / parent; document copy attempted on codex:gpt-6-luna | Two CSS changes, regression/contract docs | Worker made no changes; parent finished the bounded copy and independently checked bytes; complete candidate diff review |
| 3 / parent | Frozen validated frontend and candidate fixture | Actual Rust, Svelte and browser results below |
| 4 / parent | Commit and normal fast-forward push | Staged paths exclude private env, DBs and artifacts; origin SHA checked |
| 5 / parent | Frontend-only immutable release | Live current/index/backend guards under existing deploy lock; verified SQLite backup; retained backend/config; atomic switch and rollback checks |
| 6 / parent | Hosted verification evidence | Public health, asset-byte identity, read-only navigation/viewport checks, active release and unchanged service PID |

## Inputs and expected results

- Four desktop sizes1416×614,1024×500,720×614,701×500: real pointer wheel reaches Getting started and exactly one Sign out; guide opens, My space returns, sign-out revokes the session; no horizontal page overflow.
- Two mobile sizes700×844,390×844: exactly one visible Sign out; session becomes401; no horizontal page overflow.
- Temporary actual Rust accounts fixture with explicitly registered local/bob owners: member contribution, admin approval/rejection, private boundaries, points, withdrawal and replay controls remain intact. Existing Rust nonmember contribution denial checks remain enabled.
- Production serving path resolves through current/web/dist: activation preserves the live backend binary and configuration, retains prior hashed assets and must return healthy loopback/API endpoints plus exact frozen frontend bytes.

## Parent-run candidate results

| Check | Result |
|---|---|
| cargo test --workspace --locked |95 passed |
| cargo build --workspace --examples --bins --locked |Passed |
| pnpm --dir web check |0 errors,0 warnings |
| pnpm --dir web build |Passed |
| python3 -B tests/smoke/accounts-v1.py |20 browser cases passed, including all6 responsive cases |
| Exact source delta |Both CSS files equal upstream plus the intended single replacement each |
| Untouched baseline versus production |All13 frontend files match SHA-256 |

These candidate results are separate from the initial shared-checkout investigation, which had118 Rust tests and19+2 browser runs. The candidate excludes the unrelated unmerged administrator-queue case and other ongoing backend work.

Local excluded evidence directory: `.artifacts/bugfix-publication-20261109/` (`baseline-manifest.json`, `candidate-rust.log`, `candidate-browser.log`, `candidate-check.log`, `candidate-build.log`, activation script and subsequent publication evidence). This document records the candidate verification; the actual pushed commit, activated release, backup and public verification are recorded in that publication evidence.
