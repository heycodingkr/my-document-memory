# Contribution review queue pagination v1 test contract

## Inputs and expected results

| ID | Input | Expected |
| --- | --- | --- |
| QP01 | One old pending contribution and 120 newer rejected records; administrator GET status=pending | Old pending item returned; no rejected items; bounded page; terminal cursor null |
| QP02 | 121 pending records, tied timestamps, plus newer rejected records; limit=25 | Concatenated pages match independently queried created_at DESC,id ASC order, each ID exactly once |
| QP03 | Decide/withdraw the last item of a page, then use its saved cursor | Remaining pending items are not skipped/duplicated; anchor need not retain pending status |
| QP04 | Omitted query, all and individual status filters, limits 1/100 | Default all compatibility; filter respected; at most requested size; cursor only when another row exists |
| QP05 | Unknown/repeated parameters, invalid limits, malformed/empty/filter-mismatched cursor | Administrator gets 400; unauthenticated/customer credentials get 401 even with malformed query |
| QP06 | Actual CLI review-queue with synthetic operator token, status/limit/cursor | JSON pages follow server order, cursor round-trips, old pending item discoverable; invalid CLI flags rejected |
| QP07 | Real web + Arise with 121 pending and 120 newer rejected fixtures | Default pending100, Load more reveals oldest pending, detail opens; All/Rejected filter resets pagination; refresh and logout clear state |
| QP08 | Existing account/review/CLI/MCP smoke | Approval/rejection, private isolation, public reads and administrator boundaries continue passing |

Use isolated local databases and synthetic fixture identities. No production accounts, publication, real mail, or destructive operations. Seed fixture records with unique private template IDs and structurally valid snapshots; derive expected IDs independently from SQL rather than the pagination implementation.

## Reproduction and verification

Verified on 2026-11-09 by the parent session.

Before implementation, `cargo test -p dmem-server --test contribution_queue pending_filter_precedes_the_hundred_record_limit -- --exact` failed: the response contained 100 newer rejected IDs instead of the single older pending ID.

Final checks:

- `cargo test --workspace`: 116 passed, including all five focused contribution_queue HTTP regressions. Log: `target/review-queue-407-20261109/workspace-final.log`.
- `pnpm --dir web check`: zero errors and warnings; `pnpm --dir web build` passed.
- `python3 tests/smoke/community-v1.py`: actual CLI/MCP private save/read, cross-owner denial, revision conflict, anonymous public reads, contribution/check/decision/copy/withdrawal and audit checks passed.
- `python3 tests/smoke/accounts-v1.py`: all 15 real-server browser cases passed. QP06/07 also executes the actual CLI with default/all, pending pages of37, cursor round trips, and invalid status/limit flags.
- Existing synthetic member fixtures were aligned in the shared tree with the new member-only contribution guard. The queue fixture explicitly registers its withdrawal actor as a synthetic member. The authorization guard was preserved.
- Publicly reviewed synthetic titles use base36 timestamps. A previous 13-digit Date.now title was observed to satisfy Luhn and correctly trigger review_blocked; this fixture change avoids that intermittent unrelated failure.
- Targeted diff whitespace check passed.

## Arise smoke evidence

Used the configured Arise agent-browser0.1.76 through one persistent stdio client after forwarded host calls lost their private lease. All actions stayed in owned window58/tab131, session mdm-queue407-native-51535. The administrator used the isolated synthetic mail capture and explicit confirmation.

The fixture has 121 pending and120 newer rejected records. Assertions compare the full rendered DOM order with an independent unbounded SQL oracle. Arise snapshots cap their item inventory at80, so snapshot item count alone is not a queue-size oracle.

Verified first pending100, native Load more to121, native opening of the oldest pending review, rejected100→120, all100→200, filter/selection reset, native refresh to first100, real page navigation with session restoration to pending100, and native administrator logout clearing queue/cursor/detail. Arise's keyboard tool supports editable text fields, so status selection used the browser DOM select/change event; loading, review opening, refresh, confirmation and logout used native Arise input. A changed same-origin query forced a full page navigation because navigating to the identical URL retained the existing page.

Evidence: `target/review-queue-407-20261109/verification.json`, `arise-snapshots.json`, `fixture.json`, `arise-pending-first-100.png`, `arise-filter-menu.png` (oldest review detail), and `arise-all-first-100.png`. Returned screenshots were inspected. Administrator signed out; lease released; temporary MCP client exited0.

The isolated preview remains at http://127.0.0.1:3858/#review, PID3126. Log: `/var/folders/hn/4d_172w53_58g8kg255mlw_w0000gn/T/meshcode-detached-51535-1794198861907.log`. Its database and captured mail are synthetic. No production data was used.

Newer submissions or status changes from other reviewers require refresh; pagination does not promise a database snapshot across separate requests.
