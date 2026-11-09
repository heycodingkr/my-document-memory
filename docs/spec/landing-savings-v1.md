# Landing and README: expected time and tool-call savings

Status: 2026-11-09. Content-only update; the user explicitly requested estimates without new tests or benchmarks.

## Intent, evidence and design

Visitors should see how reusing document formats and writing instructions can reduce repeated setup in Google Slides, Google Docs and similar tools. The existing WAM Canva comparison does not surface that benefit clearly.

Use approximately **46% less task time and 34% fewer tool calls** as illustrative planning estimates. The reference is WAM's 2026-10-16 English editor pilot: Medium, rich editor and iframe editor, one run per condition. WAM computes the mean of the three per-row percentage changes. These are not Google Slides or My Document Memory measurements. The user approved using reference-based estimates; no product benchmark is requested.

Show the estimates near the landing's About content in English and Korean, with the source and estimate label beside the numbers. Use the existing green palette, a two-column metric band, and a narrow-screen stack. Add the same story to README. A hypothetical 10-minute / 100-call task becomes about 5 minutes 24 seconds / 66 calls using these rounded assumptions. Do not infer billing savings or promise a guaranteed result.

## Dependency-ordered atomic goals

| Goal | Depends on | Route | Output | Independent parent check |
| --- | --- | --- | --- | --- |
| 1. Establish evidence | None | Inline | Git status/diffs, target code/tests and original WAM pilot rows | Read cited rows and distinguish editor pilot from Slides and Canva |
| 2. Define copy | 1 | Inline | This spec and acceptance inputs/results below | Match the user's estimate-only instruction and both languages |
| 3. Update copy and presentation | 2 | Inline | README, landing copy and compact responsive metric band | Review the actual scoped patch against pre-edit snapshots |
| 4. Review | 3 | Inline | Source/diff review; no tests or benchmarks run | Check labels, source attribution, arithmetic, bilingual parity and unrelated changes |

No delegation is needed: these are coupled content/design choices in the files being changed.

## Acceptance inputs and expected results

| Input | Expected result |
| --- | --- |
| Read landing About in English or Korean | Approximately 46% less task time and 34% fewer tool calls, each explicitly estimated |
| Read the explanation | Reuse of slide structure, report format, writing rules and references explains the expected benefit |
| Read README | Same estimates, original WAM editor-pilot reference, and a clearly hypothetical 10-minute / 100-call example |
| Follow the evidence | WAM's three editor rows, one run per condition; no claim of a Slides or DMEM measurement |
| Review narrow-screen styles | Metric columns stack and text can wrap |

Verification is limited to source/diff review, as requested. No new automated tests or benchmark runs.

## Review result

- Added the same 46% / 34% estimates and hypothetical example to README and both landing languages; source links pin WAM commit `f0fdcb434916cb5ed6819546ac12ce00a3fe5e0d`.
- Reviewed changes against pre-edit snapshots and ran `git diff --check`; no whitespace errors. Tests, builds and browser QA were not run.
- Removed an existing duplicate opening `<style>` tag while adding the section styles. Concurrent free-template component and translation edits were preserved.

## Publication follow-up

The user subsequently requested both production deployment and a Git push. Use a detached checkout of latest `origin/main` (initially `486ef1e`) so the shared working tree/index and already-published hosted onboarding remain intact. Publish the savings README section and the landing dependency files: `Landing.svelte`, `landing-copy.ts`, `FreeTemplates.svelte`, `DocumentPreview.svelte`, `WorkflowDemo.svelte`, `AgentSetup.svelte`, and `web/index.html`.

| Goal | Depends on | Route | Output | Independent parent check |
| --- | --- | --- | --- | --- |
| 1. Freeze publication source | Prior source review | Inline | Isolated checkout, scoped README insertion, landing dependency snapshot and this spec | Review exact staged filenames/diff; exclude pending account/backend changes |
| 2. Produce deployable assets | 1 | Inline | Production Vite build and archive with hashes | Build succeeds; frozen assets contain English/Korean estimate labels and source reference |
| 3. Publish Git source | 2 | Inline | Commit pushed to `origin/main` without force | Fetch/compare remote SHA and published README/landing paths |
| 4. Deploy frozen web assets | 2, 3 | Inline | New web-only release cloned from the current production release | Hold deployment lock, guard expected current target, preserve server binary/config/data, record rollback, switch current atomically |
| 5. Confirm public result | 4 | Inline | HTTPS landing/JS/CSS hashes and API health | Public bytes match the built release, estimate strings present in both languages, service active |

No benchmark or test suite is requested. The production build and read-only publication/health checks are necessary for this deployment. Rollout must retain any intervening production release by re-reading current under the deployment lock.
