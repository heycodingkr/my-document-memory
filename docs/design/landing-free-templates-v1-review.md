# Free templates and lightweight AI: design, cause and review

## Cause

The existing service cards explain where document memory could be used, while “any model” and a small aspirational free-creation sentence leave the practical value implicit. Visitors cannot readily connect template choice, an existing lightweight model, free document editing and export/import. No DMEM document-writing benchmark currently supports a stronger model-quality or savings claim.

## Design

Add a middle benefit section using the existing forest/paper palette and three parallel cards: reusable free templates, Luna or another connected model, and familiar free document editors. Reuse the public-library callback for its action. Keep cost scope adjacent to the benefit. Preserve the five service examples and hero.

Place early benchmark evidence in a native details element so it can be inspected without dominating the product explanation. Cite a pinned WAM source, round times to whole seconds while retaining original values in the spec, and retain the experimental limitations. Attribute observations to their original project.

## Review criteria

- Inspect original sources rather than relying on memory/delegation summaries.
- Keep current export routes and browser-tool requirements explicit.
- Do not promise free third-party AI or model parity.
- Preserve all concurrent baseline changes and keep production deployment separate.
- Run checks/build/regressions inline and inspect desktop/mobile captures.
- Review the final patch against the saved target baselines.

## Concurrent integration and focused syntax repair

Another active task rewrote Landing.svelte for English/Korean support while the first regression run was in progress. Its write replaced the inline benefit block. Isolate the new benefits in FreeTemplates.svelte and add a locale-aware hook to the latest landing, preserving its new language behavior.

The new translation source closed each locale object before preview and then closed it again, making ko parse as a variable/type declaration. WorkflowDemo also had two consecutive style opening tags. The actual failing Svelte checks and browser runs reproduced these failures. TypeScript/Svelte in-memory checks of only the delimiter corrections produced 0 syntax errors and 0 warnings before applying them.

## Final review

The final middle-page section is isolated in FreeTemplates.svelte with English/Korean copy and a two-line import/render integration in the concurrently localized Landing.svelte. README has the matching benefits, correct export routes, explicit free-template scope, provider-dependent AI costs, and a pinned WAM comparison. Its concurrent onboarding and illustrative-savings additions remain intact.

Reviewed the actual component, integration, scoped test change, source measurements and official account/plan pages. WAM times are rounded only on the landing; README retains 473.976 / 423.193 seconds and 123 / 106 external tool boundaries. Both surfaces identify the original project and experimental limitations; DMEM measurements remain pending.

Full Svelte diagnostics ended at 0 errors/0 warnings and the production build passed. All 16 selected regression scenarios were validated (15 in the combined run and the corrected English-content case on targeted rerun). Focused QA confirmed both languages, all four viewport widths, keyboard disclosure, safe source links and public-library navigation. Parent inspected returned desktop/mobile screenshots and checked whitespace/source identity. No production activation was performed.
