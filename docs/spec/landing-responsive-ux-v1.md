# Landing readability and responsive navigation v1

Issue: #412. User authorized desktop/mobile design improvements and production deployment.

## Scope and behavior

Preserve the sage/paper identity, English default and Korean toggle, document examples, truthful product limitations, and all existing destinations. Improve the landing only. Do not ship unrelated shared-checkout changes or alter account/backend/data configuration.

- Keep the brand and language switch visible. Use a compact, keyboard-accessible mobile menu with expanded state, Escape/focus restoration, and automatic close after navigation. Display guide links and account actions in deliberate rows when opened; include examples. Every visible header action/link must have a touch area at least 44 CSS pixels high, without horizontal document overflow at 320, 390, 600, 601, 768, 1024, 1280, and 1440px.
- Use at least 16px for the hero description, 14px for supporting prose and content-card descriptions, and 12px for landing captions/disclosures. Body copy must have at least 1.65 line height; normal supporting text must have a contrast ratio of at least 4.5:1 against its actual surface.
- Keep the hero action visible within a 1440×614 laptop viewport and a 390×844 phone viewport. Give account creation one primary treatment; retain sign-in, public browsing, and agent connection as distinct options.
- Preserve arrow/Home/End keyboard tabs, translated content, locale persistence, copy actions, example links, demo controls, and reduced-motion behavior. Add an explicit focus target for the skip link.

## Root cause and design

Landing.svelte accumulated successive breakpoint overrides. Its smallest breakpoint shrinks navigation and supporting prose instead of giving them space; the header action row has no wrapping contract and its text buttons have near text-only hit areas. Numerous captions use 7–11px type and muted colors too close to the pale surfaces. Consolidate the header rules and apply a consistent type scale in the component. Visual comparison of the first iteration showed that keeping every 44px menu item expanded consumed 279px on a phone; the final design collapses the navigation while keeping the language switch available.

## Dependency-ordered atomic goals

1. Baseline and contract — route: parent/local. Output: focused failing responsive tests, desktop/mobile baseline captures and metrics. Independent parent check: open captures, inspect computed styles and real source; no delegated summaries are evidence.
2. Landing implementation — route: parent/local, after goal 1. Output: scoped Landing.svelte markup/CSS changes on an isolated current-main checkout, plus a patch applied to the shared source only after checking its context. Independent parent check: inspect diff, browser captures in both languages, and meaningful responsive/keyboard behavior assertions.
3. Verification and frozen release — route: parent/local, after goal 2. Output: Svelte check, build, focused and existing landing regression results; frozen dist/source hashes. Independent parent check: rerun all verification here; review final patch and artifact contents.
4. Production web rollout — route: parent/local, after goal 3. Output: guarded, locked web-only release preserving the current server and old assets; rollback target and live hashes. Independent parent check: reread production symlink immediately before switching, check public HTML/JS/CSS bytes, health endpoints and deployed responsive tests/screenshots. Resolve issue only after these checks pass.

## Test inputs and expected results

| Input | Expected result |
| --- | --- |
| Anonymous landing; 320/390/600/601/768/1024/1280/1440px; English/Korean | No horizontal document overflow; all guide links/actions visible after opening the phone menu and ≥44px high; no header overlap |
| Phone menu; keyboard Enter/Tab/Escape; section link; desktop resize | Starts collapsed; opens and exposes links; Escape restores toggle focus; a link closes the menu and reaches its section; desktop navigation stays visible |
| 390×844 and 1440×614 | Hero primary action visible in the initial viewport |
| Hero/supporting paragraphs and cards | Required font sizes and line height; support text contrast ≥4.5:1 |
| Keyboard-only skip link and example tabs | Skip focuses main; arrows/Home/End change selected tool and matching preview/prompt |
| Language toggle and reload | Page language/content/metadata persist and retain layout |
| Existing landing/demo/example/copy tests | Existing destinations and behavior continue passing |
| Production frozen artifact | Public index, JS, CSS match hashes; web/API health ready; original server binary/PID preserved |
