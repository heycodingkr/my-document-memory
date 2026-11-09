# Landing: service identities and one-request / three-output demo

Date: 2026-11-09. Scope: the existing English Svelte landing. Preserve concurrent authentication, public memory, agent handoff, and library work.

## Problem and experience

The landing currently represents services with letters and static examples. Visitors have to infer how a single instruction becomes useful documents across familiar web tools.

Use recognizable service assets and make the user's example concrete: “Create a 10-slide deck in Google Slides, a one-page summary in Google Docs, and a promotional post about this project for Naver Blog.” Keep the established English interface. A short illustrative animation immediately below the hero shows that brief, shared template/reference context, and three distinct writing surfaces. It demonstrates the product concept; it does not connect accounts or publish content.

The deck must visibly progress to ten slides with distinct titles. The Docs output is a single-page executive summary. The Naver output is an unpublished promotional draft. Use one coherent synthetic project (My Document Memory) for all outputs. Show outline → writing → review, and preserve the shared outline, source, and voice premise. No invented timing/performance benchmark, customer, live generation claim, or automatic publication.

## Dependency-order atomic goals

| Slice / route | Output contract | Parent independent check | Depends on |
|---|---|---|---|
| 1 / inline | Current Git diff/status, Landing/App/test/harness inspection and this spec | Read actual source and current capability boundaries | None |
| 2 / `codex:gpt-6-luna`, background | Bounded collection of original service/company logo assets in `target/landing-brand-logos/`, with source manifest; no app edits or tests | Parent opens cited assets/manifests and confirms identity/source/MIME before adoption | 1 |
| 3 / inline | Local brand component and public assets, provenance notes | Parent inspects every used image and checks local asset loading | 2 |
| 4 / inline | Independent animated three-output component with brief copy, pause/play/replay, progress scrubber and reduced-motion behavior | Parent tests deterministic timeline states, controls, offscreen/hidden pause and no external writes | 1; logos from 3 |
| 5 / inline | Landing integration and actual service identities replacing letter placeholders | Parent reviews changed source, preserves existing interactions and English copy | 3, 4 |
| 6 / inline | Type check, production build, focused browser tests, relevant regression tests and responsive visual QA | Parent runs all verification and inspects screenshots; record exact limits | 5 |

The asset worker receives a bounded list and writes only its dedicated asset directory. Design, code changes, builds, tests, integration and final review stay with the parent. A summary is a pointer; inspect its actual files and originating sources before use. Reuse the existing development server at port 5174.

## Logo contract

- Prioritize original assets from official Google Docs / Slides, Naver Blog, Notion, Medium, OpenAI/Codex, Claude, and Arise sources. Muse may use an original verified asset if one is identifiable; retain a text label rather than inventing a product logo or mislabeling another Meta product.
- Self-host verified assets. No remote hotlinks, credentials, external scripts, tracking, or new dependencies. Keep logo identity/aspect ratio; decorative images next to service names have empty alt text.
- Record original URLs or exact local canonical paths in `web/public/brands/SOURCES.md`. Company logos identify compatible examples, not partnerships or endorsements.

## Animation contract

- No API write, external document, clipboard content other than the visible example, or account changes. Naver output is visibly a draft.
- Use browser-native Svelte/CSS/JavaScript. Three writing surfaces stay visible together on desktop and stack on narrow screens. The deck contains ten actual preview slides, not a counter over an unchanged placeholder.
- One finite timeline loops after a readable completion hold. Pause stops text/progress changes; replay resets the same synthetic content. A labeled progress control lets visitors inspect any stage.
- Advance only when the demo intersects the viewport and the document is visible. Clean up timers, media listeners and observers on unmount. Reduced-motion preference starts with a complete static preview and paused playback; explicit user playback remains possible.
- Keep announcements to meaningful stage changes. Do not announce every typed character. Controls are keyboard accessible and retain focus while the timeline changes.
- Copying the composite request reports success or a selectable manual fallback. Existing single-tool request and model selection keep working. Avoid conflicting accessible names/status selectors in the current onboarding tests.
- The hero's AI selection also labels the model in the animated flow, using its verified company mark when available.

## Inputs and expected results

| ID | Input/action | Expected result |
|---|---|---|
| DEMO-01 | Open landing unauthenticated | Hero and real service identities visible; composite brief mentions Slides 10, Docs 1 page, Naver promotional post |
| DEMO-02 | Seek to start / writing / completion | Waiting states → changing slide content and typed text → ten slides, one summary page, one unpublished blog draft |
| DEMO-03 | Play then pause, advance browser clock | Progress changes while playing; remains stable when paused; replay starts the same demo |
| DEMO-04 | Reduced-motion browser preference | Completed static output; autoplay paused; controls usable |
| DEMO-05 | Demo offscreen or document hidden | Timeline stops; resumes only when visible and playback enabled |
| DEMO-06 | Copy composite request; clipboard denied | Exact visible request copied, or selectable text/manual-copy feedback; no page errors |
| DEMO-07 | 1440px, 390px and 320px widths | Recognizable service panels, usable controls, no page overflow or clipped CTA |
| DEMO-08 | Fetch every used logo | Local valid image response, identity matches name, no broken images or required external requests |
| DEMO-09 | Existing onboarding + library/agent handoff regressions | Existing model/tool choices, connection, editing and saved/unsaved state remain intact |

## Verification record

- `pnpm --dir web check`: zero errors and warnings. `pnpm --dir web build`: passed; no dependencies added.
- `DMEM_E2E_OUTPUT_DIR=../.artifacts/landing-demo/regression python3 tests/smoke/runtime-v1.py --browser`: 21 browser tests passed, including all five new demo scenarios and existing onboarding, agent handoff, landing links and document/deck workflows. Three account tests were skipped by their existing `DMEM_E2E_MAILBOX` fixture requirement; the separate account harness was not exercised by this UI task.
- The same isolated run passed real HTTP authentication, CLI import/copy/create/export, MCP transport, save conflicts, immutable history and restart persistence.
- Direct image inspection: original assets for all eight identities; the 128px Arise rendition; completed and writing-state desktop renders; 390px and 320px layouts. Screenshots: `web/test-results/multi-output-demo-{1440,390,320}.png` and `multi-output-writing.png`.
- Asset origin review: six remote originals independently matched bytes from their recorded official URLs; the Arise original matched its canonical local file. The OpenAI mark was visually inspected and retains the recorded official favicon source; an independent repeat HTTP comparison was blocked by the origin. Muse remains text. All eight used images loaded as local image responses in the browser test.
- Playback review: advancing text and distinct slide content; manual slide inspection; pause/replay/seek; inactive/offscreen page pause; reduced-motion static completion; manual-copy fallback; selected AI label and mark; no POST or other writes in the demo scenario.
- Initial test corrections: request label matching uses `exact:true`; the clock scenario explicitly pauses before seeking Home, because an unchanged native range value does not emit an input event. Production behavior was not altered to fit those test assumptions.
- Integration review: the original letter placeholders are replaced with a reusable logo component; existing concurrent `AgentSetup`, public-memory/email entry points, English copy and navigation changes are preserved. App, API, authentication, deployment and production data were not modified by this task. Source was not staged or committed.
- Existing local preview reused at `http://127.0.0.1:5174/#workflow-demo`, PID 68076, log `/private/tmp/dmem-dev.log`.

## Production verification after deployment request

The user subsequently requested deployment. Live inspection found that the intervening release `/srv/my-document-memory/releases/20261109T022729Z-13901` already included this landing. Public HTTPS HTML, both linked JavaScript/CSS bundles and all eight logo files matched the current local production files byte for byte, so no redundant release switch or service restart was performed.

`DMEM_E2E_URL=https://mydocumentmemory.com DMEM_E2E_OUTPUT_DIR=../.artifacts/deploy/landing-production-browser pnpm --dir web exec playwright test tests/landing-demo.spec.ts` passed all five scenarios against the actual public origin. This covered the selected AI, complete and intermediate drafts, ten slide previews, playback/visibility controls, reduced motion, copying/manual fallback, local logos and desktop/390px/320px layouts. Tests did not send email or write production documents.

Final public health was `200 {"ready":true}`; existing email configuration remained enabled. Stable-release and SHA-256 evidence: `.artifacts/deploy/landing-production-verification.json`. Public demo: https://mydocumentmemory.com/#workflow-demo.
