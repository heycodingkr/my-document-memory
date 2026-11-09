# Hero document examples v1

Requested 2026-11-09 after the initial domain deployment: show large visual examples of reports, presentation decks and worklogs in the hero and a dedicated section, with usable links. Keep the current English landing and existing account, agent-setup, model/tool selection and library interactions.

## Design

Use original repository-native SVG illustrations, matching the current forest, sage and paper palette. Each contains a clearly labeled fictional document, rather than only an abstract icon or empty outline. A weekly report shows summary, delivery status and next actions; a presentation shows a kickoff cover plus following slides; a worklog shows completed work and upcoming work. Mark the previews as illustrative. Do not imply benchmark results, autonomous provider synchronization or real customer data.

Create one static SVG sprite with three symbols and three standalone view fragments. The hero's existing Docs, Slides and Notion tabs render the matching large report, deck and worklog illustration. A directly adjacent examples section uses large linked previews: a full report on the left, a deck and worklog on the right; mobile stacks them. Every preview opens its matching public SVG view in a separate tab. Links must work without a login or connection token. Use descriptive accessible names, visible focus and responsive layouts.

## Dependency ordered atomic goals

| Route | Output | Independent parent check | Depends on |
|---|---|---|---|
| Parent design and current-file inspection | This contract and frozen scope for existing Landing | Read status/diff, Landing, current styles and tests | none |
| Read-only gathering through codex:gpt-6-luna | At most six source citations for existing Store migration and legacy-owner preservation | Parent opens cited code before any deployment decision; no worker edits, tests or production access | contract |
| Parent web/public/examples/document-examples.svg | Three original visual symbols and public SVG views in one asset | Parse XML; inspect actual browser rendering and all fragment links | contract |
| Parent DocumentPreview.svelte and targeted Landing edits | Enlarged hero previews, matching links and dedicated examples section | Type/Svelte check, keyboard/tabs, public page/link behavior, desktop/mobile visual QA | SVG |
| Parent focused browser checks | Independent coverage of public examples, valid image responses, view targets and no overflow | Run tests and inspect screenshots here | UI |
| Parent release validation and deployment | Compatible immutable release on mydocumentmemory.com | Build/test here; inspect relevant server code; validate any DB upgrade against a private copy first; production secrets and existing data preserved | UI/checks/gathering |
| Parent public smoke and review | Verified domain and review record | Arise public landing; original six sources/forms and two v2 examples still accessible by their IDs; valid HTTPS | release |

No design, source claim, browser loop, build, test, migration judgment or final review is delegated. Gathering is sent out because this is already a long session; its summary only locates evidence.

## Inputs and expected results

| ID | Input | Expected result |
|---|---|---|
| HE01 | Anonymous landing at desktop size | Large report in hero; a dedicated Report / Presentation deck / Worklog section, visible example links |
| HE02 | Hero Docs, Slides and Notion tabs by pointer and keyboard | Existing selected-tab behavior preserved; corresponding illustration and example URL change together |
| HE03 | Each example link, without auth | HTTP 200 SVG; the referenced standalone view exists and renders the correct example; no account or token required |
| HE04 | SVG XML | Three intended symbols/views, readable text, no scripts, external image/font dependencies or private Google URLs |
| HE05 | 1440x1000, 1440x614, 768x1024, 390x844 and 320x844 | No horizontal overflow, readable preview headings and captions, usable link targets; primary action remains reachable |
| HE06 | Existing model picker, copy request and sign-in/public-memory buttons | Existing behavior remains available |
| HE07 | Svelte/TypeScript and production build | No errors or warnings introduced; generated asset served correctly |
| HE08 | Existing production dataset through an upgraded release | Six source IDs, original bytes/checksums, six private form IDs/sections and two saved v2 documents with history remain intact |
| HE09 | Public mydocumentmemory.com and www after release | Valid HTTPS, root examples render, www redirects to apex, auth boundary remains enforced |

## Initial review

The working tree has substantial concurrent English/account/community changes. Existing production is /srv/my-document-memory/releases/20261109T011532Z on jason-4090, my-document-memory.service, loopback 3848, Caddy HTTPS. Initial deployment, six native Google originals, six private source/form records and two v2 example documents have already passed public API, browser export and restart-persistence smoke. Do not overwrite parallel work or silently replace the production DB. The current frontend's account APIs require compatibility review before deploying the current working snapshot.
