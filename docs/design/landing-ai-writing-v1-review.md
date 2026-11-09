# Landing AI-writing copy: design and review

## Decision

Use the user's change declaration as the hero. The existing production site is English, so the selected Korean phrase is rendered as “The era of writing documents yourself is ending.” Supporting copy explains the user's benefit before the mechanism: stop spending time preparing documents; give the connected AI reusable writing know-how and sources; review the result and decide what follows.

The primary action leads to the existing setup instructions. Authentication and public-memory browsing remain available through the existing controls. The footer closes with “You do the work. AI does the writing.”

## Implementation review criteria

- Preserve current uncommitted work and shared deployment state.
- Keep functionality changes limited to labels and, only if needed, heading layout.
- Reconcile the longer hero with narrow screens and short laptop viewports.
- Keep source confirmation, privacy, outline approval, illustrative-demo and provider-cost explanations accurate.
- Review the final diff and rendered output directly.
- Deploy the validated frontend without rebuilding or replacing unrelated backend changes. Keep a previous-release rollback and reject concurrent deployment drift.

## Final review

The frozen release changes the message across the hero, About, examples, how-it-works, use cases, memory explanation, getting-started heading, closing, demo content, and metadata. Existing destinations, prompt arguments, outline confirmation, authentication, exports, privacy and pricing disclosures were preserved. Direct patch review confirmed the deployed change is copy only; no CSS change was needed for its longer headline.

Svelte check and production build passed. Seventeen existing local browser cases passed, followed by sixteen read-only production cases. Laptop 1440×614, 320px mobile, the demo and workflow screenshots were opened and inspected. Thirteen public file hashes matched the validated artifact. Release `20261109T025641Z-ai-writing` inherits the active backend from `20261109T024546Z-hero`; binary/config hashes and PID 5701 remained unchanged. SQLite was backed up using its backup API. The guarded, locked symlink swap passed health and served-index checks, and retained the previous release for rollback.

Other sessions changed application/API files and moved landing copy into `landing-copy.ts` during this task. The deployed artifact was kept frozen so unfinished feature work was excluded. In the shared source, English and Korean strings were reconciled to the approved message without replacing that work. Reproduction through Svelte check and the existing language tests identified duplicate summary keys, optional-property typing and one ambiguous locator; these were corrected and the final source check reported zero errors/warnings, with four language cases passing. The localization specification and expectations now refer to the approved declaration.

The source repository remains in its existing shared, uncommitted state. No commit, index reset or unrelated source overwrite was performed. The independent host-browser lease issue remains tracked as #395; evidence for the production result comes from the automated browser suite, actual screenshots and HTTPS/service checks. The unrelated EOF formatting finding is recorded as #400.

At final readback, another session's `20261109T031250Z-savings-0736c0c` release was active. A fresh production introduction case passed against it, including the new declaration and action. It was preserved rather than replacing that newer release with this task's snapshot. The isolated local fixture was stopped; the existing development server was left running. The scoped final diff check passed.
