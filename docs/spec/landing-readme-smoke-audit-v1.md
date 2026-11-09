# Landing, README and main-feature smoke audit

Date: 2026-11-09. Scope: inspect current shared working tree, improve README entry points and verification instructions, rerun actual Rust product checks, and report landing/onboarding findings. Do not deploy, change repository visibility, publish contributions, send real email, or modify another session's feature work.

## Required behavior

- README readers can reach the hosted app, public templates, quick start and verified current feature scope before reading long background sections.
- English and Korean landing setup notes state that the hosted app needs no installation; source checkout is needed for local setup and CLI/MCP builds. Remove the historical repository-access warning after independently verifying the repository is public (issue #393).
- Verification instructions identify separate runtime, account/community, recall and public deployment smoke targets. Contract tests against the Python double are not evidence for the Rust product.
- Run product checks against the current source with synthetic temporary databases. Distinguish local checkout results from read-only hosted checks and historical reports.
- Inspect code and the final diff directly. Record failures and limitations accurately; do not claim native Office rendering, real email delivery, external provider editing or LLM quality from these checks.

## Dependency-ordered atomic goals

| Order | Route / output | Independent parent check | Dependencies |
|---|---|---|---|
| 1 | Inspect git status/diff, README, landing/setup, smoke runners, browser specs and previous reports | Parent reads source before deciding scope; preserve concurrent changes | none |
| 2 | This specification plus test inputs/expected results | Parent checks commands against fixture requirements and production read-only behavior | 1 |
| 3 | Fresh Rust tests and builds, Svelte check/build | Parent executes checks and records exit codes/logs from current source | 2 |
| 4 | Runtime/browser, accounts/review, community and recall smoke; read-only hosted smoke when configured | Parent executes real binaries; test HTTP/file/SQLite/history oracles, not worker summaries | 3 |
| 5 | README improvements and prioritized landing findings | Parent checks app routes, claims and executable commands against source/results | 4 |
| 6 | Final design/root-cause review and concise user report | Parent inspects final scoped diff; separate verified behavior, failures and untested boundaries | 5 |

All work is inline: the relevant reads, edits, tests and judgments are short, dependent or require direct source inspection. No delegation is needed.
