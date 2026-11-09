# Demo day video

A 2:42, 1080p concept video with burned-in captions, in English (the default) and in Korean, rendered from `stage.html`. The render is silent;
`make-voice.py` can add a voice-over later. The story, the scene plan, the claims it may make and the checks are in
[`docs/demo/demo-video.md`](../../docs/demo/demo-video.md). Read the claims ledger before changing any word or number.

**This tool is not product code.** The product uses the same stack as `../web-agentic-memory` (Rust server, SvelteKit web).
Node, Playwright and ffmpeg appear only here, as an offline renderer (the same way `web-agentic-memory/demo/video` works).
Nothing listens on a port: Chrome loads the stage from a virtual origin and Playwright answers each request from disk.

```sh
node --test "demo/video/*.test.mjs"                       # V-01: script.json is consistent (scenes, beats, captions)
node demo/video/build.mjs --at 4,30,66,105                # PNG stills in /tmp/mdm-video/stills (check a layout in seconds)
node demo/video/build.mjs --lint                          # V-02: layout lint at 214 times; exit 1 on any issue
node demo/video/build.mjs                                 # full render, about 3 minutes -> demo/out/video/mdm-demo-day.en.mp4
node demo/video/build.mjs --lang ko                       # the Korean version (--lang ko works with every command here)
node demo/video/build.mjs --from 96 --to 128 --out /tmp/s6.en.mp4      # one range
python3 -I demo/video/make-voice.py --dry-run             # voice-over: characters to synthesise, no network
```

Output goes to `demo/out/video/` (git-ignored): `mdm-demo-day.<lang>.mp4`, `mdm-demo-day.<lang>.srt` and `mdm-demo-day.<lang>-poster.jpg`. English is the default, so `mdm-demo-day.en.mp4` is the main file.
Output is H.264, BT.709 limited range, 30 fps, no audio. The stage is a pure function of time (`window.__render(t)`), so a render
does not depend on machine speed.

Needs Google Chrome and `ffmpeg`. Playwright is taken from this repo's `web/` once it exists (pinned like `web-agentic-memory/web`),
and until then from the sibling `../web-agentic-memory/web/node_modules`. Korean glyphs come from the macOS system font
(Apple SD Gothic Neo), so another machine may draw Korean slightly differently. The Latin fonts (Manrope, DM Sans, DM Mono, OFL) are in `fonts/`.

## Files

| File | Role |
|---|---|
| `script.json` | **Single source** for scene windows, captions (`cap`) and voice-over text (`vo`, defaults to `cap`), per language |
| `stage.html`, `stage/*.js` | The stage: `core.js` helpers and icons, `scenes-a..d.js` the nine scenes, `main.js` render, lint and init hooks |
| `build.mjs` | Renders stills, lint, or the full video, the SRT and the poster |
| `make-voice.py` | Adds a voice-over (ElevenLabs). Spends credits and sends the narration text out: only after approval |
| `script.test.mjs`, `render-options.*` | Tests for `script.json` and for the poster/overlay options |

## What is real and what is a drawing

Scene 1 is history with approximate dates (sources in the claims ledger). Scene 2 is an illustration. **Scenes 3–8 are concept drawings of the
flow in [`docs/spec/overview.md`](../../docs/spec/overview.md), with sample data.** None of them is a recording, and the badge on every
screen says so (`CONCEPT · SAMPLE DATA`). The product is still in design, and the video must not look like a recording of something that does not
exist. Brand names (Google Docs, Google Slides, Notion) are text only, with no logos.

## Changing it

- **Words and timing:** edit `script.json`. Keep each caption to one line (about 34 Korean characters or 66 English ones); `--lint` fails when a caption wraps. If you change a caption, change its `vo` too.
- **On-screen text:** it is inline in `stage/scenes-*.js` as `tr('한국어', 'English')`. Keep both languages in step.
- **Numbers and names:** they must stay inside [the claims ledger](../../docs/demo/demo-video.md#클레임-원장) or be marked as sample data.
- **Poster:** `poster_s` in `script.json`.

## Voice-over

`python3 -I demo/video/make-voice.py --dry-run` (English; add `--lang ko` for Korean) lists the beats and the character count without any network access.
The real run sends the narration text to ElevenLabs and spends credits, so run it only after the owner approves. The key comes from
`ELEVENLABS_API_KEY` or `~/.config/mdm-demo/elevenlabs.key` (never commit it). The English voice is Eric (the same as the other demo video).
The Korean `voice_id` in `script.json` is `null` on purpose: listen to candidates and pick one first; the script refuses to run until it is set.
Beats are placed at their start time and sped up to at most 1.25× when longer than their window (it warns when a beat does not fit).

## Replacing a concept scene with real footage

When the product runs, record the real screen and composite it. `build.mjs` has a second ffmpeg pass for this, copied from the other demo video's
renderer; **it has not been exercised in this repo yet**, so test it with one short range first. A scene pushes an entry to `window.__overlays`
(`{ id, file, src: {from, to}, speed, crop, mask, x, y, w, h, from, to }`, with `file` relative to `demo/out/`) and draws a `.hole` where the clip goes.
Check every recording frame by frame before publishing: crop away tab strips, URL bars and account avatars, and never use a recording with another
window or private data in it. Keep raw recordings in `demo/out/` (git-ignored); do not commit or upload them.
