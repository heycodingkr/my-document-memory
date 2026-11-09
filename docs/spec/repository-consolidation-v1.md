# Repository consolidation v1

2026-11-09. User authorizes committing existing work, merging, pushing and cleaning local/remote branches and PRs. No deployment is requested.

Preserve all existing uncommitted source before integration. Exclude local `.meshcode`, credentials, generated outputs and ignored artifacts. Use isolated worktrees and Git bundles; do not reset or overwrite concurrent work. Keep current main's API contracts, published changes and security guards when old branches conflict. Merge only after parent verification. Remove a branch only when its reachable commits are merged, or its obsolete unique work is preserved in an inspected bundle. Keep ongoing new edits intact.

Dependency-order atomic goals:

| Goal | Depends on | Route | Output | Independent parent check |
|---|---|---|---|---|
| 1. Freeze source and branch/worktree/PR inventory | none | parent | bundles, snapshot refs, manifest | inspect status; verify bundles and source tree IDs |
| 2. Gather broad docs/harness/demo delta | 1 | codex:gpt-6-luna, read-only | short map with file:line references | open cited files; no summary serves as merge evidence |
| 3. Resolve PR #2 against current main | 1 | parent | compatible allowlist regression and preserved current API | focused test, exact diff and merge-parent ancestry |
| 4. Integrate shared snapshot and unique useful worktree changes | 1, 2, 3 | parent; repetitive formatting may go to same worker | coherent source commits, retained spec/design/test records | inspect conflicts and code; check no upstream regressions |
| 5. Verify frozen integrated tree | 4 | parent | Rust/web/harness/product-smoke logs | execute real commands, inspect failures, retain evidence |
| 6. Publish and clean merged refs/worktrees/PRs | 5 | parent | pushed main, merged/closed PRs, removed obsolete refs | fetch, compare SHAs, ancestry, clean status and live PR list |

Use an expected remote head check before pushing. Preserve or integrate edits arriving after the initial freeze before updating the shared checkout. Do not claim external browser-provider behavior from fixture-only tests.
