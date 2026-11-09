# Private/public memory and contribution review: design and review

Date: 2026-11-09. Contract and dependency order: [specification](../spec/memory-community-smoke-v1.md). Test oracle: [inputs and expected results](../test/memory-community-smoke-v1.md). Issue: #397.

## Root causes and reproduced failures

1. The original CLI and seven-tool MCP adapter covered draft creation/read, but omitted private structure save/read, document revision save, anonymous public reads, and the contribution lifecycle. The new real-binary smoke initially failed at the unavailable `template-save` command.
2. `Store::decide` inserted an immutable submitted snapshot into the public catalog after credential validation alone. A focused Router test reproduced an administrator publishing a synthetic API-key marker (200 instead of expected 422). Missing review routes also reproduced as 404.
3. The shared client guard originally accepted `.` and `..` as IDs, which URL normalization can reinterpret as path segments. A focused failing unit test reproduced this, then the guard rejected both while preserving dotted seed IDs. The real CLI/MCP smoke includes those inputs.
4. The existing administrator helper required Origin even for GET. Actual browser same-origin GET omits that header, so the first review UI test failed after the correct administrator credential. A focused Router test reproduced 401, then verified the fix: authenticated reads may omit Origin, foreign supplied Origin is still rejected, and mutations still require Origin.
5. In the actual Arise 1051×612 CSS viewport, the sidebar footer was below the viewport (sign-out bottom 863.6). Scrolling the element could not reach it while sidebar overflow was visible. Adding vertical sidebar scrolling changed its bottom to 565.1 and enabled the native click after fresh assets loaded. This was verified in the affected CEF browser; the equivalent Playwright probe already passed before the change, so it was not used as evidence of reproduction.

The working tree also contains concurrent account/profile/leaderboard, starter-memory, recall, landing, harness and documentation work. Preserve those changes. Broad-suite failures from unfinished concurrent work are recorded separately from this feature's checks.

## WAM reference and domain choices

WAM is read-only. The reference-gathering delegate (job155, codex:gpt-6-luna) exhausted its budget and returned partial locators. Its summary was not accepted as evidence. The parent opened the source directly:

- `../web-agentic-memory/docs/spec/gatekeeper.md:45`: deterministic security gates and a final scan precede publication; its normal agent decision path and human exceptions are wider than this runtime.
- `../web-agentic-memory/docs/spec/admin.md:12`: reviewed proposals, explicit publishing decisions, generation checks and audit are separate from requesting verification.
- `../web-agentic-memory/crates/wam-gatekeeper/src/tools.rs:558`: duplicate comparison includes scope and the candidate fingerprint.
- `../web-agentic-memory/crates/wam-server/src/contribution_store/state.rs:164`: review decisions check current state/generation and record decision, time and reviewer.
- `../web-agentic-memory/crates/wam-server/tests/application_lifecycle.rs:106`: a manual approval without a verified proposal does not publish; repeated decisions conflict.

MDM already promises licensed derivative contributions and attribution chains. Therefore its `contribution-review-v1` treats exact/near structure duplication as a human-review advisory, while secrets, personal identifiers, injection, invalid licenses and malformed structures block approval. This is explicitly different from the future `preflight-v1` reject-on-duplicate policy. No model quality, browser replay, automatic publication or full WAM parity is claimed.

## Implementation and invariants

- The shared HTTP client omits empty Authorization and has an explicit public-read method that never forwards a private token. Optional CLI/MCP tokens enable anonymous catalog use; private requests retain server-side authentication.
- CLI JSON inputs deserialize through existing strict DTOs; MCP rejects unknown fields and unsafe IDs. MCP adds nine tools without changing the original seven names or protocol framing. Administrator commands use a distinct credential and allowed Origin.
- Pure core review logic scans the actual immutable snapshot. Findings never include the matched string or offset. Tests include synthetic credentials, PII, English/Korean injection, NFKC/hidden characters, placeholders, license lineage, markup, deterministic reports and duplicate classification.
- The server reads every catalog candidate for review, not the capped user search. Checking, decision audit insertion and publication share one SQLite transaction. Unsafe approval leaves pending unchanged. Rejection stores the report; withdrawal preserves historical decisions and existing private-copy attribution.
- The additive idempotent `0003_contribution_reviews.sql` migration preserves existing records. A test changes both unsafe and clean private originals after submission and verifies decisions use the original snapshots; accepted reports survive Store reopen.
- Web review uses escaped text and explicit confirmation. The server repeats checks at approval. The integrated web now uses a separate allowlisted-email administrator realm (companion issue #402), an HttpOnly session and CSRF for writes. It restores after reload and has explicit sign-out/lock; no operator token is entered or saved in browser storage. CLI operator credentials remain a separate supported path. Owners can read safe findings for their own submissions; other owners cannot. The parent re-tested the final email-based administrator approval and rejection in Arise, then verified session restoration and sign-out.
- Accepted-decision reports describe historical review. An approved contribution can subsequently be withdrawn, so the UI labels that outcome “Approved at review.”

## Parent review and verification

The parent performed all builds, tests, browser actions, screenshot inspections and final code review. Initial failing tests were retained as regression coverage. Real HTTP/SQLite oracles independently confirmed Arise pending privacy, approved catalog visibility, separate-account private copies, preserved author/license/version, and blocked direct CLI approval.

Arise host forwarding repeatedly lost the private tab lease (#395). The task used the configured Arise stdio MCP server through one persistent client and a new owned window; all UI actions remained Arise native inputs. No Chrome fallback, desktop automation, real email delivery or production writes were used. Browser scroll also ignored the open modal and moved the page behind it (#404); only scrolling the known dialog was adjusted through browser_eval, then native clicks and live screenshots verified the action.

See the test report for exact final command results, artifacts, concurrent-work limitations, and the detached preview PID/log.
