# Administrator email login and starter memories verification

Issue: #402. Specification: ../spec/admin-email-starters-v1.md.

## Inputs and expected results

| Input | Expected |
|---|---|
| Valid allowlisted email, case/outer whitespace variants | Exact normalized match; one administrator sign-in email; generic accepted response |
| Non-allowlisted valid email | Same accepted public response, no email and no administrator privilege |
| Empty allowlist / malformed configured address | Browser administration disabled / configuration fails closed |
| Link GET or merely opening landing page | No session or contribution mutation; explicit confirmation required |
| Valid link POST, then replay | Administrator session once; replay rejected |
| Expired or altered link; address removed before consume | Rejected; no administrator session |
| Anonymous, ordinary member session, DMEM_TOKEN | Cannot read administrator queue or decide contributions |
| Allowlisted admin session, then allowlist revocation/expiry/logout | First authorized; subsequent protected requests rejected |
| Session decision without CSRF, wrong Origin, unexpected Authorization | Rejected with no contribution change |
| Authorized explicit approval / rejection / blocked review | Expected existing publication behavior; blocked entry cannot publish |
| Browser localStorage/sessionStorage/history | No operator token or magic-link credential persisted; fragment removed promptly |
| Browser reload / lock / narrow screen | Session restore works; lock clears server session and queue; no horizontal overflow |
| Fresh DB and reopened DB seeded twice | New stable starter IDs once; old IDs/versions and private records unchanged |
| Anonymous catalog/search by locale | New originals visible with correct provenance and useful sections |
| Private copy and draft using a new writing/review memory | Attribution retained, usable deterministic outline, no invented facts or private references published |
| Production HTTPS health and existing API/web smoke | Ready, credentials/Origin boundaries and existing data remain intact |
| Full runtime browser About cards after concurrent copy update | Current consistency/guidance/review headings visible and no horizontal overflow at 320px |

## Baseline and reproduction

Initial source inspection: contribution review currently requires a browser-entered DMEM_ADMIN_TOKEN; AuthConfig has no email allowlist or administrator session. Existing member magic links issue normal dmem_session cookies. The public catalog contains nine English starter structures and nine Korean equivalents. Before backend implementation, run focused integration tests demonstrating the absent administrator email route and rejection of the intended authorized session. Record exact commands/results here.

## Results

Reproduced before implementation: the focused unconfigured-admin route test returned 404 instead of 202. The starter tests failed with project.brief.en and memory.evidence.en NotFound. The first real browser test failed because Administrator email was absent from the token-entry review form.

Parent verification passed: cargo test --workspace --locked (92 tests), cargo build --workspace --locked, pnpm --dir web check (zero errors/warnings), pnpm --dir web build, and python3 tests/smoke/accounts-v1.py (11 browser scenarios). Eight dedicated administrator integration cases cover exact allowlisting, generic issuance, malformed configuration, single-use/expiry/undelivered/revoked links, ordinary credential denial, CSRF/Origin, atomic decision audit, persistence/revocation/logout. Starter tests cover all 24 additions by ID and title search, copying/CC0 attribution, usable drafts, unchanged original templates, database reopen and bounded search responses.

Images actually opened for visual QA: target/e2e-logs/accounts-1794195355777177000/administrator-email-login.png and administrator-review-mobile.png. Desktop sign-in and the narrow-screen blocked/rejected review were inspected.

Final validation inputs were hashed before the last full run and matched afterward. The immutable archive is .artifacts/admin-starters/20261109T034500Z-admin-starters.tar.gz (SHA-256 39f237508f5953d289760f840df79e895e9eec352a3858b248c3e694a4e67c26), with 125 source/asset files recorded in .artifacts/admin-starters/release.json. Baseline was the concurrently deployed release 20261109T033037Z-80119, containing 56 records. Every existing source difference from that release was inspected: only administrator integration/formatting, owned tests/fixture and the rebuilt frontend changed; other existing files matched.

Rollout uses the jason-owned deployment lock, checks the expected current release and unchanged private environment, runs Linux admin/starter tests and a release build, uses SQLite backup before migration, atomically switches the application symlink and rolls back if readiness/catalog/assets fail. No DNS/proxy or credential replacement. Production promotion completed to /srv/my-document-memory/releases/20261109T034500Z-admin-starters. The prior release was 20261109T033037Z-80119. SQLite backup is /var/backups/my-document-memory/20261109T034500Z-admin-starters.sqlite3 (0600, integrity_check=ok). Independent HTTPS verification checked all 24 added IDs and all 24 title searches, author/license/content, exact HTML and linked asset hashes, ordinary email login enabled, anonymous administrator queue denied, generic non-allowed request behavior, and administrator configuration disabled. All 56 baseline records retained identical owner/kind/version/payload hashes and the private environment hash was unchanged. The preceding concurrent release had already seeded these shared-worktree additions, so idempotent promotion did not create duplicates (56 records before and after). Evidence: .artifacts/admin-starters/live.json.

Post-deployment public-api-v1.py passed all 9 groups and deployed-v1.py passed all 4 web/auth/assets groups. Linux administrator/starter integration tests passed 8+2 and the production release build passed. The broader runtime --browser run first exposed two stale About-card heading expectations from a concurrent copy update: source landing-copy.ts:20-22 and rendered failure context were inspected, and only those two test strings were aligned. No product code was changed for that test fix. The rerun passed HTTP/CLI/MCP/import/export/conflict/history/restart checks plus 30 browser scenarios (12 email-fixture scenarios correctly skipped); the separate account/admin suite already passed 11 scenarios. Logs: /var/folders/hn/4d_172w53_58g8kg255mlw_w0000gn/T/meshcode-detached-51535-1794196000988.log, meshcode-detached-51535-1794196168677.log and meshcode-detached-51535-1794196333066.log.

Real administrator addresses have been requested from the user. Until supplied, the production allowlist stays empty and browser administrator access stays disabled; do not guess or promote the sender address.
