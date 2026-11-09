# Landing responsive UX review

Issue #412. See the [specification](../spec/landing-responsive-ux-v1.md) and [verification](../test/landing-responsive-ux-v1.md).

The previous component mixed repeated breakpoint overrides with 7–13px presentation text. Small header controls fit by shrinking labels; mobile lost the examples link; the skip link had no focusable destination. The implementation consolidates presentation rules, uses a 14–18px prose scale with darker supporting colors, reserves 12–13px for captions, and keeps interactive targets at least 44px high.

The phone header now shows the brand, language switch, and a disclosure menu. Expanded navigation retains every destination. The toggle exposes `aria-expanded`/`aria-controls`; keyboard Tab reaches its links; Escape closes the menu and restores focus; selecting a destination closes the menu. Desktop navigation stays visible independently of the phone state. The signup action has a distinct primary treatment. Hero copy and examples preserve the established paper/sage style and existing wording.

Review covered both languages, the 600/601px menu boundary, narrow-screen overflow and overlap, actual foreground/background contrast, short laptop and phone viewports, clipboard behavior, keyboard example tabs, demo animation/reduced motion, locale persistence, and standalone SVG examples. All 25 browser cases pass and Svelte reports zero diagnostics. Desktop and mobile screenshots were opened for visual inspection.

Release isolation: unchanged current-main frontend builds byte-identically to the observed production frontend. The release contains only the reviewed landing source delta and supporting tests/docs. Shared account/backend work is excluded. Deployment must preserve the running server, old hashed assets, persistent data/configuration, and the current release guard under the existing deployment lock.

Accepted tradeoff: the mobile guide needs one menu action to expose navigation. This reduces header height from 187–200px to 77px and gives the hero action and example more room. No claim is made about conversion improvements or testing on physical phones; responsive checks use Chromium viewport emulation.
