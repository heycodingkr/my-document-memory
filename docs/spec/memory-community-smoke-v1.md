# Private/public memory and contribution review smoke v1

Status: implementation contract, 2026-11-09. Scope: the current Rust/SQLite runtime, real CLI and stdio MCP binaries, and manual Arise Browser verification using synthetic accounts and an isolated database. WAM (`../web-agentic-memory`) is a read-only reference. Existing unrelated working-tree changes must be preserved.

## Dependency-ordered atomic goals

| Order / route / owner | Output contract | Independent parent check | Depends on |
|---|---|---|---|
| 1 / specification / parent | This contract; test input/expected-result table; design/root-cause/review record | Read runtime code, current diff and existing tests before changing product code | none |
| 2 / WAM reference gathering / codex:gpt-6-luna | Short read-only map of WAM contribution/review stages and cited file:line locations, no edits or verification claims | Parent opens cited source before accepting any behavior | 1 |
| 3 / private/public CLI and MCP / parent | Save/read private structures and document revisions; anonymous public search/read; explicit contribution submission/list/withdraw | Focused failing real-binary smoke, then independent HTTP and SQLite assertions | 1 |
| 4 / review pipeline / parent | Deterministic checks on the immutable submission snapshot; separate administrator decision; unsafe snapshots cannot be approved; pending stays private | Focused Router/Store tests, rejection and duplicate-decision negative controls | 2, 3 |
| 5 / web review / parent | Separate administrator review queue showing stages and snapshot, explicit approve/reject; contribution feedback | Arise actions and resulting HTTP/DB state, ordinary-user denial | 4 |
| 6 / smoke and review / parent | Repeatable smoke runner; recorded CLI/MCP/Arise results and limitations | Parent builds, runs tests, inspects images, reviews final diff | 3, 4, 5 |

These are behavioral slices, not a request to implement the entire future gatekeeper/model/worker specifications. The existing `gatekeeper-preflight-v1.md` defines deterministic privacy, license, duplicate and structure policy. Reuse an available implementation where possible; keep administrator approval separate from preflight. Keep source files/document bodies out of public contribution snapshots. Do not publish synthetic records to production.

## Behavior

- Private writes require an authenticated owner. Saved documents keep immutable revisions and reject stale `base_version`. Other owners receive the same not-found result as a missing record.
- Public search/detail work without a library token. Copy requires a private owner and preserves author/license/version. A pending, rejected or withdrawn contribution is absent from public reads.
- Submission requires an explicit public author, license and rights confirmation. Submit a version-pinned structure snapshot, never imported file bytes or document content. Changes to the original after submission cannot change that snapshot.
- Review displays the immutable snapshot and fixed-code deterministic findings in order R0 snapshot/consent → R1 privacy/injection → R2 license → R3 duplicates → R4 structure → R5 human decision. The implemented policy is `contribution-review-v1`, distinct from the future read-only `preflight-v1` contract. Findings are `block` or `review`; verdict is `blocked`, `needs_review` or `ready`. Exact/near duplicate structures require human judgment and are advisories, preserving the existing licensed derivative/re-contribution contract. Privacy, injection, license and invalid structure block approval. Re-run checks at approval against all current public records within the publication transaction. Reject unsafe approval with 422 `review_blocked`, preserve pending status, and return fixed error codes. A passing check does not itself publish. Persist the decision/report/hash/time for owners and administrators; report findings never echo matched values.
- An ordinary library/account credential cannot use administrator routes. Operator secrets are never stored in localStorage/sessionStorage or printed in results. The integrated web uses allowlisted email sign-in and a separate HttpOnly administrator session, restored after reload and explicitly revoked by sign-out. Review actions use the configured local/authorized origin.
- MCP input validation rejects unknown fields and unsafe IDs. Protocol framing and existing tools remain compatible. Public-only MCP operation can start without a private token; private tools fail with `auth_required`.

## Runtime interface contract

| Operation | HTTP | CLI | MCP |
|---|---|---|---|
| Save/read a private structure | POST /v1/templates; GET /v1/templates/{id} | template-save <JSON>; template-show <ID> | document_template_save; document_template_get |
| Save a document revision | PUT /v1/documents/{id} | save <ID> <JSON> | document_memory_save |
| Anonymous public search/detail | GET /v1/public/templates[?q=...]; GET /v1/public/templates/{id} | public-templates [QUERY]; public-template <ID> | document_public_template_search; document_public_template_get |
| Submit/list/withdraw | POST/GET /v1/me/contributions; POST /v1/me/contributions/{id}/withdraw | contribute; contributions; withdraw | document_contribution_submit; document_contribution_list; document_contribution_withdraw |
| Own submitted-snapshot checks | GET /v1/me/contributions/{id}/review | contribution-check <ID> | document_contribution_check |
| Administrator queue/check/decision | GET /v1/admin/contributions; GET /v1/admin/contributions/{id}/review; POST /v1/admin/contributions/{id}/decision | review-queue; review <ID>; decide <ID> --decision approve\|reject | Administrator tools are separate from the private MCP adapter |

Submission body: `{template_id, author, license, rights_confirmed:true}`. CLI requires explicit `--author`, `--license`, and `--rights-confirmed`; the server independently enforces consent, ownership and license. Decision body: `{decision:"approve"|"reject"}`, unknown fields rejected.

The report contains `schema_version:1`, `policy:"contribution-review-v1"`, contribution ID, snapshot version, SHA-256 of the complete serialized snapshot, verdict, sorted unique reasons/findings, six ordered stages, and nullable decision/time. Findings contain only rule/field/fixed code/reason/action. The accepted decision, report and timestamp are inserted into `contribution_reviews` in the same SQLite transaction as the public catalog change. Repeat decisions conflict with 409; blocked approval returns 422 `review_blocked` without changing pending state.

R0 relies on the existing submission gate (authenticated owner + explicit rights confirmation + immutable structure snapshot), and checks the snapshot shape. This extension does not add a separate versioned consent ledger. R1 scans title, summary, sections, tags, submitted author, inherited attribution authors, and form variant after NFKC and hidden-character removal. R2 preserves CC BY attribution licensing; R3 uses normalized structure/form comparison over all catalog records, without the user-search result cap; R4 validates field limits, markup/control characters and normalized form; R5 is the explicit administrator decision. Final checking happens at decision time; a later edit to the private original cannot change the submitted snapshot.

Same-origin browser GETs omit Origin. Administrator reads still require the separate credential, validate any supplied Origin, and allow an absent Origin. Administrator writes always require the configured allowed Origin. CLI defaults its administrator Origin to DMEM_URL; set DMEM_ORIGIN explicitly when the web and API origins differ. The integrated web reviewer uses the separate allowlisted-email administrator realm and HttpOnly session cookie. Its session restores after reload, and Sign out and lock queue revokes it. Browser localStorage/sessionStorage contains no operator token. CLI operator-token access remains supported separately.

This extension adds nine tools to the original seven; the integrated runtime also includes document_memory_recall, for 17 tools. tools/list is the authoritative current inventory. The existing newline frame limit remains 64 KiB; larger document revision payloads can use CLI/HTTP. These runtime tool names and this review policy are distinct from the broader future doc_memory_* and preflight-v1 specifications. Model/curator judgments, replay workers, takedown management and automatic publication are outside this extension.

## Verification artifacts

See `docs/test/memory-community-smoke-v1.md` for inputs and expected results and `docs/design/memory-community-smoke-v1-review.md` for design, root causes and review. Results are added only after parent execution.
