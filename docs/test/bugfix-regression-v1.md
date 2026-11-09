# Outstanding bug regression inputs and results v1

Specification: [bugfix-regression-v1](../spec/bugfix-regression-v1.md). Date: 2026-11-09.

This is the initial shared-checkout investigation record. The separately isolated push/deployment candidate and its fresh results are recorded in [bugfix-publication-v1](bugfix-publication-v1.md).

| Case | Input | Expected result |
|---|---|---|
| BUG-398-DESKTOP | Synthetic email-member login at 1416×614, 1024×500, 720×614 and the 701×500 breakpoint boundary; scroll sidebar with pointer, click Getting started, return, sign out | Sidebar is viewport-bounded; footer controls can be revealed and clicked, guide opens, return works, session becomes anonymous |
| BUG-398-MOBILE | Same signed-in workspace at 700×844 (breakpoint boundary) and 390×844 | Navigation fits width; visible Sign out works; no horizontal document overflow |
| BUG-411-MEMBER | Fresh accounts_fixture DB with local/bob account rows and existing synthetic bearer credentials; CLI/MCP contribute/list/check/withdraw | Member contributions succeed; explicit consent required; private data isolation and operator-only approval retained |
| BUG-411-NONMEMBER | Registered bearer owner without accounts row; anonymous requests; list, submit, review, withdraw routes | auth_required/401 before contribution access; no mutation |
| BUG-411-REVIEW | Member fixture submits clean and unsafe templates via HTTP; administrator confirms decisions in browser | Explicit clean approval publishes; unsafe approval remains blocked |

| BUG-409-LATENCY | Two bounded fresh GETs per public web root and API health endpoint; parent records DNS, connect, TLS, first-byte and total timings | Preserve individual outcomes, including timeouts; distinguish current observations from historical failures; do not declare an intermittent issue fixed without an identified cause |

## Evidence

All results below were run by the parent on 2026-11-09. Logs are under target/bugfix-regression-20261109/ (git ignored).

| Check | Result | Evidence |
|---|---|---|
| Pre-fix focused sidebar browser suite | 3 passed, 1 failed at720×614: scrollWidth722; screenshot also shows duplicate Sign out/overlapping account labels | sidebar-before.log; sidebar-layout-before.log; target/e2e-logs/accounts-1794201602147295000/ |
| Same focused suite after CSS correction | 4 passed at1416×614,1024×500,720×614,390×844; actual pointer guide/return/sign-out, session401, no horizontal overflow | sidebar-after.log; screenshots under target/e2e-logs/accounts-1794201715001268000/ |
| Default account/admin/member browser regression | 19 passed, including MC-12/13 and the first four responsive cases | accounts-browser.log |
| Additional exact-breakpoint browser cases | 2 passed at701×500 and700×844; final default suite now contains21 cases | sidebar-boundaries.log |
| Rust workspace --locked | 118 passed, including member-only contribution denial controls | rust-baseline.log |
| Fresh workspace binary/example build | Passed | build-baseline.log |
| Real CLI/MCP community smoke | All MC-01–11 checks passed | community.log |
| Svelte check / build | 0 errors,0 warnings / passed | web-check.log; web-build.log |
| Current public web/API timing, two samples each | All HTTP200; total0.202–0.243s at2026-11-09T05:25:24Z; intermittent issue not resolved | public-timing.json; probe-public.py |
| Global git diff --check | Passed | whitespace.log |
| Rust formatting baseline | Failed in14 files; separate fresh owner handles #410 | rust-fmt-before.log |

Existing #411 fixture provisioning and sidebar overflow-y:auto changes were already present before this pass; this pass preserves and verifies them. The parent independently reconstructed the tracked baseline files and verified exactly the intended source replacements. The parent inspected passing 720px and mobile images. No deployment was performed.

## Historical latency evidence independently opened by the parent

The read-only gathering child (job183, codex:gpt-6-luna) completed. Its summary was used to locate original evidence, then the parent opened each cited trace ZIP's `1-trace.network` line1 and saved the selected raw fields in historical-html-timing.json. The 04:14:33Z request took29,123ms: DNS3,792 / connect14,661 / TLS6,560 / wait4,102 / receive7.988ms. The 04:15:16Z request took31,915ms: DNS1 / connect11,014 / TLS7,841 / wait13,058 / receive0.728ms. Both HTML responses were200. The delay spans multiple client-observed phases; these records do not isolate server processing from network behavior. The small receive time does not explain the long navigation.

The parent also opened public-api.log and public-api-retry.log directly. The former times out reading an HTTP status line; the latter times out in TLS handshake for the saved traceback's /v1/templates request (line49). The historical audit summary's auth-config label is not supported by that saved traceback. The old public-probes.json has no timestamps for tight correlation. Fresh HTTPS200 samples are not a completed hosted-browser regression and do not close #409. No serving configuration was changed.
