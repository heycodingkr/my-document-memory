# Landing and README: document consistency and lower-cost models

## Intent and cause

The user wants the product story to include two more problems: document formats drift when the web writing platform or AI model changes, and lower-cost models can struggle with document writing. Existing copy mentions reusable criteria across models and using a lightweight model, but does not clearly connect these problems to the value of document memory.

## Design

Update the README problem statement, consistency explanation and lightweight-model guidance. In the existing English/Korean landing dictionary, make the first two About cards describe cross-platform/model consistency and better guidance for lower-cost models. Keep the AI-writing lead and community/free-access vision.

Describe the mechanism: reusable outlines, tone, required sections, writing rules, examples, review criteria and task-specific references give the connected AI a concrete standard. Use help/support language; results still need human review. Do not claim identical rendering in every service, measured model-quality gains, or premium-model equivalence. The web runtime still creates an outline; model writing uses a connected AI host.

## Dependency-ordered atomic goals

| Goal | Depends on | Route / owner | Output | Independent parent check |
| --- | --- | --- | --- | --- |
| 1. Establish baseline | None | Inline | Inspect status/diff, README, landing dictionary/rendering and existing checks; save a scoped pre-edit snapshot | Read the actual changed sections and existing test expectations |
| 2. Record scope and acceptance | 1 | Inline | This spec with design, cause and test inputs/results | Confirm both requested problems and both landing locales are covered |
| 3. Update copy | 2 | Inline | Scoped README and English/Korean About strings | Compare against the snapshot; confirm unrelated concurrent edits remain intact |
| 4. Verify and review | 3 | Inline | Svelte check, production build, existing language cases and rendered acceptance check | Run verification here; inspect desktop/mobile output and final scoped diff |

No delegation: the scope is two copy files, and the wording, edited source and verification require direct review.

## Test inputs and expected results

| Input / action | Expected result |
| --- | --- |
| Read README The Problem | Names format drift on platform/model changes and the difficulty lower-cost models can have |
| Read README consistency and free-template guidance | Explains reusable writing standards and guidance for lower-cost models without promising equivalent results |
| Open local landing in English | About explains both problems and how reusable memory helps |
| Switch landing to Korean | Equivalent problem/benefit copy, with the existing approved hero retained |
| Run existing landing-language cases | English default, Korean translation, persistence and 320px layout pass |
| Inspect About at desktop and 320px in both languages | Full new copy is readable with no clipping/overlap or horizontal overflow |
| Run Svelte check and production build | No type/template errors and a successful production bundle |
| Compare the scoped patch with the pre-edit snapshot | Only intended copy changes; existing routes, behavior and concurrent work preserved |

This is a reversible copy change, so no new automated tests are added. Use existing checks and a one-off rendered acceptance check.

## Verification and review

- `pnpm --dir web check`: passed, zero errors and zero warnings.
- `pnpm --dir web build`: passed.
- Existing `landing-language.spec.ts`: all four cases passed against the existing local Vite server.
- One-off rendered acceptance: English and Korean at 1440px and 320px passed exact-copy and overflow checks. Opened and inspected all four About screenshots; the new cards remain readable with no clipping or overlap.
- Scoped `git diff --check`: passed.
- Direct review confirmed this task changes four README spans and the first two About cards in each landing locale. Routes, prompts, authentication and rendering code are unchanged by this task.
- Another session added MCP/contribution documentation to README after the baseline snapshot. Those additions were preserved and excluded from this task's attributed patch.
- Artifacts: `.artifacts/landing-consistency-v1/` contains the baseline, intended copy patch, observed concurrent changes, rendered acceptance JSON and four screenshots.
- This task updates local source; no publication or deployment was performed.
