# Repository consolidation: inputs and expected results

| Input/action | Expected result / independent oracle |
|---|---|
| Dirty shared and admin/bilingual worktrees | Bundle verification succeeds; snapshots reproduce all nonignored source; original index/worktree unchanged during freeze |
| PR #2's obsolete iterable allowlist vs current comma-separated string API | Current API and wildcard rejection remain; adapted regression rejects wildcard and preserves prior normalized exact address |
| Previously pushed files absent from old shared HEAD | Three-way integration retains current main additions and README publication links; no blind overlay deletions |
| Repeated URL imports, owner-isolated recall/contributions and admin review | Actual Rust integration and CLI/MCP smoke assertions pass against temporary DBs |
| Svelte UI | `pnpm check` returns no errors; production build passes; applicable browser fixture suites pass |
| Python harness and demo changes | Harness selftests, smoke/contract suites and demo unit tests pass or any independently reproduced pre-existing limitation is explicitly recorded |
| Formatting and whitespace | Rust format check and diff check pass; intentional Markdown hard breaks retained |
| Remote changes during integration | Fetch/reconcile; guarded normal push only; never force-push main |
| Completed cleanup | Live main SHA equals tested commit; no open redundant PRs; removed branches are merged/preserved; root status includes only concurrent work, if any |

Results and exact commands will be added after parent execution. Evidence directory: `.artifacts/branch-cleanup-20261109/`.
