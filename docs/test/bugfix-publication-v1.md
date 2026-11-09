# Responsive bugfix publication verification v1

Date:2026-11-09. User authorized push and production deployment.

The final frontend preserves the currently deployed landing and demo video in release `20261109T054829Z-demo-video`. Its baseline is landing source `e229b8481982e3c82b3dcc67fa811bb61c4c2aac` plus the deployed DemoVideo/Landing dependency changes. The parent rebuilt that exact source and matched all13 non-media production files. The three existing media files are retained from the live release and checked against their known hashes.

The same two #398 CSS fixes, original six regression cases and initial spec/test/review records are already on origin/main in integration `4cf5635`. The explicit `release/bugfix-navigation-20261109` branch publishes the compatible frontend snapshot, including the already-deployed compact menu/demo and the responsive corrections. The integrated backend/web-memory feature set on main is outside this frontend-only rollout.

## Dependency order and independent checks

| Order / route | Output | Parent verification |
|---|---|---|
| 1 / parent | Inspect live/source/git and freeze latest baseline | Direct source review and reproducible13-file build |
| 2 / parent | Two CSS corrections, six regressions and member-fixture note | Exact source delta; compact menu return flow; deployed demo preserved |
| 3 / parent | Validated frontend/fixture | Rust source identity, Svelte and actual browser results below |
| 4 / parent | Publish release branch and main verification record | Normal pushes, remote SHA checks, shared index/source preserved |
| 5 / parent | Guarded immutable release | Existing deploy lock; expected release/index/backend guards; SQLite backup; retained old assets/media; atomic symlink with rollback |
| 6 / parent | Hosted evidence | Public byte hashes, read-only navigation/viewport checks, auth/library smoke, unchanged PID/backend/config |

## Inputs and parent-run results

Desktop sizes1416×614,1024×500,720×614,701×500 require pointer scrolling to reach Getting started and a unique Sign out; guide opens and My space returns, opening the compact menu when needed. Mobile sizes700×844 and390×844 require a unique reachable Sign out. Every case requires no horizontal overflow and actual session401 after sign-out.

| Check | Result |
|---|---|
| Rust workspace --locked |95 passed; exact crates/Cargo.toml/Cargo.lock identity proved between tested source and deployed landing base |
| Workspace fixtures/binaries --locked |Passed |
| Final Svelte check/build |0 errors,0 warnings / passed |
| Final real account/member/admin browser regression |20 passed, including all6 responsive cases and contribution review/member-denial controls |
| Current demo baseline rebuild |13 non-media file hashes match;3 existing media hashes preserved |
| Before-switch read-only production smoke |Healthy HTTPS, credential/Origin boundaries, linked assets and private library reads pass |

Initial shared-checkout counts118 Rust and19+2 browser tests belong to that separate snapshot; they are not substituted for this final candidate's results.

Excluded evidence directory: `.artifacts/bugfix-publication-20261109/` records source/build manifests, final test logs, guarded activation script, publication-state.json and post-deployment evidence. It contains no source-control changes to production credentials or data. The backend binary/configuration/database remain outside the frontend archive.

## Completed publication

- Frontend commit: `b11e064be3c4007168056c0b824b3e9f8478a61e`, pushed to `release/bugfix-navigation-20261109`.
- Active release: `/srv/my-document-memory/releases/20261109T055832Z-bugfix-b11e064`; previous release retained: `/srv/my-document-memory/releases/20261109T054829Z-demo-video`.
- Guarded activation verified all16 expected file hashes and a SQLite backup with integrity_check=ok; backend binary/configuration and PID804357 were preserved.
- Public verification:15 complete file bodies match SHA-256; unchanged video range returns206 with the expected first1024 bytes; web/API health both200.
- Read-only live browser checks pass at1416×614,720×614,701×500,700×844,390×844: sidebar layout/guide/menu/public navigation, no horizontal overflow, demo retained and no page errors. The parent inspected the720px/mobile captures.
- Before/after authenticated read-only smoke returns the same private source/template IDs and saved document versions.
- Operational evidence remains in the excluded artifact directory; production secrets and database contents are not committed.
