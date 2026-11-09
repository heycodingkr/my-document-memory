# Repository consolidation: design, root cause and review

The shared checkout remained at the initial workspace commit while completed changes were published from isolated worktrees. This leaves a large dirty source tree, release branches already in main, two dirty older worktrees and an obsolete API on open PR #2. Source snapshots must be merged by their common ancestor so upstream-only additions are retained.

The current main already rejects wildcard administrator addresses through a comma-separated string configuration API. PR #2 implements the same guard through an older iterable API. Resolve the conflict using the current API and preserve the PR's independent prior-allowlist regression.

The parent owns source review, conflict decisions, builds/tests and publication. Bulk gathering is read-only. Existing feature specifications, root-cause records and tests stay in the consolidated tree. Initial backups are independent Git bundles outside tracked source.

Final review, residual limitations and publication evidence are pending parent verification.
