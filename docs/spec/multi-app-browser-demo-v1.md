# Multi-app Arise demo smoke

Date: 2026-11-09. Scope: live Arise Browser checks for one request producing a Google Slides deck, a Google Docs one-page overview, and an unpublished Naver Blog post. No product code changes. Preserve other sessions' files, tabs, documents and issue claims.

## Input and output contract

Use English synthetic My Document Memory project content, based on inspected repository documentation. Prefix new private test artifacts with `MDM Demo QA`. The target is ten short slides, one overview page, and one blog draft. Do not claim a native product integration from a browser-agent success. Do not publish a blog post, share documents, change account settings, or modify existing documents.

Initial forwarded browser session: `dmem-demo-20261109-qa-7138`. The verified fallback keeps one public Arise stdio MCP connection with session `dmem-demo-persistent-20261109-7138`. Create dedicated owned windows. Browser interaction, judgments and verification remain inline. Authentication uses an existing signed-in session or a sole matching saved account; do not invent credentials. Record unavailable authentication as a blocker and continue independent checks. This smoke does not establish that Arise's built-in AI completes the composite request from one prompt.

## Dependency-order atomic goals

| Route | Output | Independent direct check | Depends on |
|---|---|---|---|
| G0 / inline | Current Git status, existing demo/handoff docs and issue list; this contract | Read actual local documents; distinguish historical failures from live state | None |
| G1 / inline | Separate owned Docs, Slides and Naver windows; actual authentication/editor state | Snapshot each destination after navigation, record window/tab IDs | G0 |
| G2 / inline | Synthetic deck, one-page overview and unpublished post wherever editor access permits | Read editor content and save indicators; inspect screenshots for canvas/page layout | G1 for each app independently |
| G3 / inline | Window-switch and persistence checks | Re-select each exact owned tab, confirm content belongs to its app; reopen saved outputs where safe | G2 for each app independently |
| G4 / inline | Reproduction steps, observed limits, demo readiness and issue registration | Review direct tool evidence; report blocked and untested portions separately | G1–G3 |

## Test inputs and expected results

| ID | Action/input | Expected result |
|---|---|---|
| MAB-01 | Open each service in a new owned Arise window | Three distinct windows/tabs, correct final URLs; other tabs untouched |
| MAB-02 | Check each app's login/editor | Signed-in editable surface, or an explicit reproducible auth/account blocker |
| MAB-03 | Create `MDM Demo QA — My Document Memory Deck` | Ten slides with distinct titles, readable content and a saved document URL |
| MAB-04 | Create `MDM Demo QA — One-page Overview` | English overview fits one page, correct title/body, saved document URL |
| MAB-05 | Create `MDM Demo QA — One brief, three documents` | English title/body in Naver editor; draft persisted without publication |
| MAB-06 | Switch Slides → Naver → Docs → Slides | Exact selected target verified before input; no cross-app edits |
| MAB-07 | Reopen saved Docs/Slides; reopen draft if safely available | Title and representative body text persist; slide/page counts verified |
| MAB-08 | Inspect failure state once and try a bounded supported alternative | Concrete reproduction, underlying observed error and next prerequisite; no repeated login/captcha attempts |

## Verification method and limits

This is a live authenticated browser smoke, not a fixture/unit test. Login state, third-party editors, native canvas input and server-side persistence require actual Arise interaction. Preserve snapshots and relevant screenshots in `.artifacts/multi-app-browser-demo/` when available. Run no unrelated build/test suite because this task changes no product code. A browser tool dispatch response alone does not prove editing or saving; verify the resulting editor/server state. Record results in `docs/test/multi-app-browser-demo-v1.md`.
