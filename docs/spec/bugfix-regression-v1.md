# Outstanding bug regression pass v1

Date: 2026-11-09. Issues: #398 and #411; shared source changes are preserved.

## Required behavior

- At short desktop viewports, a signed-in person can reach every sidebar action, open Getting started, return to the workspace and sign out with pointer input. Navigation must scroll within the viewport without clipping controls, overlap or horizontal page overflow. Each viewport exposes exactly one Sign out action. Account navigation and the app sidebar switch layout at the same 700px breakpoint; memory cards stack below 900px to fit beside the desktop sidebar. Mobile navigation remains usable.
- Contribution endpoints keep their registered-member authorization gate. Member-bound bearer credentials used by CLI/MCP may contribute; anonymous or nonmember credentials must not. Fixtures must provision real account rows rather than bypass the gate.
- Existing contribution approval, withdrawal, private ownership and public-copy behavior remains intact.

## Dependency-ordered atomic goals

| Order | Route / owner | Output | Independent parent check |
|---|---|---|---|
| 1 | inline / parent | Inspect current git diff, sidebar layout, account gate, fixture and tests; record inputs before changing code | Re-read actual source and obtain fresh baseline logs |
| 2 | inline / parent, depends on 1 | Focused short-desktop Playwright regression that demonstrates actual behavior before any fix | Pointer-driven actions and DOM geometry at 1416×614, 1024×500, 720×614 and 701×500; mobile at 700×844 and 390×844; keep pre-fix result |
| 3 | inline / parent, depends on 2 | Smallest necessary responsive layout correction, if the current source still fails | Same focused test, 390×844 mobile check, Svelte check/build |
| 4 | inline / parent, depends on 1; independent of 2–3 | Fresh member-only contract verification using current Rust binaries; repair only reproducible mismatches | Rust authorization tests plus real CLI/MCP community smoke and account/admin browser suites |
| 4b | read-only historical log gathering / codex:gpt-6-luna, depends on 1 | Short cited observations from existing #409 response/trace artifacts, no tests/network/source edits | Parent opens any cited evidence before acting; parent performs fresh bounded public GET timing measurements |
| 5 | inline / parent, depends on 3–4b | Review final diff; record root cause, evidence and remaining limitations; update issue statuses | Current checks and regression results, never delegated summaries |

Production deployment and changes to Arise host source are outside this pass. Formatting-only gates and public-network latency are assessed separately from runtime behavior.
