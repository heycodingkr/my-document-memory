# Landing responsive UX verification

Specification: [landing-responsive-ux-v1](../spec/landing-responsive-ux-v1.md). Issue #412.

Baseline source: current shared Landing.svelte and live production; isolated implementation base is origin/main 964a39f. Shared checkout contains extensive concurrent changes and must not be reset, staged wholesale, or deployed wholesale.

Baseline captures and computed layout: `.artifacts/landing-ux/before/`. Focused test inputs and expected results are in the specification.

## Reproduction and local results

- Before implementation, the focused suite reproduced 5 failures and 2 passes: 13–15px-high navigation targets, 12px mobile supporting prose, and a skip link that did not focus main content. Evidence: `.artifacts/landing-ux/baseline-test.log` and `before/metrics.json`. The hero-description assertion was subsequently tightened to handle Svelte's appended scope class correctly; it now requires 16px as specified.
- Built untouched origin/main 964a39f first. Its `index-BqTwiu3k.js`, `index-Deurwy2c.css`, and index matched the inspected live production release; the index SHA-256 was `998dc2218c4e630623eda821e0da35f71af5e03977ece99a279ca9e345847c65`. This establishes the release base without deploying unrelated pending frontend work.
- Final `pnpm check`: 0 errors, 0 warnings. `pnpm build`: pass.
- Final Playwright run: **25/25 pass** (17 existing landing/language/demo/example cases, 8 responsive/accessibility cases). Widths: 320, 390, 600, 601, 768, 1024, 1280, and 1440px; both English and Korean. Evidence: `.artifacts/landing-ux/final-test.log`.
- Visually inspected desktop/phone hero, desktop About cards, and Korean phone connection setup. Final phone header is 77px high, compared with 187px at 390px and 200px at 320px before the change. Final layout measurements and captures: `.artifacts/landing-ux/final/`.
- Preview uses a detached process: PID 39319, `http://127.0.0.1:4186`, log `.artifacts/landing-ux/preview.log`. Existing shared development servers were reused for the baseline and left running.

## Production

Pending final frozen-artifact deployment and public verification. Inspected base: `/srv/my-document-memory/releases/20261109T050859Z-18544`, service PID 804357, server SHA-256 `fccafafca63abe4109cd24fc90fed5a260ce0adcb5b56f3baf098e4b3e02a952`.
