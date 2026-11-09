# Seed library and HTTPS deployment v1 — results

Verified 2026-11-09. Contract: [seed-deployment-v1.md](../spec/seed-deployment-v1.md). Public web app: https://mydocumentmemory.com.

## Result

Created four native Google Docs and two native Google Slides decks through Arise, saved them in the signed-in Google account, downloaded Office originals, validated their ZIP/XML/content and uploaded all six through the deployed application UI. Each original has a private source-memory record and a private reusable form. Created a meeting-note example and kickoff-deck example, edited and saved each as v2, reloaded history and downloaded valid DOCX/PPTX exports. All content is synthetic, with no existing personal Drive documents imported.

| Form | Native Google original | Source ID | Private form ID |
|---|---|---|---|
| MDM 회의록 양식 | [Google Docs](https://docs.google.com/document/d/1Tt2H8kNG84OpGgIvoy0sVXO1Y7e2Qd4-AGfSiXnMMlk/edit) | src_ee2a417bd81a4c8785940249071e6777 | tpl_4014656e851e41f896b7ebb47b013344 |
| MDM 주간 업무보고 양식 | [Google Docs](https://docs.google.com/document/d/1_F-WQBH9vY7ri4n4skvd_vI0Cze8XYUPT8UVoNF3-1M/edit) | src_43e1c4d47a164b08bfe6f850f9fd004d | tpl_f76b78c1ebe14417a7720edab225e60c |
| MDM 프로젝트 제안서 양식 | [Google Docs](https://docs.google.com/document/d/1CwI019IU2L-Y0pBUmrxfrtg4405-vPum46Es_V_GmWc/edit) | src_a276559d44d44b738f53b293e907e615 | tpl_f921e5209a0a49e48f934cff65f15c40 |
| MDM 업무 인수인계 양식 | [Google Docs](https://docs.google.com/document/d/1nxiyRulbk-qavV0S6lwKkp-_nYOic7hnL_9isHQmrvU/edit) | src_93e0035a2614435eb604a8b38cb7bf10 | tpl_0641510e785240b88853b73c6e3df114 |
| MDM 프로젝트 킥오프 슬라이드 양식 | [Google Slides](https://docs.google.com/presentation/d/1ds3ChrcdWkA9H8CYbUM9seTBwpSLAwBl4fv9fkjiVpY/edit) | src_0b00729089724264a53217560901a4b3 | tpl_44bd25ac8f7044449ea02f11496d2349 |
| MDM 월간 운영보고 슬라이드 양식 | [Google Slides](https://docs.google.com/presentation/d/1Hc1lbsrl6a3gHIlXec7Tp98sWqTva9mHV9-gxuoptQk/edit) | src_c650264ed8664861b589b84070912487 | tpl_6d50db0aa9c042c79fdc2cdab3a2b2be |

The Google originals retain their existing private permissions. Imports preserve their original downloaded bytes and extracted text/structure. They do not synchronize back to Google or preserve every native Office styling feature. Source/form records belong to the original production bearer owner `local`; a newly created email account has its own separate private library and does not inherit those records.

Saved examples:

- `doc_27c5a0be190444f58d7828f8f55d1b14`: MDM 회의록 작성 예시, v2, history [2,1], pinned source v1; exported DOCX contains the synthetic deployment-check note.
- `doc_1b2aa56985a145398321ff9ac54429aa`: MDM 프로젝트 킥오프 작성 예시, v2, history [2,1], pinned source v1; seven ordered slides, exported PPTX validated.

## Deployment and auth

Initial release: `/srv/my-document-memory/releases/20261109T011532Z` on `jason-4090`, isolated enabled systemd service `my-document-memory.service`, user/group dmem, loopback 127.0.0.1:3848. SQLite persists at `/var/lib/my-document-memory/library.sqlite3` with mode 0600 in a mode-0700 directory. Configuration stays in root-only `/etc/my-document-memory/server.env`; the separate private local `.env.production` is Git-ignored. No credential is included in these records.

Created apex DNS and www CNAME in the existing Cloudflare zone; added only the application Caddy site and dynamic-DNS domain entry, preserving other services. Caddy serves valid public HTTPS and redirects www to apex. The app's public Origin is accepted; unrelated Origins and missing/wrong bearer credentials are rejected. Later parallel account/public-API releases are documented in [deploy/README.md](../../deploy/README.md) and their own verification records.

Current hero release and its unchanged-server rollout are documented in [hero-examples-v1.md](hero-examples-v1.md). All six seeds and two saved documents passed its before/after-restart smoke as well.

## Validation and evidence

| Scenario | Observed result |
|---|---|
| Native creation/save/download | Four DOCX originals (7,475 / 7,200 / 7,223 / 7,266 bytes) and two four-slide PPTX originals (40,964 / 40,941 bytes); valid ZIP/XML and expected headings |
| Deployed UI import and save-as-form | Six sources, six private forms; matching families and sections |
| Search/reload | Same source/form IDs found by Korean title after reload |
| Original integrity | Every deployed original equals downloaded bytes and SHA-256 |
| Document/deck editing | Both saved at v2 with immutable [2,1] revision history and source-v1 pins |
| Office exports | Actual browser DOCX/PPTX downloads; valid ZIP/XML; deck has seven ordered slides |
| Restart persistence | Seed/source/form IDs, document versions, history and original bytes unchanged |
| Public deployment | HTTPS root/health/assets work, auth and Origin boundaries hold, www reaches apex |
| Initial checks | Rust workspace 16 tests, Svelte check/build and runtime HTTP/CLI/MCP smoke passed at initial deployment |
| Final checks | Current workspace 33 tests, Svelte 0/0 and production build; 12 public/landing browser tests and complete read-only seed smoke pass |

Ignored evidence and exact checksums/download paths: `.artifacts/seed-library/manifest.json`, `.artifacts/seed-library/smoke-downloads.json`, `.artifacts/deploy/{baseline-smoke,seeded-before-ui-smoke,before-restart,after-restart}.json`, `.artifacts/hero-examples/{before-release,after-release}.json`, and deployed browser screenshots. The before/after JSON pairs were independently compared and found identical. `tests/smoke/deployed-v1.py --manifest .artifacts/seed-library/manifest.json` repeats read-only HTTPS, auth, asset, source-byte, form, pin/history and Office-package checks.

## Review

Parent kept design, source inspection, native browser work, builds/tests, deployment and final review inline. No personal source data or production database was copied into a release archive. Early Google downloads produced before save completion were discarded; canonical files were exported only after the saved badge appeared and final package text was checked. The import UI uses text/structure extraction rather than a native Google editor integration, and example content is explicitly synthetic.
