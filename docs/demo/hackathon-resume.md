# English demo completion — 2026-11-09

The owner authorized continuing Claude's unfinished demo, writing English Google Docs and Naver Blog drafts through the signed-in Arise browser, keeping posts unpublished, adding `mydocumentmemory.com`, and checking submission specifications. Existing unrelated working-tree changes and previous exports stay intact. No commit or public upload is requested.

## Contract

- Deliver a finished English 90-second MP4 with English narration/captions and the closing URL. Replace the illustrated Docs and Blog panes with actual captured browser execution when verified saved drafts are available.
- Capture through Arise's public browser screenshot MCP, with one retained stdio connection. Do not use shell desktop capture. Record timestamps and assemble the genuine viewport frames; no fabricated editor content.
- Newly created drafts contain only the synthetic project notes in `demo/video/hackathon/fixtures/`. Read the actual destination, focus, contents and saved state before claiming success. Never publish the blog.
- The four-pane composition combines separate runs. Disclose that they were recorded separately; the Slides clip remains an earlier WAM project run. Change the simultaneous-run narration/caption accordingly.
- The owner explicitly confirmed **1 minute 30 seconds** in this session. This overrides the three-minute wording in the previously saved participant guide; do not apply that older guide's duration to this demo. Keep 1080p and report actual file size; no resolution/size cap has been supplied or independently confirmed.

## Dependency-order atomic goals

| Goal / route | Output | Independent check | Dependency |
|---|---|---|---|
| R0 / inline | Current git status/diff, render code/tests, existing assets and this contract | Run baseline tests and inspect actual files; 23 tests passed | None |
| R1 / inline | Persistent public Arise MCP capture probe, new owned tab, genuine nonblank viewport | Inspect captured image and actual tab URL; no desktop screenshots from shell | R0 |
| R2 / inline | English Docs draft and timestamped viewport footage | Inspect native editor/save badge, reloaded/exported text and footage frames | R1 |
| R3 / inline | English Naver draft and timestamped viewport footage | Inspect live editor and saved/reopened title/body; remain unpublished | R1; sequential with R2 to avoid browser input contention |
| R4 / inline | Real-pane overlays, accurate disclosure/captions, closing URL | Focused contract test first, then direct overlay/frame review and layout lint | R2, R3 |
| R5 / inline | Full English render, voice mux, SRT, poster, QC report | Own ffprobe, loudness/black-frame/privacy checks and image inspection | R4 |
| R6 / inline | Official specification findings and completion/root-cause record | Read the official page; distinguish current verified rules from saved extract | R0; independent of R1–R5 |

Browser control, builds, tests, source changes and all judgment stay inline. No gathering delegation is needed for these known files.

## Inputs and expected results

| Check | Input | Expected result |
|---|---|---|
| RC-01 | New Arise window, two successive calls through retained MCP | Same owned tab and intended URL; screenshot contains page content |
| RC-02 | Short synthetic text typed into focused new Docs draft | Exact text is visible, saved to Drive, and survives reload/read-back |
| RC-03 | English title/body entered into Naver writer, save-draft only | Exact title/body persist; no publish action occurs |
| RC-04 | Real-pane footage config | Both files exist, finite speed/source/time placement fits scene, explicit separate-run disclosure; no simultaneous-run claim |
| RC-05 | Existing renderer test suites and layout lint | Tests pass; no off-screen text, caption wrap or page/request error |
| RC-06 | Final MP4/SRT | 90.0 ± 0.1 s; 1920×1080 30fps H.264/AAC; 16 matching subtitle cues; audible English track; URL visible near 88 s |
| RC-07 | Representative captured and final frames | Genuine Docs/Blog content, no black frames or private account/address/token UI in composited crops |
| RC-08 | Official guide/submission page | Record stated duration and any stated resolution/size; do not invent unspecified requirements |

## Root cause and review

Initial observation: host-forwarded `browser_new_window` followed by screenshot/snapshot returned a blank tab, matching the documented connection-local lease issue #395. Previous raw recordings include black/covered-window frames and an incomplete Docs save. A retained public MCP connection and renderer viewport captures address different failure modes; verify both independently. Existing `winshots.swift` is not used because the owner requires MeshCode/Arise screenshot tools for live captures.

## Verified results

Final output: `demo/out/video/mdm-hackathon-90s.en.final.mp4`, with matching `.srt` and `-poster.jpg`. The original v1 exports remain intact. Silent v2 composite: `.en.real.mp4`.

| Check | Result |
|---|---|
| RC-01 | A retained public MCP child preserved its private tab handles across navigation, native input, captures and subsequent windows. Controller was detached with `start_new_session=True` so a tool-runtime refresh could not terminate it. Only public stdio browser tools were used; no CDP/private socket/desktop shell capture |
| RC-02 | New Docs draft `My Document Memory - Project Overview`: explicit Drive-saved badge, reload screenshot, and server DOCX export. Parsed text is 836 characters and contains the exact title, five sections, concluding confirmation flag and URL. A duplicate title caused by native selection timing was corrected with exact field entry + blur and verified saved before export |
| RC-03 | A separate blank Naver draft was used. The earlier QA draft remains in the saved list; count grew from 1 to 2. A new Arise window opened the saved list and loaded `Stop starting every document from zero`; title, all paragraphs, URL and hashtags persisted. The editor remains an unpublished draft |
| RC-04 | Docs: 323 captured viewport frames over 193.8923 s, edited to 24 changing frames / 32 s. Blog: 242 frames over 187.948 s, edited to 32 changing frames / 32 s. Clips are 1776×732 H.264 / 30fps / 960 frames. Source timestamps and edit durations are retained in `frames.json` / `edit.json`. These durations describe edits, not agent performance |
| RC-05 | Focused test first failed because Docs recording configuration was absent. After replacement and provenance correction, 25/25 renderer/script tests passed; layout lint sampled 120 times with 0 issues / 0 page problems. Media-dependent tests skip on a clean checkout without private footage |
| RC-06 | ffprobe: 90.000 s, 1920×1080, 30fps, 2700 video frames, H.264 High / BT.709, AAC LC / 44100 Hz / stereo, 7,848,210 bytes. All 16 SRT cues match the script exactly; all 16 actual voice beats fit. New h07 voice is 2.786 s inside its 4.5 s window. Final 88.5 s frame visibly contains the URL |
| RC-07 | Domain QC reported 0 black segments and −16.3 LUFS. Independent ebur128 measured −16.3 LUFS / −4.5 dBFS true peak. OCR: final 90 frames / 3016 lines / 0 findings; prepared Docs/Blog 64 frames / 660 lines / 0 findings. Opened real footage, final representative frames, contact sheet and closing card for visual review |
| RC-08 | Owner confirmed 90 seconds. The archived three-minute guide does not set the duration for this task. No independent size/resolution cap was supplied; actual format/size are reported |

### Review decisions and limits

- Replaced the two drawn panes with genuine cropped viewport images; removed their simulated typing/log code. Kept the earlier Slides material explicitly labelled `EARLIER PROJECT`; the grid and voice say the runs were recorded separately.
- Preserved the common renderer, voice-mixer implementation, original voice cache and unrelated dirty product files. Added only an offline capture-preparation script and changed this cut's stage/config/tests/docs. No product restart, deployment, commit, post publication or upload occurred.
- Native coordinate input confirmed dispatch without changing Save; a fresh snapshot and actual Save button selector produced the new stored draft. The independent new-window read, not input dispatch, established persistence.
- `video_qc` assumes vertical Shorts at 1080×1920 / 6–60 s and therefore reports an irrelevant format failure for this landscape 90 s cut. Its silence/freeze notices reflect caption gaps, graphic scenes and edited viewport captures. Acceptance uses the 90 s / 1080p contract and the measured values above.
- `listen_audio` returned a text attachment notice through the host bridge; the runtime explicitly cannot accept audio input. Narration was verified through exact synthesis/cache inputs, beat lengths, encoded stream and measured loudness; no claim of listening/full real-time playback is made.
- Final evidence, manifests and privacy logs are in `.artifacts/video-resume/`; raw browser frames stay ignored in `demo/out/footage/arise/`. A saved blog article and source DOCX were read directly before delivery.
