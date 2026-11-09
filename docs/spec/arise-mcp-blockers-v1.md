# Arise MCP demo blockers: fixes for #395 and #396

Date: 2026-11-09. User requested fixes for the two live blockers recorded in `docs/test/multi-app-browser-demo-v1.md`. Issues claimed by `codex-arise-blockers-20261109-7138`.

## Contract and boundaries

- #395: consecutive host-forwarded calls using an unchanged effective MCP configuration and the same explicit conversation must retain that server's connection-local lease proof when concurrent calls rotate the heavyweight tool worker. Different conversations still cannot acquire each other's private leases. Never relax ownership to a public session-name match. Explicit configuration changes retain the existing documented reconnect behavior.
- #396: `browser_eval(frame="f0", js=...)` must evaluate in the requested same-origin frame, consistently with snapshot/read, or fail explicitly. It must never silently evaluate in the parent. Preserve native `cef:` routing, validate nested paths, and report inaccessible/missing frames without parent-side execution.
- Code owners are sibling repositories `agent-browser` (public MCP planning/frames) and `meshcode/newapp` (CLI MCP provider/routing). Inspect their actual source, tests, status and existing diffs before edits. Preserve all concurrent changes, credentials, account state, user tabs and saved demo artifacts. No public release or installed app replacement is authorized merely by this specification.

## Dependency-order atomic goals

| Slice / route | Output contract | Independent parent check | Depends on |
|---|---|---|---|
| G0 / inline | Current issue claims, repository status/diffs, applicable instructions, initial MCP source/tests, this spec | Read actual files and compare the earlier live failure evidence | None |
| G1 / `codex:gpt-6-luna`, background, read only | Short file:line map of the MeshCode CLI MCP connection lifecycle and existing stateful-provider test fixtures; no judgment, edits, builds, tests, app or configuration changes | Parent opens each cited location before acting; summary only guides inspection | G0 |
| G2 / inline | Focused failing frame-evaluation test covering child/global scope and absence of parent fallback | Run it against pre-fix code and preserve the failure | G0; independent of G1 |
| G3 / inline | Minimal Arise frame-planner change, source review and focused passing regression | Parent inspects each changed line and runs frame/MCP regressions | G2 |
| G4 / inline | Reproduce #395 in a focused stateful MCP lifecycle test, then make the smallest correct connection-retention change at the verified owner | Parent opens mapped source, demonstrates red, reviews ownership/caching decisions, then runs green and isolation regressions | G1 |
| G5 / inline | Build candidate MCP binaries and exercise isolated fixture/live calls for both fixes | Parent owns all builds/tests and browser loops; verify same-source binary provenance, exact target and saved demo preservation | G3, G4 |
| G6 / inline | Design/root-cause/review record, issue comments/status, precise runtime rollout boundary | Review final diffs and direct evidence; do not mark an unverified running deployment fixed | G5 |

The gathering child receives a bounded read-only inventory task because this conversation is already long. Routing follows the user's first usable allowed backend. Implementation, the file about to change, tests, builds, browser control and every judgment stay inline. If its gathering fails, continue inline; never treat the summary as evidence.

## Inputs and expected results

| ID | Input | Expected result |
|---|---|---|
| FIX-F01 | Parent title `parent`; iframe `f0` title `child`; eval `document.title` | `child`; parent code does not run |
| FIX-F02 | Nested `f0>f1`; expression and explicit global/window references | Resolve the requested child realm, not merely a shadowed document variable |
| FIX-F03 | Missing, malformed, or inaccessible frame | Explicit error; no parent mutation/evaluation fallback |
| FIX-F04 | Existing `cef:` token and no frame | Native `frame_id` remains pinned; unframed evaluation retains its current semantics |
| FIX-L01 | Stateful toy MCP: acquire, catalog discovery, select via host envelope | Same child connection and private proof; select succeeds |
| FIX-L02 | A user-MCP call is in flight while an unrelated native call rotates the busy worker | Native call completes independently; subsequent user-MCP selection retains the same child and proof |
| FIX-L03 | Explicit Arise endpoint/config change or dead transport | Drop/reconnect affected server intentionally; report loss honestly, do not replay uncertain input |
| FIX-L04 | A second client with identical public session name tries selection | Still denied without the original private lease proof |
| FIX-L05 | Tool catalog refresh and concurrent conversations | Current catalog, distinct targets, no unnecessary reconnect or cross-conversation selection |
| FIX-LIVE | Candidate binaries, own loopback framed fixture and owned tabs; repeated host calls | Frame result and window lease survive the exact previously failing sequence; user demo tabs untouched |

## Review and evidence

Keep red/green logs and candidate binary paths in `.artifacts/arise-mcp-blockers/` or repository-local ignored build directories. Existing dirty changes are not this task's output. Record any test/build baseline failure separately. Complete the concrete fix and validation before a runtime restart/replacement decision; keep the existing working browser available.

## Verified source boundary

The frame planner sends the user's JS unchanged and ignores a relative frame path; the new focused tests failed for child/global selection and unavailable-frame parent execution. Four focused tests, 98 MCP unit tests, 59 MCP process/socket integration tests, and a real Arise HTTP iframe probe pass after the minimal planner change. A data-URL fixture hit an existing renderer timeout even for unframed evaluation; the HTTP probe separates this environment limitation from the fix.

For #395, `meshcode/newapp/crates/meshcode/src/main.rs` `checkout_call_worker` removes a busy worker from the cache to keep native tool calls concurrent. `build_mcp_tool_worker` currently creates a new `UserMcpTools`, which creates new stdio clients and loses connection-local leases. Keep one weakly pooled provider per canonical project/channel across overlapping worker generations; serialize connection synchronization and cache catalog definitions so a blocked MCP call does not block unrelated native calls. Per-worker catalog revision tracking avoids consuming another worker's change notification. Test with a real stateful stdio fixture and concurrent shims before implementation.

## Authorized local runtime rollout

The user explicitly approved applying the tested fixes after the source/candidate report. Scope is this machine's MCP execution; no public release, update-feed publication, dependency change or signing-key change.

| Slice / route | Output | Parent check | Depends on |
|---|---|---|---|
| R0 / inline | Current installed hashes/signatures, effective global/project MCP configuration, daemon metadata and source-candidate hashes | Compare candidates with the previous verification manifest; never print credentials | G6 |
| R1 / inline | Staged copy of the installed MeshCode bundle containing the tested binary, signed with the existing Developer ID; stable copy of the tested Arise public MCP | Full signature check, same bundle identifier/team/designated requirement/entitlements, linked UUID and every `__TEXT` section unchanged; preserve original resources and executable | R0 |
| R2 / inline | Post-signing isolated real-process/Arise probe | Same stateful connection and child-frame result as the prior green probe | R1 |
| R3 / inline | Local MeshCode installation with original bundle retained, global/project Arise MCP command updated without altering other fields | Compare fresh configuration before each write; back up credential-bearing configuration privately; verify installed signature and hashes | R2 |
| R4 / inline | New shared MCP daemon and actual installed-shim smoke | New record matches installed binary stamp; own-window selection survives a busy-worker turnover, native call completes during browser wait, Naver f0 resolves editor; saved demo tabs retained | R3 |
| R5 / inline | Runtime evidence, issue resolution and durable deployment note | Distinguish the new shared daemon from older connections still draining | R4 |

Use the existing daemon's supersession/drain behavior rather than killing active shims or the GUI. New shims read the new installed executable; existing shims can finish on their old daemon until their turn ends. Keep the GUI and Arise renderer running so unsaved user work and the demo windows survive.

Rollback: retain the original signed MeshCode bundle and private byte-for-byte MCP configuration backups. Before installation, confirm the original bundle still verifies and that copied configuration parses identically. If the installed smoke fails, restore only the changed command fields (preserving concurrent unrelated edits), restore the old bundle, then start its daemon using the existing generation mechanism. Do not delete either generation during validation. This is a local development installation of already-tested source candidates, with the existing signer and application identifier.
