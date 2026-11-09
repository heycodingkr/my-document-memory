# Review queue #407: root cause, design and review

The existing Store::contributions query sorts all statuses and applies LIMIT 100. ContributionReview then filters pending locally. Thus 100 newer terminal submissions hide an older pending submission. Even 101 pending submissions have no route to the oldest item.

A dedicated administrator query applies status before LIMIT and fetches one extra row to detect continuation. Its cursor contains version, status, created_at and id. The existing sort is preserved with an explicit ascending ID tie-break. A stable immutable anchor avoids the offset-pagination skip caused by approving/rejecting earlier items. Cursor fields are validated and bound as SQL parameters. Authorization remains in the shared administrator guard.

Personal contribution listing is left intact. Queue responses retain items and add next_cursor. The UI owns filter, cursor and request/session lifecycle; it requests the selected server filter and appends subsequent pages. CLI flags expose the same contract. No schema migration is needed for correctness.

Review before completion: inspect all changed source and test claims; preserve concurrent web-origin logic; verify malformed input/auth boundaries, tied timestamps, decided anchor, UI filter reset and logout, and real CLI pagination. Newer inserts require refresh by design; this is not a snapshot export.

Final parent review found no remaining #407 blocker. The HTTP extractor captures query errors and checks the shared administrator guard before returning400. SQL binds every cursor/filter field, applies status before LIMIT, fetches at most101 rows, and hydrates reviews only for the returned page. The cursor uses immutable created_at/id rather than updated_at, offset, or a database lookup requiring the anchor to remain pending.

The UI requests server filters, clears pagination and confirmation on view/session resets, guards concurrent operations and late session responses, and removes decided items from a pending view while retaining their decision detail. CLI flags use URL query encoding and preserve default all/items behavior. Existing web-origin submission handling and the member-only contribution guard were preserved.

All five focused tests,116 Rust workspace tests, actual CLI/MCP community smoke,15 browser cases, Svelte checks/build and the owned Arise smoke passed. See [test results](../test/review-queue-pagination-v1.md) for commands, independent oracles and browser evidence.

During integration, shared member fixture changes arrived while a read-only Luna impact sweep was running. That sweep was cancelled and collected as failed/cancelled; its partial summary was not used as verification. Parent inspected the relevant source and ran every build/test/browser check. No delegated source edits were accepted.

The retained limitation is request-to-request concurrency: new submissions and later status changes are surfaced by refresh, not a snapshot export. The endpoint remains bounded at100 returned records per request.
