# English experience and agent handoff verification

Date: 2026-11-09. Result: the scoped English experience, agent handoff, existing document/deck workflows, and default installed connection passed. See [contract](../spec/english-handoff-v1.md) and [design review](../design/english-handoff-v1-review.md).

## Reproduction before implementation

| Issue | Focused input | Observed failure | Evidence |
|---|---|---|---|
| #390 | Open a template preview and read its Agent prompt | No labeled request existed | [Browser RED log](../../.artifacts/english-handoff/red-ui.log) |
| #391 | Create from an en-US template with English references | Draft labels used Korean instead of `{{Needs confirmation: Purpose}}` | [Rust RED log](../../.artifacts/english-handoff/red-rust.log) |
| Stale local runtime | Request `/v1/templates?locale=en-US` from the installed default library | HTTP 400 from the old running process | [Before restart](../../.artifacts/english-handoff/default-runtime-before.json) |

The browser reproduction initially hit an overly broad test selector; it was corrected before recording the missing-prompt failure. That harness error is not treated as product evidence.

## Automated results

| Check | Result and coverage |
|---|---|
| `cargo test --workspace --locked` | **33 passed**: core 9, MCP 3, accounts 9, English 5, library 4, public provenance 3 |
| `pnpm --dir web check` | **0 errors, 0 warnings** |
| `pnpm --dir web build` | **Passed**, 136 modules transformed |
| Scoped runtime/browser regression | **13 passed** in 9.4s: agent handoff 5, workspace 3, onboarding 5 |
| Runtime harness | HTTP authorization, installed CLI import/copy/create/export, MCP transport, conflicts, immutable revisions, and persistence across owned-server restart passed |
| Default installed CLI/configured MCP | English Meeting template returned through both installed CLI and registered MCP tools |

The five English Rust tests cover English document/deck labels and citations, deck approval, preserved Korean labels, additive/idempotent seeds, and locale filtering before the result limit. Browser checks cover exact visible-request/clipboard equality, no create side effect, clipboard rejection/manual selection, deck approval reversal, blank titles, public English/Korean filters, custom en-US defaults, English UI, and narrow layouts.

The closing shared-source run caught an obsolete onboarding assertion after a concurrent landing change moved outline text out of the hero panel. The test now verifies the selected deck preview/link and separately retains the copied request's outline-approval assertions. All 13 scoped workflows then passed. The complete earlier run, including that failure, is retained in [shared-source checks](../../.artifacts/english-handoff/shared-source-checks.log); the passing rerun is [verified workflow](../../.artifacts/english-handoff/verified-workflow.log).

The browser run explicitly selects `agent-handoff.spec.ts`, `workspace.spec.ts`, and `onboarding.spec.ts`. It does not certify every concurrently added browser suite or actual email delivery.

```sh
cargo test --workspace --locked
pnpm --dir web check
pnpm --dir web build
python3 tests/smoke/runtime-v1.py --browser \
  --browser-spec agent-handoff.spec.ts \
  --browser-spec workspace.spec.ts \
  --browser-spec onboarding.spec.ts
```

## Real Arise and installed MCP smoke

All references and document content below are synthetic and English.

1. Opened the running English landing/library in an owned Arise window and inspected screenshots.
2. Previewed `meeting.minutes.en` v1, entered **Northstar Pilot Review**, and selected **Northstar Pilot Notes**.
3. Clicked **Copy prompt**, observed success, then used native **CMD+V** into an unsaved textarea. The pasted value exactly matched the visible request; the unsaved form was cancelled.
4. Parsed its JSON and passed the exact `create_arguments` to the installed `/Users/jason2/.cargo/bin/dmem-mcp` against the same isolated library.
5. Created `doc_f5b0630b07bc4ec2959dcb37a8b7c839` v1. Checked English confirmation/evidence labels and citations before editing.
6. Edited the purpose and fictional review details in Arise and saved **v2**.
7. Clicked DOCX export. Arise reported a completed download with a real existing file, **1,919 bytes**.
8. Validated the ZIP, parsed every XML/relationship part, and checked the title, English labels, review date, and absence of Hangul in document text. An independent CLI read confirmed saved v2.

[Copied website request](../../.artifacts/english-handoff/native-agent-prompt.txt) · [Creation arguments](../../.artifacts/english-handoff/create-request.json) · [English DOCX](../../.artifacts/english-handoff/Northstar-Pilot-Review.docx) · [Native verification](../../.artifacts/english-handoff/native-verification.json)

DOCX SHA-256: `199927c661ff6d2118e7dd4aad96d4dd820cf691cdd20af1d37eea984e82797f`.

The web editor was visually inspected. Native Word/PowerPoint page rendering was not tested. A later native reload observation timed out after export; it is not counted as a successful reload. The saved revision was independently read through CLI, and the automated document reopen workflow passed.

## Public domain and screenshots

`https://mydocumentmemory.com/` returned **HTTP 200** with `lang=en`. An owned Arise window displayed the English heading **Any model. Your standard.**, navigation, workflow example, and sign-in entry. [HTTP result](../../.artifacts/english-handoff/public-final.json) · [Arise observation](../../.artifacts/english-handoff/public-arise-snapshot.json).

README screenshots are actual captures: [public landing](../assets/landing-en.png), [English library](../assets/library-en.png), and [saved English editor](../assets/editor-en.png). The existing hero artwork is identified as a concept.

Another session deployed the public English release during this work. This session did not change production services or DNS. The authenticated create/edit/export smoke used the isolated local runtime; production private access and email delivery are outside this result.

## Running local environments

| Environment | Address | Process/log |
|---|---|---|
| Updated default web/API, used by configured CLI/MCP | Web `http://127.0.0.1:5174`; API `http://127.0.0.1:3847` | Detached supervisor **21179**; `/var/folders/hn/4d_172w53_58g8kg255mlw_w0000gn/T/meshcode-detached-51535-1794191722296.log` |
| Frozen synthetic demo preview | `http://127.0.0.1:52263` | Detached server **3660**; `/var/folders/hn/4d_172w53_58g8kg255mlw_w0000gn/T/meshcode-detached-51535-1794190370227.log` |

Before restarting the default supervisor, its library was backed up privately. All existing rows remained byte-for-byte unchanged: records increased **13 → 22** only from nine English seeds; revisions remained **2**, source files **1**. The English-filtered list also contains existing private English templates, so its total is **11**, including **9 public** seeds. [Default runtime verification](../../.artifacts/english-handoff/default-runtime-verification.json) · [Configured MCP verification](../../.artifacts/english-handoff/default-mcp-verification.json).

Browser leases were released and the public stdio adapters closed. Local servers remain detached for review. Tokens/private configuration and runtime databases are ignored by Git.
