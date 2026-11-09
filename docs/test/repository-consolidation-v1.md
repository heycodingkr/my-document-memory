# Repository consolidation: inputs, expected results and verification

2026-11-09. Specification: [repository-consolidation-v1](../spec/repository-consolidation-v1.md). Evidence: `.artifacts/branch-cleanup-20261109/`, with browser/fixture artifacts retained under the isolated consolidation worktree's ignored `target/e2e-logs/`.

| Input/action | Expected result / independent oracle | Parent result |
|---|---|---|
| Dirty shared and admin/bilingual worktrees | Verifiable independent bundles; preserve source and live index during integration | Three original source bundles plus successive live-source snapshots saved and verified |
| PR #2's obsolete iterable allowlist vs current string API | Preserve current API, reject wildcard, retain prior normalized exact allowlist | Guard removed: focused test fails; restored: passes; server suite passes; PR #2 merged |
| Upstream-only additions and published README | No blind overlay deletion or lost web-app links/deployment history | Reviewed 25 conflicts; retained upstream records and top-of-README links |
| Reference import followed by DB reopen/template extraction | Persist selected language/region/provider/variant | Initial full Rust run reproduces Null vs ja-JP; incoming owner fix persists form; final regression passes |
| Recall of externally imported private templates | Preserve original copy restrictions | Parent disabled rights override: full vs structure_only failure; restored override passes |
| Short desktop/sidebar boundary | Reach guide/sign out, no duplicate controls or horizontal overflow | Initial 720px failure reproduced; final 701/720/1024/1416 desktop and 390/700 mobile pass |
| Markdown hard break cleanup | Same rendered break and a passing whitespace gate | GitHub Markdown API produced identical HTML before/after; explicit backslash retains break |
| Completed branch cleanup | Merged refs are ancestors, published main matches reviewed tree; concurrent work preserved | Verified in final Git/PR inventory after publication |

Parent commands and outcomes:

| Command / log | Result |
|---|---|
| `cargo test --workspace --locked` (`final-rust-tests.log`) | 122 passed, no failures |
| `cargo build --workspace --locked` and `--examples` | Passed |
| `cargo fmt --all -- --check`; complete `git diff --check` | Passed after scoped formatting and EOF cleanup |
| `pnpm --dir web check`; `pnpm --dir web build` | Zero Svelte errors/warnings; build passed |
| Harness `unittest discover` | 138 passed |
| Harness smoke / contract | 14 passed; 222 passed and 3 explicit skips |
| Mutation check | 18/18 mutants killed; clean control |
| Document/code trace | Every cited ID defined; 238 implemented cases; all 203 R1/F rows accounted for |
| `dmtest.porttrace --upstream /Users/jason2/projects/ai-coding/web-agentic-memory --require-upstream` | 93 sources, 72 adapted, 21 excluded; actual upstream comparison passed |
| Demo Node tests | 17 passed, 2 explicit skips |
| Runtime browser smoke | Actual HTTP/CLI/MCP/restart checks passed; 35 browser cases passed, 22 fixture/opt-in cases skipped in this invocation |
| Accounts browser fixture | 21 passed, including all six sidebar viewport cases |
| Web-memory fixture with `--browser` | 28 checks passed, including 2 Playwright cases |
| Recall / community real-product smoke | Passed |

`tests.json` records the first run, including the reproduced form and 720px failures. `followup-tests.json` records the final passing product checks and the expected failing rights mutation (exit 101). No production deployment, actual email delivery, or live provider account operation was part of this consolidation verification. Existing feature-owner review records and separately reported Arise evidence are preserved; they are distinct from this parent's fixture-only intake run.
