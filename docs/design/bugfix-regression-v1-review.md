# Outstanding bug regression review v1

Date: 2026-11-09. Parent owns root-cause analysis, implementation review and verification.

## Baseline and design constraints

The checkout contains substantial pre-existing uncommitted account, web-memory, documentation and demo work. No reset, broad commit, production operation or overlapping feature rewrite is authorized by this regression pass. #406 remains with its existing owner.

#398 was reported when sidebar overflow was visible. Current CSS already has overflow-y:auto, so reproduce against the current build before selecting a fix. Inspect flex child sizing and mobile breakpoints only if the regression persists.

#411 was reported after contribution routes gained require_member. Current accounts_fixture already inserts local/bob account rows; preserve this provisioning and the server gate. Fresh builds and real product/browser smokes will determine whether the reported mismatch remains.

## Reproduction and root cause

Fresh Rust workspace tests, Svelte check/build and real CLI/MCP community smoke pass before this pass changes product source. The existing sidebar overflow-y:auto fix passes pointer-driven footer/guide/sign-out checks at 1416×614 and 1024×500; mobile 390×844 also passes.

The new 720×614 test fails before implementation: document scrollWidth is 722, with a MyPage memory-box extending to x721.578125. The two-column memory-card grid retains its content minimum width in the narrow desktop main area. The same screenshot shows cramped/overlapping account labels and duplicate Sign out: AccountNavigation switches at 760px, whereas the app sidebar stays a desktop column until 700px.

Use the existing app breakpoint (700px) for account navigation, and stack MyPage memory cards below 900px to accommodate the desktop sidebar. Preserve existing short-height scrolling and mobile sign-out behavior. Add the focused tests to the default account smoke so these widths remain covered.

## Review and results

The exact pre-fix focused suite had 3 passes and 1 failure at 720×614. After the two CSS media-query changes it has 4 passes, including pointer scroll → Getting started → My space → Sign out and independent /v1/auth/session=401 assertions. The default account/admin/member browser suite now includes these cases and passes all 19 tests. The parent inspected the passing 720px and mobile screenshots. Additional boundary cases at701×500 and700×844 also pass; final default suite inventory is21 cases (19-case full run plus2 added boundary checks).

The parent reconstructed each tracked pre-edit file from the saved baseline patch in an external temporary directory. AccountNavigation, MyPage and the account smoke runner exactly match their original contents plus the three intended single replacements; no unrelated incremental source edit was introduced. The current runtime contract documents registered-member bearer binding. Existing is_member queries accounts by owner, and the existing accounts test denies all four contribution routes for anonymous/nonmember/operator/invalid credentials. Fresh real CLI/MCP smoke passes all MC-01–11 checks.

Svelte check reports 0 errors and 0 warnings; build passes. Fresh baseline Rust workspace execution passes 118 tests. These are local results; production frontend was not deployed. For #409, the historical artifact gathering child completed; the parent independently read its cited original HAR entries and API tracebacks before accepting observations. Long HTML navigation times span DNS/connect/TLS/response-wait phases, while receive times are under8ms; server-versus-network cause is not isolated. The saved retry traceback actually names /v1/templates, not the auth-config request named in the prior audit summary. This correction is recorded in the new results and the issue comment.

The parent’s four bounded public GET samples at 2026-11-09T05:25:24Z all return 200 in 0.202–0.243s; that does not resolve intermittent #409.

The global diff whitespace gate passes. Rust fmt still reports 14 mismatching files in the fresh baseline. #405 and #410 were freshly claimed by codex-repository-consolidation-20261109-96462 during this pass, so no demo or Rust formatting source edits were made here; the exact log was supplied on #410. Arise host scrolling #404 and ongoing feature #406 remain outside the local responsive fix.
