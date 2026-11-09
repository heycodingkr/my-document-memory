# Free templates and lightweight AI in the product story

Status: implemented and locally verified, 2026-11-09. Spec and acceptance inputs were recorded before implementation. Issue #399.

## Intent and cause

The user wants README and landing visitors to understand that multiple document templates can be reused with a lightweight model such as Luna and continued in Google Docs, Google Slides, or Notion using their free editing options. Current copy has service examples and an aspirational free-creation line, but does not connect these benefits or name Luna. The model-neutral claim alone does not explain the accessible workflow.

## Requirements

- Preserve concurrent working-tree changes. The concurrently added language switch now requires English and Korean benefit copy in a separate FreeTemplates.svelte component, receiving the current locale and existing public-library callback.
- Add a visible middle-page section, after How it works and before the existing service examples; add the corresponding README section before How it works.
- Explain free reusable templates, handing the template/rules/sources to an existing AI host including Luna, and the concrete DOCX → Docs, PPTX → Slides, Markdown → Notion routes.
- Link official service pages for account/plan scope. Browsing and reusing document templates is free; AI host/model/API costs and third-party plan limits remain provider-dependent.
- Reuse the existing public-library callback for a “Browse free templates” action.
- Keep direct browser editing conditional on compatible host/browser tools. The built-in app produces a deterministic outline rather than calling a model.
- Include a compact, expandable landing evidence note and a README comparison from the original WAM Canva R7 report. Attribute it to WAM and retain model, date, one run per condition, differing templates/upload paths, higher reported tokens, unmeasured billing, and pending DMEM document-writing benchmarks.
- Do not infer equal output quality, general speedups, a free Luna/API entitlement, or completed direct integrations from those observations.
- Use a responsive three-column benefit band that stacks on small screens; give its section an accessible heading and its evidence disclosure native keyboard behavior.

## Verified sources

- Existing runtime/export scope: README.md, lines 31 and 49–64; web/src/lib/Landing.svelte, lines 128–157 in the captured baseline.
- Google Docs account access and Word editing: https://workspace.google.com/products/docs/ (FAQ, checked 2026-11-09).
- Google Slides account access and PowerPoint editing: https://workspace.google.com/products/slides/ (FAQ, checked 2026-11-09).
- Notion Free personal plan and plan limits: https://www.notion.com/pricing (checked 2026-11-09).
- WAM Canva R7: https://github.com/heycodingkr/web-agentic-memory/blob/04cb13318acb0c7dff7734b6613325c361deb827/docs/test/benchmarks/canva.md (original local lines 7–36 and public pinned source checked).
- Source measurements: gpt-6-luna/max, 2026-10-31; tools-only 473.976 s / 123 external tool boundaries; supplied WAM hints 423.193 s / 106. Both passed the full task/file checks. This product's port map excludes inheriting those as DMEM measurements.

## Dependency-ordered atomic goals

| Goal | Depends on | Route | Output | Independent parent check |
| --- | --- | --- | --- | --- |
| 1. Establish baseline | None | Inline | Git status/diffs, target sources/tests, baseline Svelte check and target snapshots | Read actual targets and original benchmark; verify official free-plan sources |
| 2. Define acceptance | 1 | Inline | This spec, test inputs/expected results, design/root-cause note | Check requested benefits against current runtime and distinguish product vision from evidence |
| 3. Update both surfaces | 2 | Inline | README addition and landing benefit band/disclosure using existing callback | Compare with captured target baselines; review wording, numbers, routes and link safety |
| 4. Verify | 3 | Inline | Svelte check, production build, relevant existing Playwright regressions, focused desktop/mobile QA | Parent runs checks and inspects returned screenshots; verify disclosure keyboard use and library action |
| 5. Review and record | 4 | Inline | Final design/test results, issue comment/status | Inspect final scoped diff and ensure unrelated changes remain intact |

Concurrent localization replaced Landing.svelte during validation, so integrate the new section as a separate FreeTemplates.svelte component and preserve the new locale state. Verification reproduced two independent syntax defects in that work: extra locale-object closures before preview, and duplicate style opening tags in WorkflowDemo. Minimal delimiter corrections were first checked in memory with the TypeScript parser (0 errors) and Svelte compiler (0 warnings); correct only those delimiters to restore validation.

No worker dispatch is needed for these content targets. File inspection, judgment, edits, all builds/tests and final review remain inline. Existing Vite PID 21195 on port 5174 is reused. This task updates local source; production activation belongs to the separate release work.
