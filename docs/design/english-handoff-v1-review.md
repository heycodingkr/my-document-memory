# English experience and agent handoff review

Reviewed 2026-11-09 against [the contract](../spec/english-handoff-v1.md). Issues #390 and #391 are addressed in source and verified through the real runtime.

## Root causes and decisions

| Finding | Cause | Change and independent check |
|---|---|---|
| A template could be copied, but its agent request could not be viewed or copied | The preview only offered library-object copying and deterministic creation | `prompt.ts` builds a visible request; `AgentPrompt.svelte` owns clipboard feedback. The browser test reads the real clipboard, compares it to the textarea, and watches for unintended document POSTs. |
| English drafts contained Korean confirmation/evidence labels | Draft generation used fixed Korean strings regardless of template locale | Choose labels once from `template.form.locale` for both documents and decks. Rust tests verify English document/deck output, citations, and retained Korean behavior. |
| English forms could disappear behind a capped Korean result list | Locale was not part of server-side template filtering | Optional locale filtering happens before `MAX_RESULTS`. The regression adds more than 20 other-language templates and still retrieves the English match. |
| Reusing Korean seed IDs would change saved expectations | Templates and documents record IDs and versions | Seed nine new `.en` IDs with insert-if-absent behavior. Reopening the database preserves existing Korean/private records and avoids duplicates. |
| Clicking a card after changing lists could open the previous item | Reused list DOM and interactive stale results during refresh | Key template/source/document cards by ID and disable preview controls while loading. Existing generation counters reject stale responses. The document workflow verifies the opened template title. |
| Added language/visibility filters overflowed narrow screens | Search controls could not wrap | Allow search rows and public search controls to wrap, with shrinkable inputs. Browser checks cover 320/390px widths. |
| Installed commands still rejected the new locale query | The old development process was still running | Back up the library and restart only this session's supervisor. Verify English HTTP/CLI/configured MCP results and byte-for-byte preservation of all previous database rows. |

## Request boundary

The request contains the title, template metadata, ordered sections, reference IDs/expected versions/titles, and exact `document_memory_create` arguments. It contains neither the library token nor reference bodies. Metadata is quoted JSON data; instructions ask the connected agent to verify versions, use selected references, preserve citations, and flag missing facts.

Copying a prompt does not create a document. Blank titles and unapproved deck outlines disable the copy action. Spreadsheet previews explain their creation limitation. A denied/unavailable clipboard selects the request for manual copying and does not report success. Changes to the request clear obsolete success feedback.

Expected versions are advisory preflight instructions for the agent. The existing creation API accepts IDs and pins the versions it reads transactionally; this change does not add atomic expected-version arguments or promise protection from a version change between agent preflight and creation.

The runtime still creates deterministic outlines with selected excerpts. Model generation and work inside external document services require the connected AI host. README and landing examples distinguish product direction from these runtime capabilities.

## English presentation

The primary app, accessibility labels, validation errors, import/export location labels, custom-template defaults, metadata, catalog defaults, README, and synthetic document demo use English. Korean templates remain selectable with their original IDs and content. Other locales currently use English draft-label fallback.

README keeps the existing vision and external-workspace examples, explains CLI/MCP installation and limitations, and uses actual English library/editor screenshots. The hero illustration remains identified as a concept. The public English landing was separately inspected in Arise; its screenshot is retained as local evidence.

## Review scope and concurrent work

Source review covered the prompt formatter/component, App integration and list refresh behavior, API locale arguments, server draft labels and seeding, shared search contract, copy-only helper changes, responsive CSS, tests, and README. Builds, tests, browser input, visual inspection, and all implementation judgments ran in the parent session.

Delegation attempts 127 and 132 targeted `codex:gpt-6-luna`, the first permitted backend. Both were cancelled while queued, confirmed never to have started, and produced no changes. The parent completed the mechanical sweep and read the new account UI directly.

Other sessions added account/community features, the expanded landing/demo, email links, tests, and a commit during this work. Those changes were preserved. The saved baseline patch therefore includes concurrent additions and is not an isolated ownership diff. This session staged and committed nothing.

The final whitespace scan found a trailing blank line in concurrent `tests/smoke/cases/fmt.py`; it is outside this change. Owned text files passed the whitespace scan. See [verification](../test/english-handoff-v1.md) for passed checks and the bounds of native/public testing.
