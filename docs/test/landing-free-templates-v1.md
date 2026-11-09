# Free templates and lightweight AI: inputs and expected results

Status: acceptance defined before implementation, 2026-11-09. Spec: ../spec/landing-free-templates-v1.md. Issue #399.

| Input / action | Expected result |
| --- | --- |
| Read README from product examples through How it works | A middle section connects free templates, lightweight AI including Luna, and Google Docs / Google Slides / Notion |
| Read the landing between How it works and service examples | A visible section explains those three benefits and offers Browse free templates |
| Follow the described output routes | DOCX → Docs; PPTX → Slides; Markdown → Notion. Direct service editing still depends on compatible host/browser tools |
| Read the cost explanation beside those benefits | Free template reuse and free document-editing options are explicit; AI host/model/API charges and service plan limits remain provider-dependent |
| Open the evidence disclosure with keyboard Enter or Space | Native details opens, showing WAM/Canva attribution, Luna/max, source date and link, observed 474 s / 123 versus 423 s / 106, and both successful runs |
| Read evidence limits in README and the open disclosure | One run per condition, differing template/upload paths, higher reported tokens and unmeasured billing are retained; DMEM writing benchmarks are pending |
| Click Browse free templates while anonymous | The existing public template catalog opens; no new auth mechanism or provider action is introduced |
| View 1440×1100, 768×1024, 390×844 and 320×844 with evidence closed and open | Cards and text remain readable, links/button usable, and no document horizontal overflow or clipped content |
| Read the English page with its native-language locale switch | Main/footer content remains English; the intentional 한국어 switch label is allowed. Exact accessible-label matching distinguishes the request from its copy button |
| Switch between English and Korean and reload | The new benefit cards, cost explanation, action and evidence follow the selected language and retain their behavior |
| Compile the concurrent localization files | Reproduction: TypeScript parser rejects malformed locale-object closures; Svelte rejects duplicate style tags. Minimal delimiter corrections produce 0 TypeScript parse errors and 0 Svelte compile warnings |
| Run current landing-link, demo and hero-example regressions | Existing navigation, setup/copy, illustrative demo, tabs and output examples remain functional |
| Run Svelte check and production build | No check errors or warnings; production build succeeds |
| Review the scoped patch against baseline snapshots | Only the requested additions and their styles change in README/Landing; other sessions' existing changes are preserved |

This is a reversible content/UI addition. Reuse existing regression tests and focused browser/visual checks instead of adding persistent tests that merely assert copy strings.

## Results

Verified on 2026-11-09.

| Check | Observed result |
| --- | --- |
| Baseline and final shared-tree `pnpm --dir web check` | 0 errors, 0 warnings on both recorded successful runs |
| Isolated FreeTemplates component type/Svelte check | 0 errors, 0 warnings |
| Final `pnpm --dir web build` | Passed; `index-ByOVtp4U.css` and `index-5zXvCiG1.js` |
| Existing landing-link, language, demo and hero-example regressions | 16 scenarios validated: 15 passed together; the remaining English-content case passed on targeted rerun after allowing the intentional native-language switch label |
| Focused browser QA | Both languages at 1440, 768, 390 and 320 pixels; no page/section horizontal overflow, no page errors, three cards and all format routes present |
| Keyboard and link behavior | Enter/Space opens/closes evidence; report uses the pinned source; official links have safe new-tab attributes |
| Browse free templates action | Existing anonymous public-library view opens in both languages; navigation checked with read-only API mocks |
| Parent visual inspection | Returned images for Korean desktop and English 320px; readable cards, cost scope, action and open evidence |
| Scoped whitespace review | `git diff --check` passed |

The first broad browser run occurred while another task replaced the landing and introduced syntactically incomplete translation sources; it timed out and is not treated as verification evidence. Parent reproduced those syntax failures and checked the minimal locale-delimiter / duplicate-style corrections in memory before applying them. Subsequent shared-tree type errors were resolved during the concurrent work; final diagnostics are clean.

The English-content regression previously rejected the intentionally Korean-labelled language switch. Its updated assertion still checks all main/footer copy for accidental Korean while allowing the dedicated switch label. A separate language test verifies that control.

Evidence: `.artifacts/free-templates/{check.log,component-check.log,build.log,final-regression.log,regression-rerun.log,qa.log,qa/results.json,final-source-sha256.json}`. Source and pre-fix snapshots are under `.artifacts/free-templates/baseline/`.

Reused the existing detached Vite server, PID 21195, at http://127.0.0.1:5174. Its existing log is `/private/var/folders/hn/4d_172w53_58g8kg255mlw_w0000gn/T/meshcode-detached-51535-1794191722296.log`. No new development server was started. Production activation was outside this task; the reviewed additions are in local source and the local production build.

