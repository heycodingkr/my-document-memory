# Arise MCP blocker fixes — 2026-11-09

Issues #395 and #396 have source fixes, passing candidate verification, and **an applied local MCP runtime verified through the installed MeshCode shim and new shared daemon**. The user explicitly approved runtime application. The signed Arise GUI remains running; its registered public MCP executable now uses the fixed local build. Existing connections to the older MeshCode daemon can finish before that generation drains.

Contract and test inputs: [arise-mcp-blockers-v1.md](../spec/arise-mcp-blockers-v1.md). Original demo and saved documents: [multi-app-browser-demo-v1.md](multi-app-browser-demo-v1.md).

## Root cause and design

### #395: private tab lease lost across forwarded calls

In the sibling `meshcode` repository, `newapp/crates/meshcode/src/main.rs` replaces a busy heavyweight tool worker so unrelated native calls can proceed. Each replacement previously constructed another `UserMcpTools`, spawning a new stdio MCP connection. Arise correctly rejected its missing private lease proof. Matching the public browser session name cannot restore that proof.

The fix shares `UserMcpTools` across overlapping workers by canonical project root and BCB channel. Weak pool entries release the provider when its last owner disappears; a temporary strong reference bridges worker replacement. Synchronization is serialized, tool definitions are cached, and each worker tracks the shared catalog revision independently. Catalog construction therefore does not wait behind a blocked MCP call. Explicit effective configuration changes retain the existing reconnect behavior. No lease check, wire format, dependency or complete tool-graph threading model changed.

Files: `newapp/crates/meshcode/src/main.rs`, `newapp/crates/meshcode/src/user_mcp_tools.rs`, and new `newapp/crates/meshcode/tests/mcp_stateful_process.rs`. Owner specification: `meshcode/docs/specs/arise-mcp-worker-lifetime-fix.md`.

### #396: relative frame evaluation ran in the parent

In the sibling `agent-browser` repository, `crates/agent_browser/src/mcp.rs` forwarded `browser_eval` source unchanged for relative paths such as `f0`. The selected frame's document was never resolved for evaluation. The fix resolves the existing frame path and evaluates in that document's window realm, covering `document`, `window`, `location` and `globalThis`. Missing or inaccessible paths fail before user source runs. Unframed and native `cef:` evaluation keep their existing routing.

Files: `crates/agent_browser/src/mcp.rs` and `crates/agent_browser/src/mcp/regression_tests.rs`.

## Failing before implementation

- Frame regression: four focused tests ran against the original planner. Three failed: child/global realm selection, mutation isolation, and unavailable-frame rejection. The parent was incorrectly evaluated for `f0` and a missing frame could execute a parent mutation. The unchanged native/unframed case passed.
- Connection regression: a real Python stdio MCP fixture acquired process-local proof, then blocked a call while another shim forced worker replacement. The next selection returned a different child process and lost proof. The regression failed before the provider change. A separate installed-binary probe reproduced PID `69595` / held `true` becoming PID `69632` / held `false`.

Red logs: `.artifacts/arise-mcp-blockers/logs/frame-red.log`, `logs/stateful-source-red.log`, and `stateful-installed-red.json`.

## Final verification

All builds, tests, browser control and source review were performed by the parent session. A read-only delegated inventory returned an unusable partial result; no implementation decision relies on it.

| Suite | Passing tests |
|---|---:|
| Arise MCP unit tests, including the four new frame regressions | 98 |
| Arise MCP embedded-socket integration tests | 59 |
| MeshCode user MCP provider tests | 19 |
| MeshCode worker-cache tests | 6 |
| MeshCode daemon process tests | 8 |
| MeshCode GUI-routing process test | 1 |
| New real-process stateful-provider regression | 1 |
| **Distinct total** | **192** |

Commands, from each owner's workspace:

```sh
# agent-browser
cargo test -p agent_browser --lib mcp:: -- --test-threads=1
cargo test -p agent_browser --test mcp_embedded_socket -- --test-threads=1

# meshcode/newapp
cargo test -p meshcode --lib user_mcp_tools::tests -- --test-threads=1
cargo test -p meshcode --bin meshcode worker_cache -- --test-threads=1
cargo test -p meshcode --test mcp_stateful_process --test mcp_daemon_process --test mcp_gui_routing -- --test-threads=1
```

The provider tests cover simultaneous initialization, canonical-root/channel separation, last-owner cleanup, configuration/dead-server behavior and independent catalog revisions. The process regression confirms that the native call finishes while the user MCP remains blocked, and later selection retains the original process and proof. Existing Arise ownership/isolation checks still pass.

Real browser checks used the public MCP against the running Arise GUI:

- An owned loopback HTTP fixture returned the correct parent, child `f0`, nested `f0>f1`, and native frame globals. `f99` returned an explicit error and left the parent untouched.
- A fresh, unedited Naver writer returned `PostWriteForm.naver`, the save control, and `globalThis === window` through **`frame=f0`**. The saved demo draft was not edited.
- Both candidate binaries were connected together. During a blocked user call, an unrelated native script completed; the next forwarded Arise tab selection returned `selectionVerified=true`, and `f0` returned the child marker. This exercises the actual MeshCode → Arise route after worker replacement.
- Test-created tabs, including the earlier data-URL fixture tab 87, were closed and leases released. The original demo document windows were left intact. No publication or sharing action occurred.

Direct evidence: `frame-http-live.json`, `naver-fixed-live.json`, `stateful-candidate-green.json`, `forwarded-arise-green.json`, `cleanup-final.json`, and `logs/` under `.artifacts/arise-mcp-blockers/`.

A data-URL fixture timed out even for unframed evaluation; the successful loopback HTTP fixture avoids attributing that renderer/setup limitation to the frame patch. Two early process-test attempts also encountered discovery timeouts during heavy builds; the final focused and combined runs passed. Neither is claimed as a separately fixed issue.

## Reviewable deliverables and runtime boundary

Targeted final source diffs and patch whitespace were reviewed. Other sessions' dirty changes were preserved. The Arise patch excludes pre-existing tool-description edits. At the source/candidate checkpoint, no commits, installed bundle edits, global MCP configuration writes, or shared-process restarts had been performed. The later authorized local activation is recorded below.

Ignored local evidence directory: `.artifacts/arise-mcp-blockers/`.

| Deliverable | Path |
|---|---|
| Arise source patch | `patches/arise-frame-eval.patch` |
| MeshCode source patch, including the new process test | `patches/meshcode-stateful-mcp.patch` |
| Counts, candidate provenance and applied runtime evidence | `verification-manifest.json` |

Verified Arise candidate: `/Users/jason2/projects/ai-coding/agent-browser/target/debug/agent_browser`, SHA-256 `0578b7c8b14ba84324fd383d29b418fa16deea4bf37fb98261918f83f0363331`. This source candidate identifies as 0.1.76; the installed public MCP remains 0.1.77. The candidate was verified with that installed GUI, without replacing it.

Verified MeshCode candidate: `/Users/jason2/projects/ai-coding/meshcode/newapp/target/debug/meshcode`, SHA-256 `e16e054eec5f9c42bcc8993d9e6cbac0d4755a691db64ee702212b512a344f2c`.

At the source/candidate checkpoint, runtime activation was pending because active shared clients were observed. The following local application was then explicitly approved and performed; this is separate from a public release.

## Applied local runtime

- MeshCode `/Applications/MeshCode.app` now contains the tested 0.2.936 development binary, signed with the existing `ai.meshcode.desktop` identifier and Developer ID team `923WLF6MS6`. The designated requirement and audio-input entitlement match the previous bundle. Full strict signature verification passed. The linked UUID and all nine `__TEXT` section hashes match the tested source binary; signing changes the whole-file hash as expected.
- Fixed Arise public MCP: `/Users/jason2/.meshcode/bin/agent_browser-blockers-0578b7c8b14b`, signed with the same existing team. Global `~/.meshcode/mcp.json` and this project's `.meshcode/mcp.json` now point their `arise-browser.command` to it. Every other server entry, argument, environment value and unknown field was preserved. The installed Arise GUI bundle was not replaced.
- New shared MeshCode daemon: PID **96462**, version 0.2.936; its record's binary stamp matches the installed executable. It was detached with a new session and closed stdin. Launch log: `.artifacts/arise-mcp-blockers/runtime/shared-daemon-launch.log`. No active shim or GUI was killed. Older connections to PID 51535 finish through the existing drain mechanism; newly launched shims use the fixed generation.
- The installed-shim/shared-daemon probe returned **`allPass=true`**: a native call finished in 0.143 seconds while an owned browser wait remained active; tab selection succeeded after worker turnover; `f0` returned the child globals; the existing Naver editor returned `PostWriteForm.naver`, its save button and the correct window realm.
- Slides tab 59 and Naver tab 63 remained open. Original Docs tab 61 was absent at final read-only discovery; the saved summary was reopened as tab **126**. No document content was changed. Test fixture tab 125 was closed and leases released.

Runtime evidence is in `.artifacts/arise-mcp-blockers/runtime/`: `installed-shared-runtime.json`, its log, `signing-provenance.json`, signature descriptions, rollout state, and private configuration backups. The first signed-candidate harness attempt hit its 15-second discovery limit; the retry with a 45-second startup bound passed. Runtime harness preparation also needed to wait for Naver's iframe and recognize its current `저장` button label. One newly opened writer disappeared during a probe; the final passing probe read the original owned demo editor instead. These harness/target-state failures are retained in separate logs and are not reported as new production fixes.

Installed signed MeshCode SHA-256: `b25d7910d4181b21789521c33198619bdf0fa64aeabdddf127578812eae9ff46`. Registered signed Arise MCP SHA-256: `fc53f2c653826c92036acef44e4fef385b0de5f9373c4415a80b94559f1a9561`.

Recovery copy: `/Applications/.MeshCode-before-arise-mcp-e16e054e.app`. Original configuration bytes are retained privately under the runtime evidence directory. This local installation did not publish an update feed or change a signing key. No additional user restart is required for new MCP shims to use the fix.
