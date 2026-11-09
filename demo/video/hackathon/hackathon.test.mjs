// HV-01: hackathon/script.json is the single source for scenes, captions, voice-over and footage placement.
// Run: node --test "demo/video/hackathon/*.test.mjs"   (Node 26 needs the glob; a directory path fails)
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, '../../..');
const script = JSON.parse(readFileSync(path.join(here, 'script.json'), 'utf8'));
const scenes = Object.entries(script.scenes).map(([id, s]) => ({ id, ...s })).sort((a, b) => a.start - b.start);
const beats = script.beats;
const EPS = 1e-9;
const VOICE_CPS = 14.5;     // measured speaking rate of the chosen ElevenLabs voice (characters per second)
const MAX_TEMPO = 1.25;     // make-voice.py speeds a beat up by at most this factor

test('scene windows are contiguous, start at 0 and end at total_s = 90', () => {
  assert.equal(scenes[0].start, 0);
  for (let i = 1; i < scenes.length; i++) assert.equal(scenes[i].start, scenes[i - 1].end, `${scenes[i].id} must start where ${scenes[i - 1].id} ends`);
  assert.equal(scenes.at(-1).end, script.total_s);
  assert.equal(script.total_s, 90);
  assert.deepEqual(scenes.map((s) => s.id), ['problem', 'command', 'agents', 'share', 'saved', 'close']);
});

test('every scene has a beat, every beat names a scene, ids are unique and in order with 0.2 s between captions', () => {
  for (const b of beats) assert.ok(script.scenes[b.scene], `${b.id}: unknown scene ${b.scene}`);
  for (const s of scenes) assert.ok(beats.some((b) => b.scene === s.id), `scene ${s.id} has no beat`);
  assert.equal(new Set(beats.map((b) => b.id)).size, beats.length);
  assert.equal(beats.length, 16);
  for (let i = 0; i < beats.length; i++) {
    assert.ok(beats[i].end > beats[i].start, `${beats[i].id}: end must be after start`);
    if (i) assert.ok(beats[i].start >= beats[i - 1].end + 0.2 - EPS, `${beats[i].id} starts less than 0.2 s after ${beats[i - 1].id}`);
  }
});

test('every beat sits inside its scene, 0.3 s clear of the edges', () => {
  for (const b of beats) {
    const s = script.scenes[b.scene];
    assert.ok(b.start >= s.start + 0.3 - EPS, `${b.id} starts too close to the start of ${b.scene}`);
    assert.ok(b.end <= s.end - 0.3 + EPS, `${b.id} ends too close to the end of ${b.scene}`);
  }
});

test('captions are one line (66 characters or fewer) and readable at 17 characters per second or less', () => {
  for (const b of beats) {
    const cap = b.en?.cap;
    assert.equal(typeof cap, 'string', `${b.id}.en.cap`);
    assert.ok(cap.trim().length > 0, `${b.id}: empty caption`);
    assert.ok(cap.length <= 66, `${b.id}: caption has ${cap.length} characters, one line holds 66`);
    assert.ok(cap.length / (b.end - b.start) <= 17, `${b.id}: caption is too fast to read`);
    if (b.en.vo !== undefined) assert.ok(typeof b.en.vo === 'string' && b.en.vo.trim().length > 0, `${b.id}.en.vo`);
  }
});

test('the voice-over of every beat fits its window (14.5 characters per second, at most 1.25x faster)', () => {
  for (const b of beats) {
    const text = b.en.vo ?? b.en.cap, window = b.end - b.start;
    const natural = text.length / VOICE_CPS;
    assert.ok(natural / MAX_TEMPO <= window + 0.35, `${b.id}: ${text.length} characters need ${natural.toFixed(1)} s, the window is ${window.toFixed(1)} s`);
  }
});

test('the English voice is set and the cut is English only', () => {
  assert.match(script.voice.en.voice_id, /^[A-Za-z0-9]{10,}$/);
  assert.equal(script.voice.ko, undefined);
});

test('numbers in captions and voice-over are only the ones the claims ledger allows', () => {
  const allowedDigits = new Set(['167']);
  const allowedWords = new Set(['one', 'two', 'three', 'ten', 'thousand', 'seven']);
  for (const b of beats) for (const text of [b.en.cap, b.en.vo ?? '']) {
    for (const d of text.match(/\d[\d,.]*/g) ?? []) assert.ok(allowedDigits.has(d.replace(/[.,]$/, '')), `${b.id}: number ${d} is not in the ledger`);
    for (const w of text.toLowerCase().match(/\b(one|two|three|four|five|six|seven|eight|nine|ten|twenty|hundred|thousand|million)\b/g) ?? []) assert.ok(allowedWords.has(w), `${b.id}: number word "${w}" is not in the ledger`);
  }
});

test('the what-if arithmetic in the ledger is right: 10 min x 1,000 reuses = 10,000 min = about 167 h', () => {
  const l = script.ledger;
  assert.equal(l.whatif_minutes * l.whatif_reuses, 10000);
  assert.equal(Math.round((l.whatif_minutes * l.whatif_reuses) / 60), l.whatif_hours);
  assert.equal(l.whatif_hours, 167);
  assert.equal(l.mcp_tools, 7);
});

test('the poster time falls inside the video, on the four-window scene', () => {
  assert.ok(script.poster_s >= script.scenes.agents.start && script.poster_s < script.scenes.agents.end);
});

test('footage starts inside its scene, and finishes before the next clip or the scene ends', () => {
  const f = script.footage, S = script.scenes;
  assert.ok(f.slides.from >= S.agents.start && f.slides.from < S.agents.start + 3);
  assert.ok(f.memory_app.from >= S.agents.start + 8 && f.memory_app.from < S.agents.end);
  assert.ok(f.share_public.from >= S.share.start && f.share_public.from < S.share.start + 2);
  assert.ok(f.share_copy.from > f.share_public.from && f.share_copy.from < S.share.end - 3);
  assert.equal(f.slides.speed, 45);
  assert.equal((f.slides.src_to - f.slides.src_from) / f.slides.speed, 1423 / 45);
});

test('Docs and Blog declare recording placement and disclose the separate runs', () => {
  const f = script.footage, scene = script.scenes.agents;
  for (const name of ['docs', 'blog']) {
    const clip = f[name];
    assert.ok(clip, `${name} recording must replace the illustration`);
    assert.ok(clip.from >= scene.start && clip.from < scene.end);
    assert.ok(Number.isFinite(clip.speed) && clip.speed > 0);
    assert.ok(Number.isFinite(clip.src_from) && clip.src_from >= 0);
    assert.equal(typeof clip.file, 'string');
  }
  assert.match(f.disclosure, /recorded separately/i);
  const narration = script.beats.map((b) => `${b.en.cap} ${b.en.vo ?? ''}`).join(' ');
  assert.doesNotMatch(narration, /at the same time|simultaneously/i);
});

test('when the private Docs and Blog clips exist, they decode and fit their scene', {
  skip: !['docs', 'blog'].every((name) => existsSync(path.join(repo, 'demo/out', script.footage[name]?.file || '__not-generated__')))
    && 'private browser footage not generated'
}, () => {
  const f = script.footage, scene = script.scenes.agents;
  for (const name of ['docs', 'blog']) {
    const clip = f[name];
    const file = path.join(repo, 'demo/out', clip.file);
    assert.ok(existsSync(file), `${name} recording missing: ${file}`);
    const probe = spawnSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=codec_name,width,height:format=duration', '-of', 'json', file], { encoding: 'utf8' });
    assert.equal(probe.status, 0, `${name} recording cannot be decoded`);
    const media = JSON.parse(probe.stdout);
    assert.equal(media.streams[0].codec_name, 'h264');
    assert.ok(media.streams[0].width >= 888 && media.streams[0].height >= 366);
    assert.ok(Number(media.format.duration) > clip.src_from + 1);
    assert.ok(clip.from + (Number(media.format.duration) - clip.src_from) / clip.speed <= scene.end, `${name} recording exceeds the scene`);
  }
});

test('when the footage files exist, their durations match the placement', { skip: !existsSync(path.join(repo, 'demo/out/footage/slides-muse-x45.mp4')) && 'footage not generated (run demo/video/capture/*)' }, () => {
  const dur = (rel) => Number(spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path.join(repo, 'demo/out', rel)], { encoding: 'utf8' }).stdout);
  const f = script.footage, S = script.scenes;
  const slides = dur(f.slides.file);
  assert.ok(Math.abs(slides - (f.slides.src_to - f.slides.src_from) / f.slides.speed) < 0.15, `slides clip is ${slides} s`);
  assert.ok(f.slides.from + slides <= S.agents.end + 0.01, 'the Slides clip runs past the scene');
  const end = (c) => c.from + (dur(c.file) - c.src_from) / c.speed;
  assert.ok(end(f.memory_app) <= S.agents.end, 'memory app clip runs past the scene');
  assert.ok(end(f.share_public) <= f.share_copy.from + 0.25, 'public-memories clip runs into the next clip');
  assert.ok(end(f.share_copy) <= S.share.end + 0.01, 'library-preview clip runs past the scene');
});
