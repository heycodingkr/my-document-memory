# Hero document examples v1 — verification

Verified 2026-11-09. Contract: [hero-examples-v1.md](../spec/hero-examples-v1.md).

## Result and review

The public landing now has a large selected report/deck/worklog SVG in the hero and a separate three-example gallery before the workflow demo. Existing About content, model/tool selection, keyboard tabs, prompts, account controls, agent setup and multi-output demo remain available. Each illustration contains fictional filled content and explicitly identifies itself as illustrative. Its full public SVG view opens in a new tab without authentication. Private Google originals are not exposed by these links.

Implementation: `web/public/examples/document-examples.svg` (11,812 bytes; three symbols and three view fragments), `web/src/lib/DocumentPreview.svelte`, targeted `web/src/lib/Landing.svelte` changes and `web/tests/hero-examples.spec.ts`. The SVG has no script, external image or font dependencies. Links use descriptive accessible names and noopener/noreferrer; focus remains visible. Parent reviewed the component, selection/link mapping, markup, actual desktop/mobile renders and XML. Read-only delegate #151 located migration/auth evidence; its summary was not used as verification.

Public examples:

- [Weekly product report](https://mydocumentmemory.com/examples/document-examples.svg#report)
- [Project kickoff deck](https://mydocumentmemory.com/examples/document-examples.svg#deck)
- [Team worklog](https://mydocumentmemory.com/examples/document-examples.svg#worklog)

## Checks

| Check | Result |
|---|---|
| `cargo test --workspace` | 33 tests passed across core, MCP and server suites |
| `pnpm --dir web check` | 0 errors, 0 warnings |
| `pnpm --dir web build` | Passed; frozen production JS/CSS below |
| Local hero examples tests | 3 passed; real SVG/popups, keyboard selection, no extra API writes, responsive layout |
| Existing landing links/demo tests | 9 passed; links, agent connection examples, copying, animated and reduced-motion demo |
| Public domain hero examples tests | 3 passed on https://mydocumentmemory.com, including anonymous static routes |
| Viewports | 1440×1000, 1440×614, 768×1024, 390×844, 320×844; no horizontal overflow |
| Parent visual inspection | Hero, full report/deck, desktop/mobile gallery; live hero/gallery and standalone worklog through Arise |
| HTTPS and public assets | Valid certificates; www reaches apex; public JS/CSS/SVG match local frozen bytes |
| Seeded production dataset | Six originals and private forms, two v2 documents, source pins, history and Office exports all passed before and after restart; snapshots identical |

Read-only production smoke was run with `tests/smoke/deployed-v1.py --manifest .artifacts/seed-library/manifest.json`. The manifest and its private connection secret remain excluded from Git. There are 18 public catalog templates plus six private imported forms; the general list is capped at 20, so each seed is additionally checked directly by ID and exact search.

## Release

Live base at inspection: `/srv/my-document-memory/releases/20261109T022729Z-13901`, already account-enabled. Parent compared all 32 Cargo/crate source and migration files by SHA-256; they matched the tested workspace. Parent opened Store::open, both SQL schema files, main's bearer-owner mapping, auth middleware and persistence assertions. The existing bearer still maps to owner `local`.

Activated `/srv/my-document-memory/releases/20261109T024546Z-hero`. Only web/dist changed; the exact existing server binary, source snapshot, environment and SQLite path were preserved. No migration or schema change was performed. The rollout held the existing deployment lock, checked the expected current target, recorded rollback, switched the symlink atomically and restarted only `my-document-memory.service`. It is enabled, active/running as dmem on 127.0.0.1:3848. Observed PID after restart: 5701.

- Rollback target: `/srv/my-document-memory/releases/20261109T022729Z-13901`, also recorded in `/etc/my-document-memory/previous-release`.
- Web archive SHA-256: `8554278847c42f9b00a3b829688c928744ba96cf86e5a3c5e45b6aa57f92639e`.
- Server binary SHA-256: `ff93a5c6fb7e5e36e06d6d9b9195fc4fa43c0344c5256f48db66373f171dc824`.
- SVG SHA-256: `75a46633129ab5a54d3d7ddad4e4ce82c14fdc48de7c56059238fe18f024c661`.
- Assets: `/assets/index-Z6u7XNu3.js`, `/assets/index-BYTz7HPo.css`.

The first rollout attempt stopped before activation because root could not create/open the existing jason-owned lock in /tmp (fs.protected_regular=2). Retrying with flock as its existing owner and sudo only inside the lock succeeded. The initial smoke's 45-second wrapper expired before its many sequential reads finished; rerun detached completed successfully. Browser test output directories can be cleared by concurrent Playwright runs; durable Arise evidence is kept under `.artifacts/hero-examples`.

## Evidence and limits

Local ignored evidence: `.artifacts/hero-examples/{cargo-test,check,build,landing-regression,public-hero,deploy,before-release,after-release}.log`, before/after JSON, backend-comparison.json, public-assets.json, frozen web-dist.tar.gz, deploy-web.sh and Arise screenshots. Arise uses an existing signed-in browser account; Getting started opened the guide without signing out or changing that account. Anonymous access was independently tested in fresh Playwright contexts and direct HTTPS requests.

A separate existing signed-in sidebar issue at 1416×614 was reproduced and registered as workspace issue #398: footer actions fall below the viewport. Keyboard focus and Enter opened Getting started for QA. That account-layout issue is outside this visual-example change. Synthetic illustrations are not live Google/Notion provider synchronization. Tests cover Chromium and Arise; no cross-browser claim is made.
