# Contribution review queue pagination v1 (#407)

## Behavior and compatibility

The administrator queue must include older pending contributions even when more than 100 newer terminal contributions exist. Filter in the database before applying the page limit. Keep the personal contributions endpoint unchanged.

GET /v1/admin/contributions accepts status (all, pending, approved, rejected, withdrawn; default all), limit (1–100; default 100), and an opaque cursor. Return items and next_cursor (null at the end). Existing clients reading items remain compatible. Unknown or repeated parameters, invalid limits, and malformed or filter-mismatched cursors return invalid_input/400 after administrator authorization.

Sort by created_at descending and id ascending. The cursor anchors both immutable fields and its status filter. Use keyset pagination, so deciding or withdrawing the anchor does not shift or invalidate subsequent pages. Newer inserts are visible on refresh; this is not a snapshot export. Validate cursor size, version, timestamp and ID without trusting client input.

The web queue defaults to pending, requests the selected status from the server, and offers Load more submissions. Changing filter or refreshing resets pagination and selection. Loading and decisions disable conflicting actions. Logout/authentication failure discards queue, cursor, selected report and confirmation. A completed decision updates the current view and keeps its detail available.

CLI review-queue exposes --status, --limit and --cursor; no flags retains all/default100 compatibility. Administrator authentication and review decisions retain the existing authorization path. No administrator MCP capability is added.

## Dependency-ordered atomic goals

| Order | Route | Output | Independent parent check |
| --- | --- | --- | --- |
| 1 | Parent | This contract, explicit fixture expectations, root-cause/design record | Inspect existing SQL, HTTP authorization, UI and CLI callers |
| 2 (depends 1) | Parent | Focused real-Router failing regression with >100 records | Run before product edits; observe missing older pending item |
| 3 (depends 2) | Parent | Validated queue DTO, filtered keyset SQL and HTTP handler | Run real HTTP tests against independent fixture/SQL order oracle |
| 4 (depends 3) | Parent | Web filter/load-more state and CLI query parameters | Browser regression against real server; actual CLI JSON and continuation |
| 5 (depends 4) | Parent | Build/test results, Arise smoke, final diff review | Root owns all execution, browser actions and evidence; update #407 |

Queue implementation, design, source review and all verification stay with the parent. Bulk read-only integration gathering may be delegated during a long session; summaries only identify locations for parent inspection. Preserve concurrent changes, especially web-origin submission handling for #406. No production deployment or publication is required.

Integration dependency discovered during verification: the shared tree added require_member for contribution endpoints. Before final verification, synthetic actors intended to contribute must have matching accounts rows; keep explicit library-only negative controls unregistered. Route medium read-only fixture-impact gathering to the allowed Luna backend during the long integration session, with no writes or worker builds/tests. Preserve concurrent member fixture updates. Parent inspects the actual source and owns all reruns.
