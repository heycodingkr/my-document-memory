// V-01: script.json is the single source for scenes, captions and voice-over. Run: node --test demo/video/
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const script = JSON.parse(readFileSync(fileURLToPath(new URL('./script.json', import.meta.url)), 'utf8'));
const scenes = Object.entries(script.scenes).map(([id, s]) => ({ id, ...s })).sort((a, b) => a.start - b.start);
const beats = script.beats;
const EPS = 1e-9;

test('scene windows are contiguous, start at 0 and end at total_s', () => {
  assert.equal(scenes[0].start, 0);
  for (let i = 1; i < scenes.length; i++) assert.equal(scenes[i].start, scenes[i - 1].end, `${scenes[i].id} must start where ${scenes[i - 1].id} ends`);
  assert.equal(scenes.at(-1).end, script.total_s);
  assert.equal(script.total_s, 162);
});

test('every scene has at least one beat and every beat names an existing scene', () => {
  for (const b of beats) assert.ok(script.scenes[b.scene], `${b.id}: unknown scene ${b.scene}`);
  for (const s of scenes) assert.ok(beats.some((b) => b.scene === s.id), `scene ${s.id} has no beat`);
});

test('beat ids are unique and in time order, with a gap between captions', () => {
  assert.equal(new Set(beats.map((b) => b.id)).size, beats.length);
  assert.equal(beats.length, 26);
  for (let i = 0; i < beats.length; i++) {
    const b = beats[i];
    assert.ok(b.end > b.start, `${b.id}: end must be after start`);
    if (i) assert.ok(b.start >= beats[i - 1].end + 0.2 - EPS, `${b.id} starts less than 0.2 s after ${beats[i - 1].id}`);
  }
});

test('every beat sits inside its scene, leaving the scene edges free for transitions', () => {
  for (const b of beats) {
    const s = script.scenes[b.scene];
    assert.ok(b.start >= s.start + 0.3 - EPS, `${b.id} starts too close to the start of ${b.scene}`);
    assert.ok(b.end <= s.end - 0.3 + EPS, `${b.id} ends too close to the end of ${b.scene}`);
  }
});

test('each beat has a Korean and an English caption, readable at 17 characters per second or less', () => {
  for (const b of beats) {
    for (const lang of ['ko', 'en']) {
      const cap = b[lang]?.cap;
      assert.equal(typeof cap, 'string', `${b.id}.${lang}.cap`);
      assert.ok(cap.trim().length > 0, `${b.id}.${lang}.cap is empty`);
      assert.ok(cap.length / (b.end - b.start) <= 17, `${b.id}.${lang}: caption is too fast to read`);
      if (b[lang].vo !== undefined) assert.ok(typeof b[lang].vo === 'string' && b[lang].vo.trim().length > 0, `${b.id}.${lang}.vo`);
    }
  }
});

test('the English voice is set; the Korean voice must be chosen before voice-over runs', () => {
  assert.match(script.voice.en.voice_id, /^[A-Za-z0-9]{10,}$/);
  assert.ok('voice_id' in script.voice.ko);
  assert.ok(script.voice.ko.voice_id === null || /^[A-Za-z0-9]{10,}$/.test(script.voice.ko.voice_id));
});

test('the poster time falls inside the video', () => {
  assert.ok(script.poster_s >= 0 && script.poster_s < script.total_s);
});
