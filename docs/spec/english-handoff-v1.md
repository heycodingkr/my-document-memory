# English experience and agent handoff v1

Status: implemented and verified, 2026-11-09. Fixes workspace issues #390 and #391 and makes the README, landing page, and primary product UI English by default.

## Contract

The template preview shows an English, selectable agent request built from the currently selected template, document title, reference IDs/versions, and section order. Copy prompt writes exactly that visible request to the clipboard. It never creates a document or sends credentials/reference body text. A blocked/unavailable clipboard selects the request and explains manual copying without claiming success. Blank titles, unsupported sheet creation, and unapproved deck outlines cannot produce an executable copy action. Deck approval is explicit and reversible.

Template/source titles and section labels are quoted data within structured JSON. Instructions tell the agent to verify expected versions, use only selected references, preserve citations, and flag missing facts. The request includes exact arguments for the existing document_memory_create tool; it does not claim that this app calls an LLM.

English templates generate English confirmation placeholders and evidence labels for documents and decks. Korean templates retain Korean draft labels. Other locales use an English fallback until their UI copy is localized. New custom/import-derived templates default to en-US. Nine English catalog entries use new .en IDs; existing .ko templates and saved versions are not rewritten. The template API filters locale before its result limit; the UI defaults to English and permits All languages/Korean.

The landing page, navigation, labels, validation messages, accessibility names, print/source labels, import location labels, metadata, and README are English. Demo input and output are English. README screenshots come from the actual updated app, with synthetic data. Existing generated artwork may be retained only if its embedded text fits the English presentation.

## Dependency-ordered atomic goals

| Order / route | Output | Independent parent check | Dependency |
|---|---|---|---|
| 1 inline | Git status/diff, relevant code/tests, issue claims, baseline snapshots | Read actual files, preserve concurrent work | none |
| 2 inline | This contract and test inputs/expected results | Compare to requested English UI and issue repros | 1 |
| 3a codex:gpt-6-luna attempt, then inline fallback | Initial five-file copy sweep; job 127 was queued and cancelled with no edits, completed by parent | Direct parent file review and checks | 2 |
| 3b codex:gpt-6-luna attempt, then inline fallback | Job 132 was queued and cancelled without starting; parent reviewed the three newly added account components and completed remaining English/filter changes | Direct source reads and integration tests | 2; newly observed account UI |
| 4 inline | Focused failing Rust and browser tests for both bugs | Run tests here and capture specific failures before implementation | 2 |
| 5 inline | Locale-aware drafts/catalog filtering and prompt preview/copy; English App/README | Review exact source changes and clipboard/approval behavior | 4 |
| 6 inline | Builds/tests, actual Arise smoke, English screenshots and exported demo | Parent runs workspace checks, isolated runtime/browser smoke and image inspection | 3,5 |
| 6b inline | Refresh this session's existing development supervisor after observing HTTP 400 for the new locale parameter on its old process | Same database/token retained; health, English HTTP search, installed CLI and configured MCP checked | 6 |
| 7 inline | Review, issue comments/status, verified know-how corrections | Evidence links and final diff; deployment state stated accurately | 6,6b |

No worker runs builds, tests, browser loops, production actions, commits, or credential reads. Worker scope was the explicitly named mechanical-copy files; both queued attempts were cancelled before starting, so no worker changes or summaries serve as evidence. App.svelte, README, store.rs, contracts, tests, CSS, design/root-cause decisions, and final review stay with the parent.

## Inputs and expected results

| ID | Input/action | Expected result |
|---|---|---|
| ENG-01 | en-US document template, English source and two sections | English confirmation paragraphs and Selected Source Excerpts heading; exact source citation/version |
| ENG-02 | en-US deck template and selected English source | English Needs confirmation labels and Evidence slide titles; outline approval remains required |
| ENG-03 | ko-KR template | Existing Korean confirmation/evidence behavior remains intact |
| ENG-04 | Reopen an existing DB after English catalog seeding | Nine new .en public entries plus unchanged .ko entries; no duplicate/private-record overwrite |
| ENG-05 | Template locale=en-US query, including >20 records in other locales | English matches returned because filtering precedes the cap |
| ENG-06 | Selected template, title and reference in preview | Readonly Agent prompt reflects exact IDs/expected versions and ordered sections; token and source body absent |
| ENG-07 | Click Copy prompt with browser clipboard permission | Actual clipboard equals visible prompt; no document-create request occurs |
| ENG-08 | Clipboard write rejects | Selectable prompt and explicit manual-copy message; no false success |
| ENG-09 | Deck preview before/after outline checkbox | Copy/create disabled until approved; copied JSON has outline_approved=true only after approval |
| ENG-10 | Empty title / sheet preview | Copy/create remains unavailable; supported behavior explained |
| ENG-11 | Fresh landing/library/custom form at desktop and mobile | English accessible UI and en-US custom template, no horizontal overflow |
| ENG-12 | Full document/deck workflows, auth errors, save conflict, validation recovery | Existing behavior passes with English labels/data |
| ENG-13 | Real Arise preview -> copy -> MCP create -> save -> download | Native clipboard content matches visible request; saved English document and valid DOCX |
| ENG-14 | README and updated screenshots | English prose/examples and actual English app renders; truthful current scope and working commands |

## Design and root causes

Issue #390: App.svelte's preview has library-object copy and create only. Add a separate visible request and clipboard action, preserving the distinction between copying a form and copying agent instructions.

Issue #391: store.rs hardcodes Korean document placeholders, evidence headings and deck evidence titles regardless of template.form.locale. Choose draft labels once from the template locale and use them consistently across both document families.

Current catalog has nine Korean seeds. Add English IDs rather than repurposing pinned Korean IDs or mutating persisted user content. Add optional locale filtering server-side before MAX_RESULTS, because filtering a truncated client list can hide valid English entries.

The initial workspace has substantial concurrent untracked implementation and new deployment/account specifications. Snapshot only relevant files, patch exact regions, avoid broad formatting/rewrites of unrelated sources, and stage/commit nothing.

A final shared-source run caught an outdated onboarding assertion after the concurrent landing changed its hero from outline text to an output preview. Keep the behavior contract: selecting Slides must show its deck example and link, while the separate copied request must still require outline approval. Update that assertion to inspect the actual current panel/link, then rerun the workflow suite here.

## Review and evidence

See [verification report](../test/english-handoff-v1.md) and [design review](../design/english-handoff-v1-review.md). Evidence is under .artifacts/english-handoff/. Public HTTPS now returns English and was visually inspected in Arise; the authenticated create/edit/export smoke used an isolated local library. This work did not perform the concurrent production rollout.
