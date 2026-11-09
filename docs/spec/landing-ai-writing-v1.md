# Landing: let AI do the writing

## Intent and cause

The user selected the declaration “문서를 사람이 쓰던 시대는 끝나갑니다.” and authorized updating the related landing copy and deploying it. The existing “Any model. Your standard.” lead describes consistency across models but does not explain why someone should stop spending time writing documents.

Keep the production landing in English. Lead with “The era of writing documents yourself is ending.” Explain the value in this order: time spent preparing documents, reusable writing know-how, the connected AI doing the drafting, and the person reviewing and deciding.

## Copy and behavior

- Hero: the selected declaration, a direct invitation to stop spending time writing, and a “Let AI write” link to the existing getting-started section.
- Product story: templates, writing guidance, review criteria, and task-specific references give the AI the context it needs. People check sources and open questions and decide what comes next.
- Examples and illustrative demo: reports, decks, worklogs, and posts follow the same message. Keep the demo visibly illustrative and unpublished.
- Closing: “You do the work. AI does the writing.”
- Browser title and description reflect the new message.
- Keep existing navigation destinations, authentication, AI/tool selection, prompt copying, privacy controls, source checks, outline approval, exports, and provider-cost disclosures working.
- Do not promise an in-app model call, universal direct publishing, measured time savings, or free third-party AI usage. The free shared-memory goal remains explicitly a goal.

## Dependency-ordered atomic goals

| Goal | Depends on | Route / owner | Output | Independent check by the implementing parent |
| --- | --- | --- | --- | --- |
| 1. Establish baseline | None | Inline: inspect worktree, source, existing tests, deployment and live release | This spec, test matrix, baseline build and release identity | Compare built baseline assets with the running public release; inspect actual files rather than summaries |
| 2. Update the message | 1 | Inline: edit Landing, WorkflowDemo and HTML metadata | Consistent copy and adjusted existing text expectations | Review the patch against the baseline; verify routes and request-generation code are unchanged |
| 3. Validate the artifact | 2 | Inline: builds, checks and browser verification | Production build, existing landing tests, desktop/mobile screenshots | Inspect rendered screenshots; check primary action, overflow, copying, review disclosures and auth entry |
| 4. Deploy and verify | 3 | Inline: existing SSH host, guarded frontend-only release | Isolated release with the existing production server/configuration/data | Lock deployment; reject a changed current release; verify public asset hashes, browser behavior and service health after activation |

No agent dispatch is needed: the files being edited, copy decisions, builds, tests, review, and deployment verification stay with the parent.

## Concurrent localization reconciliation

During verification, another session moved landing strings into `web/src/lib/landing-copy.ts` for an English/Korean switch. Keep this task's approved copy in that dictionary as well: English retains the deployed declaration; Korean uses the user's exact declaration. Update existing language-test text expectations and verify them locally. Preserve the other session's localization and unrelated application work. The production artifact for this task remains the independently validated frozen English frontend; ongoing feature work is excluded from that artifact.
