# Landing AI-writing copy: verification

Inputs and expected results are recorded before implementation. Existing browser tests are updated for the new labels; this copy change does not require a separate test framework.

| Input / action | Expected result |
| --- | --- |
| Anonymous visitor opens `/` with `ko-KR` browser locale | English landing; one primary heading reads “The era of writing documents yourself is ending.”; the selected Korean declaration retains its meaning |
| Read hero and select “Let AI write” | Copy explains that a connected AI drafts using templates and sources; link opens `#get-started` and its instructions |
| Follow About and How it works | Story connects document preparation time, reusable know-how, AI drafting, and human review/decisions |
| Use tool tabs and keyboard navigation; select another AI | Correct example, destination link, and request remain synchronized |
| Copy example request or deny clipboard access | Existing exact-copy and manual-copy behavior remains intact |
| Play, pause, seek and replay the demo; use reduced motion | Three sample drafts and all existing playback behavior remain usable; content reflects the new message; illustrative/unpublished disclosure remains |
| Open sign-in or existing library connection | Existing email entry and connection behavior remain usable; no authentication or data changes are introduced |
| View 1440×614, 1440×1100, 768×1024, 390×844 and 320×844 | Readable heading; primary action reachable and visible on the laptop; no horizontal overflow, clipped action or overlap |
| Read page title, description and closing | Metadata uses the AI-writing message; closing reads “You do the work. AI does the writing.” |
| Build and run Svelte checks | Production output succeeds and Svelte reports no errors or warnings |
| Activate production frontend | Expected current-release guard and deployment lock pass; existing executable/config/data stay in place; HTTPS health succeeds; published index and assets match the validated build |
| Run read-only landing checks at production origin | New declaration and actions render; demo, public examples and navigation pass without writing to production data |

## Results

- Frozen production candidate: Svelte check passed with zero errors and warnings; Vite production build passed.
- Existing local browser cases: **17 passed** on the frozen production build with an isolated SQLite fixture.
- Production browser cases: **16 passed** at `https://mydocumentmemory.com`; excluded the one case that intentionally creates/edits local-library data. All executed production cases are read-only or use browser-local request mocks.
- Directly inspected laptop 1440×614, mobile 320×844, three-output demo and how-it-works screenshots. Existing layout tests also covered 768×1024 and 390×844.
- All **13** files in the validated public distribution matched the HTTPS responses byte for byte. `/healthz` returned `ready=true`; email authentication remained enabled.
- Activated `/srv/my-document-memory/releases/20261109T025641Z-ai-writing`; previous release `/srv/my-document-memory/releases/20261109T024546Z-hero`. Existing server binary and configuration hashes matched before/after; service PID **5701** stayed unchanged. The static directory follows `current`, so no restart was needed. SQLite backup is outside release directories.
- Artifacts: `.artifacts/landing-ai-writing-v1/deployment-result.json`, `public-verification.json`, `production-e2e/`, `local-rendered/`, and `local-e2e/`.

## Source reconciliation

Concurrent localization moved strings into `landing-copy.ts`. The approved copy was preserved in English and Korean in that dictionary. Initial checking exposed duplicate `workflow.summary` properties (header and document body), missing union-property narrowing for optional step links/asides, and an ambiguous Korean request locator. The checker and existing language case reproduced these failures before correction. The header and document body now use `summary` and `documentSummary`; optional fields are narrowed; the request locator is exact. Removed two selectors made unused by the concurrent markup change.

Follow-up: `pnpm --dir web check` passed with **zero errors and zero warnings**. All **4** existing language cases passed against the running local Vite server, including the selected Korean declaration, English default, persistence, and 320px overflow checks. These source integrations preserve the ongoing localization work; that feature is not part of this task's frozen production release.

The host-forwarded Arise navigation returned success but a subsequent evaluation reported `about:blank` (the existing issue #395). It was not used as production verification. Production evidence is the successful automated browser cases, inspected screenshots, HTTPS hashes and service checks above.

An unrelated whole-worktree diff check flagged an EOF blank line in `tests/smoke/cases/fmt.py:416`; issue #400 records it. That in-progress test file was left unchanged.

## Final live check after a concurrent rollout

Another session subsequently activated `20261109T031250Z-savings-0736c0c`. It was left in place. The service remained active with PID 5701 and `ready=true`. A fresh read-only production run of `onboarding.spec.ts` / “public introduction explains the workflow before authentication” passed (**1 passed, 2.7s**), confirming the final public landing still has the approved declaration, “Let AI write” action, getting-started destination and existing browser links. Output: `.artifacts/landing-ai-writing-v1/production-final-e2e/`.
