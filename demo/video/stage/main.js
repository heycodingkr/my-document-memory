'use strict';
// Render, layout lint and init hooks used by build.mjs.
const logoEl = () => document.getElementById('logo');
const badgeEl = () => document.getElementById('badge');
const capEl = () => document.getElementById('cap');
const BADGES = {
  history: { cls: 'history', text: () => tr('역사 · 연도는 대략', 'HISTORY · DATES APPROXIMATE') },
  illus: { cls: 'illus', text: () => tr('일러스트', 'ILLUSTRATION') },
  concept: { cls: '', text: () => tr('컨셉 · 예시 데이터', 'CONCEPT · SAMPLE DATA') }
};

window.__render = (t) => {
  let active = null;
  scenes.forEach((sc) => {
    const inA = sc.start === 0 ? 1 : fade(t, sc.start, sc.start + 0.45);
    const outA = sc.end >= SCRIPT.total_s ? 1 - fade(t, sc.end - 0.8, sc.end) : 1 - fade(t, sc.end - 0.45, sc.end);
    const a = Math.min(inA, outA);
    if (t >= sc.start && t < sc.end + 0.001 && a > 0.001) {
      sc.e.style.display = 'block'; sc.e.style.opacity = a;
      sc.e.update(t - sc.start, t);
      if (a >= (active ? active.a : 0)) active = { sc, a };
    } else sc.e.style.display = 'none';
  });
  const showChrome = active && active.sc.chrome !== false;
  const lg = logoEl();
  lg.style.opacity = showChrome ? active.a : 0;
  lg.className = active && active.sc.dark ? 'dark' : '';
  const b = badgeEl(); const kind = active && BADGES[active.sc.badge];
  b.style.opacity = kind ? active.a : 0;
  if (kind) { b.className = kind.cls; b.textContent = kind.text(); }
  const c = CAPTIONS.find((x) => t >= x[0] && t <= x[1]);
  const cap = capEl();
  if (c) { cap.textContent = c[2]; cap.className = c[3] ? 'ondark' : ''; cap.style.opacity = Math.min(fade(t, c[0], c[0] + 0.18), 1 - fade(t, c[1] - 0.18, c[1])); }
  else cap.style.opacity = 0;
};

// Layout lint (V-02). Returns a list of problems for the frame that was just rendered.
window.__lint = () => {
  const out = [];
  const eff = (e) => { let o = 1; for (let p = e; p && p !== document.documentElement; p = p.parentElement) { const cs = getComputedStyle(p); if (cs.display === 'none' || cs.visibility === 'hidden') return 0; o *= parseFloat(cs.opacity); } return o; };
  const cap = capEl();
  const capVisible = eff(cap) >= 0.5;
  const capR = cap.getBoundingClientRect();
  if (capVisible && capR.height > 100) out.push({ type: 'caption-wraps', text: cap.textContent, detail: `height ${Math.round(capR.height)}px` });
  const leaves = [...document.querySelectorAll('#stage *')].filter((e) => !e.closest('svg') && e.id !== 'cap' && !cap.contains(e) && [...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()));
  const rects = [];
  for (const e of leaves) {
    const o = eff(e); if (o < 0.05) continue;
    const range = document.createRange(); range.selectNodeContents(e);
    const r = range.getBoundingClientRect(); if (r.width < 1 || r.height < 1) continue;
    const text = e.textContent.trim().replace(/\s+/g, ' ').slice(0, 48);
    if (r.left < 30 || r.right > 1890 || r.top < 16 || r.bottom > 1064) out.push({ type: 'outside', text, detail: `[${Math.round(r.left)},${Math.round(r.top)} → ${Math.round(r.right)},${Math.round(r.bottom)}]` });
    const box = e.closest('.card, .field, .btn, .chip, [data-box]');
    if (box && box !== e) { const b = box.getBoundingClientRect(); if (r.left < b.left - 2 || r.right > b.right + 2 || r.top < b.top - 2 || r.bottom > b.bottom + 2) out.push({ type: 'spills-box', text, detail: `text [${Math.round(r.left)},${Math.round(r.top)} → ${Math.round(r.right)},${Math.round(r.bottom)}] box [${Math.round(b.left)},${Math.round(b.top)} → ${Math.round(b.right)},${Math.round(b.bottom)}]` }); }
    if (capVisible && eff(e) >= 0.3 && r.bottom > capR.top - 6 && r.top < capR.bottom && r.right > capR.left && r.left < capR.right) out.push({ type: 'under-caption', text, detail: `bottom ${Math.round(r.bottom)} vs caption top ${Math.round(capR.top)}` });
    if (o >= 0.6 && !e.closest('[data-overlap]')) rects.push({ e, r, text });
  }
  for (let i = 0; i < rects.length; i++) for (let j = i + 1; j < rects.length; j++) {
    const a = rects[i], b = rects[j];
    if (a.e.contains(b.e) || b.e.contains(a.e)) continue;
    const w = Math.min(a.r.right, b.r.right) - Math.max(a.r.left, b.r.left), h = Math.min(a.r.bottom, b.r.bottom) - Math.max(a.r.top, b.r.top);
    if (w > 3 && h > 3) out.push({ type: 'text-overlap', text: `${a.text} ⟷ ${b.text}`, detail: `${Math.round(w)}×${Math.round(h)}px` });
  }
  return out;
};

// Visible on-screen text of the frame that was just rendered (build.mjs --text). Used to check numbers against the claims ledger (HV-08).
window.__visibleText = () => {
  const eff = (e) => { let o = 1; for (let p = e; p && p !== document.documentElement; p = p.parentElement) { const cs = getComputedStyle(p); if (cs.display === 'none' || cs.visibility === 'hidden') return 0; o *= parseFloat(cs.opacity); } return o; };
  const out = [];
  for (const e of document.querySelectorAll('#stage *')) {
    if (e.closest('svg')) continue;
    const own = [...e.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).filter(Boolean).join(' ');
    if (own && eff(e) >= 0.3) out.push(own);
  }
  return out;
};

// A cut (see build.mjs CUTS) can set window.__SCRIPT_URL, window.__BADGES and window.__buildScenes before __init runs.
window.__init = async () => {
  Object.assign(BADGES, window.__BADGES || {});
  SCRIPT = await fetch(window.__SCRIPT_URL || '/demo/video/script.json').then((r) => r.json());
  window.__total = SCRIPT.total_s;
  window.__poster = SCRIPT.poster_s;
  CAPTIONS = SCRIPT.beats.map((b) => [b.start, b.end, b[LANG].cap, !!SCRIPT.scenes[b.scene].dark]);
  window.__captions = CAPTIONS;
  logoEl().innerHTML = `${logoSvg}<span>my document memory</span>`;
  if (window.__buildScenes) await window.__buildScenes();
  else { buildS1(); buildS2(); buildS3(); buildS4(); buildS5(); buildS6(); buildS7(); buildS8(); buildS9(); }
  // Scenes are display:none until their time, so load the web fonts explicitly before the first frame.
  await Promise.all(['800 40px Manrope', '600 20px "DM Sans"', '400 20px "DM Mono"', '500 20px "DM Mono"'].map((f) => document.fonts.load(f, 'Aa 123')));
  await document.fonts.ready;
  window.__ready = true;
};
