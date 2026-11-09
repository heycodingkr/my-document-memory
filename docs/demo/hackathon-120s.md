# My Document Memory — 120-second English demo

Owner request, 2026-11-09: extend the English demo to 120 seconds and explain company document formats, link sharing of templates/writing/design guidance across document tools, and community contribution/leaderboard credit when others reuse memories. Keep existing 90-second artifacts and their submission URL intact. Continue the established English Eric narration/captions and closing `mydocumentmemory.com` card.

## Story and claim boundaries

| Time | Scene | Intended message / evidence |
|---|---|---|
| 0–75 s | Existing problem, command, real-editor composite and library flow | Reuse the verified 90-second cut's source and footage; separate-run and earlier-project disclosures remain |
| 75–85 s | Company formats | Manage different companies' report/proposal/meeting-note structures in a library. Demonstrate templates and guidance; do not imply organization isolation/permissions unless verified |
| 85–95 s | Shared standard | Give an agent a memory link with reusable structure/writing/design guidance. Across-tool consistency means following the same instructions, not guaranteed identical rendering or universal native connectors |
| 95–105 s | Contribution and reuse | Share useful templates for others to reuse. Each approved template that remains public earns 20 points; public profile/leaderboard display is opt-in. Copies/views do not earn points |
| 105–116 s | Time-saving illustration | Existing 10 minutes × 1000 reuses ≈ 167 hours, still explicitly hypothetical |
| 116–120 s | Close | Product name, tagline and website |

New explanatory scenes may be code-drawn, labelled `ILLUSTRATION · EXAMPLE DATA`; actual product captures require `REAL APP · DEMO DATA` or their real provenance. Company names, example leaderboard rows and point animations must not look like measured adoption. Existing public catalog and planned-work labels will be checked against current implementation. Never expose private company references or imply they become public with a link.

## Dependency-order atomic goals

| Goal / route | Output | Independent parent check | Dependency |
|---|---|---|---|
| L0 / inline | Status/diff/render code/tests, this spec, baseline and focused missing-route result | Read actual sources and execute tests | None |
| L1 / `codex:gpt-6-luna`, background, bounded read-only gathering | Short source/test/UI file:line map for leaderboard scoring and third-party reuse eligibility/deduplication only; no edits/tests/builds/browser/production actions | Parent opens all relevant cited lines before using a claim; summary is only a map. Sharing/company source is read inline in L3 | L0 |
| L2 / inline | `--cut hackathon-120` render and voice routes, independent 120-second script/tests | Demonstrate missing route before edits, then run actual CLI and script tests; 90-second route remains valid | L0 |
| L3 / inline | Three feature scenes and evidence-grounded English narration/ledger | Parent reads scoring/share/template source and reviews each capability claim; inspect rendered stills | L1, L2 |
| L4 / inline | Layout lint, actual composited 120 s render, English narration and subtitles | Parent owns all builds/tests, frame inspection, voice-fit/loudness checks and privacy checks | L3 |
| L5 / inline | Local final MP4, poster/SRT, completion/review record; separate unlisted submission link using the established upload preference | ffprobe, original artifact hashes, actual Studio saved state, duration display and unsigned YouTube metadata read if uploaded | L4 |

This is a long session; a bounded multi-file evidence inventory goes to the first usable allowed backend. Design, every source claim acted on, files being changed, browser loops, tests, builds and review stay inline. No worker may change production/account state. Failed gathering is taken inline rather than repeatedly redispatched.

## Inputs and expected results

| ID | Input | Expected result |
|---|---|---|
| LV-01 | Existing renderer and hackathon tests | Baseline passes before edits; previous source assets decode |
| LV-02 | `node demo/video/build.mjs --cut hackathon-120 --text 78,90,100` before routing support | Focused failure reports unknown cut; after implementation the same invocation renders actual feature text |
| LV-03 | New JSON/test suite | Contiguous 0–120 s scenes; captions ≤66 characters and ≤17 chars/s; narration fits; beats inside scenes, no caption overlap; explicit separate-run / illustration / hypothetical disclosures |
| LV-04 | Current scoring code/test cases | Approval-credit narration matches the actual eligibility rules; no points-for-reuse claim; sample scores clearly illustrative |
| LV-05 | Current share/template routes and payloads | Public links point to supported resources; confidential references remain private. No unverified company workspace or pixel-identical layout claim |
| LV-06 | Both cuts' layout lint and representative stills | New cut has no overflow, overlap or caption wrapping; shared code leaves 90 s layout valid |
| LV-07 | Final 120 s video/SRT/voice | 1920×1080, 30fps H.264/AAC stereo, 120.000±0.1 s, exact subtitle text/times, no voice overflow, approximately −16 LUFS and true peak ≤−1 dBFS |
| LV-08 | Final frames and original artifact hashes | New scenes/website legible; no private account, token or email UI; original 90 s outputs unchanged |
| LV-09 | YouTube delivery variant, if required | Use ≤119.9 s to avoid AAC padding rounding to 2:01. Preserve all spoken content. Actual saved visibility is UNLISTED, with a new URL and a 2:00 display; retain the 90 s URL |

## Design, root cause and review record

The existing renderer/voice CLI select only `demo-day` and `hackathon`; the latter is fixed to 90 seconds. Introduce an explicit additional cut rather than retiming the existing export. Reuse the verified footage and pure-time scene functions; add the three scenes only for the longer cut. Current capability evidence, red/green results and final review will be appended after direct verification.

### Directly verified capability ledger

- Scoring: `crates/dmem-server/src/members.rs:6–18` counts approved contributions with a surviving public catalog template, at 20 each. `web/src/lib/Leaderboard.svelte:11` and `MemberPanel.svelte:17` explicitly exclude views/copies. `member_leaderboard.rs:431–494` asserts pending/rejected 0, two approvals 40, one approval 20, and removal of 20 on withdrawal. The requested usage-based reward is therefore not presented as current behavior. Example animation: 80 → 100 on one additional approval, with fictional names and an illustration badge.
- Sharing: `http/account.rs:319–337` exposes anonymous public-template reads. A live read of `https://api.mydocumentmemory.com/v1/public/templates/meeting.minutes.en` returned the public meeting-note template and ordered sections. It is a supported API link; the UI has no per-template deep link. The link's actual payload carries structure, not a complete design profile. The illustration labels writing/design guidance as additional AI instructions supplied by the user.
- Formats: `dmem-contracts/src/lib.rs:83` and `store.rs:145–170` support named templates, form metadata and ordered sections. Fictional companies illustrate library organization, not organization accounts or permissions. `prompt.ts` supplies the selected structure and reference IDs to the host; actual external-editor behavior depends on that host and review. No identical-rendering guarantee is made.
- Pre-edit focused route check: `node demo/video/build.mjs --cut hackathon-120 --text 78,90,100` exited 1 with an unknown-cut error. Baseline existing renderer/script tests passed 25/25; original 90-second stills and final artifacts were hashed under `.artifacts/video-120/baseline/`.

### Implementation review and verification

- Read-only gathering job 173 (`codex:gpt-6-luna`, retained thread `mdm-120s-score-map-20261109`) completed. Its summary was used to locate sources; the parent opened scoring, test and UI code directly before finalizing any narration. No worker edits or worker verification were used.
- Added an explicit `hackathon-120` route in the shared render/voice CLI and query-selected script loading. New scene builders are registered only for the longer cut. No product behavior was changed.
- The new test initially failed on unverified sample scoring; after direct policy verification, all 31 renderer/script tests pass. The original unknown-cut invocation now succeeds and shows actual company/link/community text. `cargo test -p dmem-server --test member_leaderboard only_active_approvals_score_and_private_rank_never_leaks -- --exact` passes.
- Layout lint: 120-second cut, 159 sample times, zero issues/page problems; 90-second cut, 120 sample times, zero issues/page problems. Inspected rendered company, standards, leaderboard, what-if and closing stills; no clipping or overlap found.
- Re-rendered 90-second stills at 3/50/80/88 s exactly match pre-edit SHA256 hashes. Both existing 90-second final and YouTube delivery files also retain identical hashes; evidence: `.artifacts/video-120/original-preserved.json`. Changed-file whitespace check passes. English-only rejection was verified for both new CLI routes.
- Audio listening is unavailable in this runtime; do not claim a listening audit based on input/duration/loudness measurements.

### Final media

- Master: `demo/out/video/mdm-hackathon-120s.en.final.mp4`, exactly 120.000000 s, 1920×1080 / 30fps / 3600 frames, H.264 video and AAC / 44.1 kHz / stereo audio, 10,277,860 bytes. SHA256 `eb07d1313e1b46908b0cdd3d8bc7db11b2e15e4e8acea80f51cb3a7f448a0521`. Matching final SRT and poster are beside it. Silent composite is `.en.real.mp4`.
- All 22 SRT cues exactly match script text and timestamps. All 22 actual cached/synthesized voice clips fit their windows; the final voice clip ends at 119.225714 s. Six new beats were synthesized; old beats reused their English Eric cache.
- Independent ffmpeg scan: zero black segments, −16.3 LUFS integrated, −4.5 dBFS true peak. OCR: 120 frames / 3820 lines / zero findings. The parent inspected the final actual editor composite at 50 s, new company/standards/leaderboard scenes at 83/93/103 s, and closing URL at 118.5 s. The coarse contact sheet samples a few scene-transition fades, so the individual in-scene frames establish feature legibility.
- YouTube delivery copy: `.en.youtube.mp4`, 119.900000 s / 3597 frames, 1920×1080 H.264/AAC stereo, 64,204,195 bytes, produced by MeshCode `video_trim`. Only the last 0.1 s of the static/silent closing tail was removed. The exact 120-second master is retained.
- Evidence: `.artifacts/video-120/verification.json`, `ffprobe.json`, `privacy.log`, `quality.log`, `render-result.json`, `youtube-ffprobe.json` and opened final PNGs. No full real-time playback/listening or remote YouTube quality claim is made.

### Submission URL

- **120-second version:** https://youtu.be/JAkA8PgXcOU — `My Document Memory — 2-Minute Hackathon Demo`, channel `Groove Stacks`, saved **UNLISTED / 일부 공개**, displayed **2:00**.
- The upload used the verified 119.9-second delivery copy. Before Save, UNLISTED was selected and PUBLIC was false. Studio then showed the posted-video success dialog. A fresh owned tab at `/video/JAkA8PgXcOU/edit` independently showed the persisted title/description, `공개 상태 / 일부 공개`, and `2:00`.
- Anonymous YouTube oEmbed returned HTTP 200 with the exact title and channel name. Evidence: `.artifacts/video-120/youtube-report.json` and `youtube-public-oembed.json`. This establishes link access and metadata, not a full playback/listening audit.
- The long native title/description entry returned a 60-second MCP timeout after completing both fields; fresh DOM reads confirmed their exact text and saved state before continuing. The operation was not blindly resent. The final details page confirmed both fields again.
- Existing 90-second URL remains https://youtu.be/fh8DfHHa1zY and its local files are unchanged. No source commit was made.
