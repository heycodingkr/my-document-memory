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

Pending post-fix validation.
