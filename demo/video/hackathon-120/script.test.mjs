import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const spec = JSON.parse(readFileSync(new URL('./script.json', import.meta.url), 'utf8'));
const short = JSON.parse(readFileSync(new URL('../hackathon/script.json', import.meta.url), 'utf8'));

test('120-second cut adds company, standard and community scenes in dependency order', () => {
  const scenes = Object.entries(spec.scenes);
  assert.equal(spec.total_s, 120);
  assert.deepEqual(scenes.map(([id]) => id), ['problem', 'command', 'agents', 'share', 'companies', 'standards', 'community', 'saved', 'close']);
  assert.equal(scenes[0][1].start, 0);
  for (let i = 1; i < scenes.length; i++) assert.equal(scenes[i][1].start, scenes[i - 1][1].end);
  assert.equal(scenes.at(-1)[1].end, 120);
});

test('existing first 75 seconds and source footage are preserved', () => {
  assert.deepEqual(spec.beats.slice(0, 13), short.beats.slice(0, 13));
  for (const name of ['docs', 'blog', 'slides', 'memory_app', 'share_public', 'share_copy']) assert.deepEqual(spec.footage[name], short.footage[name]);
  assert.match(spec.footage.disclosure, /recorded separately/i);
  assert.match(spec.footage.disclosure, /illustrations with example data/i);
});

test('all 22 English caption and narration beats fit their scenes and reading windows', () => {
  assert.equal(spec.beats.length, 22);
  assert.equal(new Set(spec.beats.map(b => b.id)).size, 22);
  for (let i = 0; i < spec.beats.length; i++) {
    const b = spec.beats[i], scene = spec.scenes[b.scene];
    assert.ok(scene, b.id);
    assert.ok(b.start >= scene.start + 0.3 - 1e-8 && b.end <= scene.end - 0.3 + 1e-8, b.id);
    assert.ok(b.end > b.start, b.id);
    if (i) assert.ok(b.start >= spec.beats[i - 1].end + 0.2 - 1e-8, b.id);
    assert.ok(b.en.cap.length <= 66, `${b.id}: caption too long`);
    assert.ok(b.en.cap.length / (b.end - b.start) <= 17, b.id);
    assert.ok((b.en.vo || b.en.cap).length / 14.5 / 1.25 <= b.end - b.start + 0.35, `${b.id}: voice window`);
  }
});

test('longer narrative names guidance without promising identical rendering or tenant permissions', () => {
  const words = spec.beats.map(b => `${b.en.cap} ${b.en.vo || ''}`).join(' ');
  assert.match(words, /companies|company/i);
  assert.match(words, /link/i);
  assert.match(words, /writing patterns, and design guidance/i);
  assert.match(words, /leaderboard/i);
  assert.doesNotMatch(words, /pixel-perfect|identical rendering|every platform|organization permissions|at the same time|simultaneously/i);
});

test('approval-point example follows the current policy without claiming reuse earns points', () => {
  const r = spec.feature_examples.reputation;
  assert.equal(r.source_status, 'verified');
  assert.ok(Number.isSafeInteger(r.before) && r.before >= 0);
  assert.ok(Number.isSafeInteger(r.increment) && r.increment > 0);
  assert.equal(r.after, r.before + r.increment);
  assert.equal(r.increment, 20);
  assert.ok(r.source && r.rule);
  assert.match(spec.beats.find(b => b.id === 'r02').en.vo, /Approved public templates earn twenty points/);
  const scene = readFileSync(new URL('./scenes.js', import.meta.url), 'utf8');
  assert.doesNotMatch(scene, /qualifying reuse|reuse gives the author credit/);
  assert.match(scene, /per approved public template/);
});

test('time-saving assumptions, English voice and closing URL remain consistent', () => {
  assert.deepEqual(spec.voice, short.voice);
  assert.equal(spec.footage.site_url, 'mydocumentmemory.com');
  assert.equal(Math.round(spec.ledger.whatif_minutes * spec.ledger.whatif_reuses / 60), spec.ledger.whatif_hours);
  assert.ok(spec.poster_s >= spec.scenes.community.start && spec.poster_s < spec.scenes.community.end);
  assert.equal(spec.beats.at(-1).end, 119.7);
});
