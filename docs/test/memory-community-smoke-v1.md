# Private/public memory and contribution review: test inputs and expected results

Contract: [memory-community-smoke-v1](../spec/memory-community-smoke-v1.md). Use a temporary SQLite database, random loopback port, synthetic Alice/Bob owners, a separate synthetic administrator token and `example.test` mail capture. Never use production credentials or real user data in fixtures.

| ID | Input / action | Expected result / independent oracle |
|---|---|---|
| MC-01 | CLI saves a synthetic private template JSON; MCP reads it | Same ID/version/sections; visibility private; HTTP/SQLite owner matches Alice |
| MC-02 | MCP creates a private template; CLI reads it; Bob queries ID/list | Alice can read; Bob list omits it and ID returns not_found |
| MC-03 | CLI creates document, MCP saves revision at base_version=1, CLI reads; repeat stale save | Version 2 with edited content; stale save version_conflict; revision 1 unchanged |
| MC-04 | CLI and MCP public search/detail with no DMEM_TOKEN | Same public seed ID, version, author/license; private read/write auth_required |
| MC-05 | CLI contribution without rights flag, then valid explicit rights/author/license | First rejected; valid snapshot pending, own list includes it, anonymous detail/list cannot see it |
| MC-06 | MCP submission and list; Bob submits Alice ID or withdraws it | Own valid submission works; cross-owner actions not_found |
| MC-07 | Ordinary token requests administrator queue/check/decision | auth_required; no public record or changed status |
| MC-08 | Admin checks clean unique structure and approves; anonymous search/read then Bob copies | Ordered checks pass, pending until decision; approved public snapshot; private copy preserves attribution and source version |
| MC-09 | Submit synthetic email, API-key marker or instruction injection; admin tries approve | Findings contain codes only, no matched value; approve denied; no catalog record |
| MC-10 | Submit an exact duplicate of a public structure; check and explicitly reject | Duplicate finding, needs_review verdict; pending remains private until human decision; rejection persists |
| MC-11 | Repeated decision, rejected submission, withdrawal after approval | Repeated decision version_conflict; rejected not public; withdrawal removes public reads/new copies, existing private copy retained |
| MC-12 | Arise: synthetic sign-in → private save/read → contribute → review queue → approve → public preview/copy | Visible saved/private state and pending status; explicit admin action; resulting public attribution; HTTP/DB agree with visible state |
| MC-13 | Arise: ordinary credential denial, allowlisted administrator email, blocked contribution, explicit reject, refresh/sign-out | Error visible; unsafe approve unavailable/rejected; reject persists; no secret saved in local/sessionStorage |
| MC-14 | Existing runtime smoke + Rust workspace + Svelte check/build | Existing document/source/import/export, protocol framing and account isolation continue passing |
| MC-15 | Put `AKIAABCDEFGHIJKLMNOP` in turn in `title`, `summary`, `author`, `sections[0]`, `tags[0]`, `origin.author`, and `attributions[0].author` of an otherwise valid public snapshot | For each input, `review_snapshot` returns `blocked`, includes `R1/secret/aws_access_key` at the exact field path, and serialized findings contain no marker. Keep values within each field's length limit. |
| MC-16 | Review a clean snapshot whose summary contains the Luhn-invalid card-like value `4111 1111 1111 1112` | Verdict stays `ready`; no `card_number` finding. This is the negative control for checksum detection. |
| MC-17 | Submit a private template with `tags: ["AKIAABCDEFGHIJKLMNOP"]`, then request its admin review and attempt approval | Review returns `blocked` with `tags[0]` and fixed codes only; approve returns 422 `review_blocked`; the contribution remains pending and anonymous public lookup returns 404. HTTP response and SQLite catalog are the independent oracles. |
| MC-18 | CLI/MCP IDs `.` and `..`, valid seed ID `meeting.minutes.en` | Dot-segment IDs return invalid_input before HTTP URL normalization; a dotted seed ID remains valid. |

## Dependency-ordered test goals

| Order | Route / output | Independent parent check | Depends on |
|---|---|---|---|
| 1 | Specification: MC-15–17 input values, exact field paths, codes, HTTP status and visibility expectations | Compare cases with the current review implementation, API handlers and existing tests before edits | none |
| 2 | Core review tests: exhaustive descriptive-field privacy sweep plus Luhn negative control | Run the test against the pure `review_snapshot` function; assert verdict, exact finding path/code and serialized redaction | 1 |
| 3 | Server review route: unsafe tag survives submission only as a private pending snapshot, is blocked at review/approval, and never reaches public catalog | Exercise real Router + temporary SQLite; inspect response JSON, contribution status and catalog query independently | 1, 2 |
| 4 | Parent review: run focused Rust tests, inspect final diff and confirm test input/output still match the spec | Parent opens changed source and test lines and verifies the negative control protects against false positives | 2, 3 |

## Execution results

Focused review tests passed:

- `cargo test -p dmem-core --test review`: 6 passed.
- `cargo test -p dmem-server --test contribution_review`: 6 passed.
- Latest `cargo test --workspace`: passed.

The first workspace run overlapped with issue #402 being integrated and reported transient route and seed-count failures. The final integrated run passed all 93 Rust tests; administrator email sessions are now wired through the shared authorization helper to the same deterministic review/decision path. The parent additionally verified that final email-authenticated path in actual Arise and independently checked SQLite and anonymous HTTP.

### Final parent-executed verification — 2026-11-09

| Check | Result |
|---|---|
| Workspace and account-fixture builds, locked dependencies | PASS |
| Rust workspace | 93 passed; focused review tests 6 core + 6 server |
| Rust formatting | PASS |
| Svelte check and production build | PASS, 0 errors / 0 warnings |
| Real CLI/MCP community smoke | PASS MC-01–11, including independent HTTP/SQLite checks |
| Account/review Playwright subset | 5 passed, including email-admin approval and unsafe rejection |
| Editor/agent/onboarding browser regressions | 13 passed; HTTP/CLI/MCP, conflicts, immutable history and restart also passed |
| Actual Arise Browser | PASS private save/read, contribution, pending privacy, review, public read/copy, owner isolation, unsafe block/reject, administrator email, reload and explicit sign-out |

No production contribution was published or real mail sent. All accounts and reviewer addresses were synthetic `example.test` fixtures.

Arise sequence:

1. Signed in **arise-smoke-alice@example.test** with a captured synthetic link, saved **Arise Smoke Review Notes**, previewed its sections and submitted with explicit author, CC-BY-4.0 and rights confirmation. UI showed Awaiting review; anonymous public detail returned404 and unauthenticated private API returned401.
2. Verified ordinary credentials were denied administrator access. Inspected R0–R5, confirmed and approved. SQLite contained the accepted report/hash, and public detail returned200.
3. Signed out and searched/previewed anonymously. Signed in **arise-smoke-bob@example.test**; its private library initially had zero templates. Copied the public structure and independently verified a separate private record with the original public ID/version/author/license.
4. Submitted a synthetic email-containing structure through the CLI. Arise kept approval disabled after confirmation; forced CLI approval returned `review_blocked`. Explicit rejection persisted, public detail stayed404, and safe findings did not echo the matched value.
5. Re-tested the final integrated administrator email flow in a fresh owned Arise window. Captured the allowlisted **reviewer@example.test** link, explicitly confirmed it, approved **Arise Email Review Notes** (public200), and blocked/rejected **Arise Email Blocked Fixture** (public404). Verified administrator restore across a real reload, then signed out and locked the queue.

The parent inspected the actual Arise-returned screenshots. MeshCode forwarding lost tab leases (#395), so the configured Arise MCP server was kept in one persistent parent-owned client. A fresh owned window also resolved native clicks that acknowledged dispatch without changing an older window. Modal scrolling required scrolling the known dialog because the tool moved the background page (#404). All form input and decisions used native Arise input; no Chrome or desktop fallback was used.

Local run evidence in `target/community-arise-20261109/`:

- [Final checks](../../target/community-arise-20261109/verification.json), per-command `*.log`, and [safe Arise snapshots](../../target/community-arise-20261109/arise-steps.json).
- [Pending/private oracle](../../target/community-arise-20261109/pending-oracle.json), [approval oracle](../../target/community-arise-20261109/approved-oracle.json), [separate-account copy oracle](../../target/community-arise-20261109/copy-oracle.json), [unsafe rejection oracle](../../target/community-arise-20261109/unsafe-oracle.json), [final email-review oracle](../../target/community-arise-20261109/email-review-oracle.json).
- [Private template](../../target/community-arise-20261109/private-template.png), [private-copy attribution](../../target/community-arise-20261109/public-copy.png), [final review stages](../../target/community-arise-20261109/review-ready-email.png), [unsafe approval disabled](../../target/community-arise-20261109/review-blocked-email.png).

### Re-run

```sh
cargo build --workspace --locked
cargo build -p dmem-server --example accounts_fixture --locked
pnpm --dir web build
python3 tests/smoke/community-v1.py
DMEM_E2E_TESTS='accounts.spec.ts review.spec.ts' python3 tests/smoke/accounts-v1.py
python3 tests/smoke/runtime-v1.py --browser \
  --browser-spec workspace.spec.ts \
  --browser-spec agent-handoff.spec.ts \
  --browser-spec onboarding.spec.ts
```

Arise additionally requires the actual configured browser; Playwright results alone are not Arise verification. Office application rendering, model/curator/replay workers, production publication and the entire unrelated web suite are outside these measurements. Queue pagination/status filtering for more than100 historical submissions was fixed in #407: database filtering precedes the page limit, the UI loads subsequent pages, and CLI exposes status/limit/cursor. See [the dedicated regression and Arise results](review-queue-pagination-v1.md).

### Kept local preview

http://127.0.0.1:3856/ — detached PID85846; synthetic DB `target/community-arise-20261109/library.sqlite3`. Log: `/var/folders/hn/4d_172w53_58g8kg255mlw_w0000gn/T/meshcode-detached-51535-1794195760518.log`. Only owned older preview processes were stopped for binary updates; the final preview outlives the turn.

