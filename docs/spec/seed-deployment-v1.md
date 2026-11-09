# Seed library and HTTPS deployment v1

Requested 2026-11-09: create varied native Google Docs and Slides through Arise, download their Office originals, upload them as private source memories and reusable templates, connect mydocumentmemory.com and smoke the deployed application. Existing work and the local development database must be preserved. Synthetic examples only; no existing personal Drive documents are imported.

## Dependency ordered atomic goals

| Order and route | Output | Independent parent check | Dependency |
|---|---|---|---|
| 1 inline design and deployment discovery | Six original Korean form outlines, verified host and Cloudflare access | Inspect code, routes, DNS answers, running services and auth | none |
| 2 inline Arise Google Docs and Slides | Four Docs and two decks, saved privately in current account, Office downloads | Read saved titles and content, inspect rendered browser pages and downloads | 1 |
| 3 inline deployment packaging | Repeatable service configuration with loopback API, persistent SQLite, private connection token and static production web build | Build and run workspace tests here, inspect package and service configuration | 1 |
| 4 inline host and DNS deployment | Running isolated service and mydocumentmemory.com HTTPS reverse proxy | Real HTTPS health, unauthenticated 401, correct assets, Origin acceptance | 3 |
| 5 inline Arise uploads and memory creation | Six source records and six private reusable forms from the original downloads | Verify source bytes and SHA-256, titles, family, search, template links and reload persistence | 2,4 |
| 6 inline deployed smoke and review | Saved document and deck with pinned form/source versions and downloads, evidence report | Exercise actual public origin through Arise, inspect exports and restart persistence; review own diff | 5 |

No worker is assigned code, builds, tests, browser loops or production changes. A gathering task may be routed separately only with a bounded read-only spec and cited evidence opened by the parent.

## Seed content

Four document forms: meeting minutes, weekly work report, project proposal, handover checklist. Two slide forms: project kickoff and monthly business review. Each contains fillable placeholders, section guidance, synthetic example labels and no invented real commitments. Google creation and downloads are performed through the requested Arise UI. DOCX/PPTX preserve the downloaded originals. Current runtime imports text/structure rather than full native Office styling, and does not synchronize Google providers.

## Inputs and expected results

| ID | Input or action | Expected result |
|---|---|---|
| SD01 | DNS A/AAAA/CNAME for apex and browser HTTPS before deployment | Record current failure; currently no web address exists |
| SD02 | Six saved Google files and Office download actions | Six nonempty valid ZIP packages, four DOCX and two PPTX, recorded URLs and checksums |
| SD03 | GET /healthz over public HTTPS | 200 JSON ready true, valid certificate |
| SD04 | GET /v1/templates without token and with wrong token | 401 auth_required, no source data or token leaked |
| SD05 | Correct token plus Origin https://mydocumentmemory.com | Authenticated API works; a different origin is rejected |
| SD06 | Upload each original through web UI then save as form | Original bytes preserved, nonempty extracted blocks/slides, private form of matching family |
| SD07 | Search Korean seed title, reload and reopen | Same IDs, counts, structure and privacy preserved |
| SD08 | Create document with selected seed and source, edit and save | Correct pinned versions, saved revision increments, reload preserves edit |
| SD09 | Create deck after reviewing outline, export PPTX | Ordered slides, saved record and valid nonempty package |
| SD10 | Restart only the new application service | Health returns, six sources/forms and saved documents remain |
| SD11 | Existing workspace verification | cargo test --workspace, Svelte check/build and runtime smoke pass, unrelated edits preserved |

## Design and root cause

Initial inspection: runtime-v1 is a single-owner token-authenticated Axum/SQLite application. It intentionally binds loopback and accepts configured Origins. Deploy behind HTTPS reverse proxy without removing those safeguards, using a separate production DB and secret. The purchased domain delegates to Cloudflare but has no A answer; deployment needs both a running host route and DNS.

## Review and evidence

Pending execution. Record exact production route, service, release, test outcomes, Google URLs and imported IDs in docs/test/seed-deployment-v1.md. Do not record tokens or credentials.
