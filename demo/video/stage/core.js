'use strict';
// Stage core: time helpers, language switch, icons, scene registry. Everything here is a pure function of time.
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const ease = (x) => 1 - Math.pow(1 - clamp(x), 3);
const seg = (t, a, b) => clamp((t - a) / (b - a));
const fade = (t, a, b) => ease(seg(t, a, b));
const lerp = (a, b, p) => a + (b - a) * p;
const el = (tag, cls, html, parent, css) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; if (css) e.style.cssText = css; if (parent) parent.appendChild(e); return e; };
// A: an absolutely positioned div. css carries left/top/width/...; extra classes go in cls.
const A = (parent, css, html, cls) => el('div', 'abs' + (cls ? ' ' + cls : ''), html == null ? '' : html, parent, css);
const show = (e, a, dy = 0, dx = 0, scale = 1) => { e.style.opacity = a; e.style.transform = `translate(${(1 - a) * dx}px, ${(1 - a) * dy}px) scale(${lerp(.97, 1, a) * scale})`; };
const typed = (s, p) => s.slice(0, Math.floor(clamp(p) * s.length));
const press = (e, t, at, dur = 0.5) => { const p = seg(t, at, at + dur); e.style.transform = `scale(${1 - 0.05 * Math.sin(Math.PI * p)})`; };

const LANG = new URLSearchParams(location.search).get('lang') === 'ko' ? 'ko' : 'en';   // English is the default
document.documentElement.lang = LANG;
const tr = (ko, en) => (LANG === 'ko' ? ko : en);

let SCRIPT = null;                       // script.json, loaded in __init
let CAPTIONS = [];                       // [start, end, text, onDark]
const scenes = [];
window.__overlays = [];                  // real clips composited by build.mjs: { id, file, src, speed, crop, mask, x, y, w, h, from, to }
const addScene = (id, cfg) => {
  const w = SCRIPT.scenes[id];
  const e = el('div', 'scene' + (w.dark ? ' dark' : ''), '', document.getElementById('scenes'));
  e.id = id;
  scenes.push({ id, e, start: w.start, end: w.end, dark: !!w.dark, ...cfg });
  return e;
};

const chip = (txt, cls = '', css = '') => `<span class="chip ${cls}" style="${css}">${txt}</span>`;

// ── icons (original, generic; no third-party logos) ──
const ICONS = {
  tablet: '<svg viewBox="0 0 48 48"><rect x="7" y="9" width="34" height="30" rx="7" fill="#d9b88a" stroke="#a98456" stroke-width="2"/><g stroke="#8a6638" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" fill="none"><path d="M14 18l3 2-3 2M21 20h8M14 28l3 2-3 2M21 30h12"/></g></svg>',
  scroll: '<svg viewBox="0 0 48 48"><rect x="12" y="11" width="24" height="26" fill="#f1e4b9" stroke="#c4ad6c" stroke-width="2"/><ellipse cx="12" cy="24" rx="4" ry="13" fill="#e3cf97" stroke="#c4ad6c" stroke-width="2"/><ellipse cx="36" cy="24" rx="4" ry="13" fill="#e3cf97" stroke="#c4ad6c" stroke-width="2"/><path d="M18 19h12M18 24h9M18 29h12" stroke="#8c7a45" stroke-width="2" stroke-linecap="round"/></svg>',
  press: '<svg viewBox="0 0 48 48"><g fill="#d6ddd8" stroke="#7d8a84" stroke-width="2"><rect x="5" y="14" width="11" height="20" rx="1.5"/><rect x="18.5" y="14" width="11" height="20" rx="1.5"/><rect x="32" y="14" width="11" height="20" rx="1.5"/></g><g fill="#254b3c" font-family="Manrope, sans-serif" font-weight="800" font-size="12" text-anchor="middle"><text x="10.5" y="28.5">A</text><text x="24" y="28.5">B</text><text x="37.5" y="28.5">C</text></g></svg>',
  typewriter: '<svg viewBox="0 0 48 48"><rect x="14" y="6" width="20" height="14" fill="#fffef9" stroke="#7d8a84" stroke-width="2"/><path d="M18 11h12M18 15h8" stroke="#8aa095" stroke-width="2" stroke-linecap="round"/><rect x="7" y="19" width="34" height="19" rx="4" fill="#3b4a43"/><g fill="#d8ef78"><circle cx="14" cy="26" r="1.8"/><circle cx="20" cy="26" r="1.8"/><circle cx="26" cy="26" r="1.8"/><circle cx="32" cy="26" r="1.8"/><rect x="15" y="31" width="18" height="2.4" rx="1.2"/></g></svg>',
  wp: '<svg viewBox="0 0 48 48"><rect x="8" y="8" width="32" height="24" rx="3" fill="#dfe6df" stroke="#6b7c73" stroke-width="2"/><rect x="12" y="12" width="24" height="16" fill="#0f2a22"/><path d="M15 17h14M15 21h18M15 25h10" stroke="#d8ef78" stroke-width="2" stroke-linecap="round"/><path d="M18 37h12M24 32v5" stroke="#6b7c73" stroke-width="3" stroke-linecap="round"/></svg>',
  web: '<svg viewBox="0 0 48 48"><rect x="6" y="9" width="36" height="30" rx="4" fill="#fffef9" stroke="#254b3c" stroke-width="2"/><path d="M6 17h36" stroke="#254b3c" stroke-width="2"/><g fill="#d8ef78" stroke="#254b3c" stroke-width="1.2"><circle cx="11" cy="13" r="1.6"/><circle cx="16" cy="13" r="1.6"/></g><path d="M12 24h24M12 29h18M12 34h21" stroke="#254b3c" stroke-width="2" stroke-linecap="round"/></svg>',
  form: '<svg viewBox="0 0 48 48"><rect x="9" y="6" width="30" height="36" rx="4" fill="#fffef9" stroke="#254b3c" stroke-width="2.4"/><rect x="14" y="11" width="20" height="5" rx="1.5" fill="#254b3c"/><rect x="14" y="20" width="9" height="8" rx="1.5" fill="#d8ef78" stroke="#254b3c" stroke-width="1.6"/><rect x="25" y="20" width="9" height="8" rx="1.5" fill="#d8ef78" stroke="#254b3c" stroke-width="1.6"/><path d="M14 33h20M14 37h13" stroke="#254b3c" stroke-width="2" stroke-linecap="round"/></svg>',
  refs: '<svg viewBox="0 0 48 48"><rect x="13" y="6" width="26" height="32" rx="4" fill="#e8f0da" stroke="#254b3c" stroke-width="2"/><rect x="8" y="11" width="26" height="32" rx="4" fill="#fffef9" stroke="#254b3c" stroke-width="2.4"/><rect x="13" y="19" width="16" height="5" rx="1.5" fill="#d8ef78"/><path d="M13 16h14M13 29h16M13 35h9" stroke="#254b3c" stroke-width="2" stroke-linecap="round"/></svg>',
  rules: '<svg viewBox="0 0 48 48"><rect x="8" y="8" width="32" height="32" rx="6" fill="#fffef9" stroke="#254b3c" stroke-width="2.4"/><text x="24" y="31" text-anchor="middle" font-family="Manrope, sans-serif" font-weight="800" font-size="19" fill="#254b3c">Aa</text></svg>',
  lock: '<svg viewBox="0 0 48 48"><path d="M15 21v-6a9 9 0 0 1 18 0v6" fill="none" stroke="#254b3c" stroke-width="3.2" stroke-linecap="round"/><rect x="9" y="21" width="30" height="21" rx="5" fill="#d8ef78" stroke="#254b3c" stroke-width="2.6"/><circle cx="24" cy="30.5" r="3" fill="#254b3c"/><path d="M24 32v4" stroke="#254b3c" stroke-width="2.6" stroke-linecap="round"/></svg>',
  shield: '<svg viewBox="0 0 48 48"><path d="M24 5l15 5v12c0 10-6.5 17-15 21C15.500 39 9 32 9 22V10z" fill="#d8ef78" stroke="#254b3c" stroke-width="2.6" stroke-linejoin="round"/><path d="M17 24l5 5 9-11" fill="none" stroke="#254b3c" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  versions: '<svg viewBox="0 0 48 48"><rect x="15" y="5" width="26" height="20" rx="4" fill="#e8f0da" stroke="#254b3c" stroke-width="2"/><rect x="11" y="13" width="26" height="20" rx="4" fill="#cfe39a" stroke="#254b3c" stroke-width="2"/><rect x="7" y="21" width="26" height="20" rx="4" fill="#fffef9" stroke="#254b3c" stroke-width="2.4"/><path d="M13 29h14M13 35h8" stroke="#254b3c" stroke-width="2" stroke-linecap="round"/></svg>',
  file: '<svg viewBox="0 0 48 48"><path d="M12 5h17l9 9v27a2 2 0 0 1-2 2H12a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z" fill="#fffef9" stroke="#254b3c" stroke-width="2.4" stroke-linejoin="round"/><path d="M29 5v9h9" fill="#d8ef78" stroke="#254b3c" stroke-width="2.4" stroke-linejoin="round"/><path d="M15 23h18M15 29h18M15 35h11" stroke="#254b3c" stroke-width="2.4" stroke-linecap="round"/></svg>',
  deck: '<svg viewBox="0 0 48 48"><rect x="5" y="9" width="38" height="25" rx="3" fill="#fffef9" stroke="#254b3c" stroke-width="2.4"/><rect x="10" y="14" width="16" height="4" rx="1.5" fill="#254b3c"/><path d="M10 23h24M10 28h14" stroke="#254b3c" stroke-width="2" stroke-linecap="round"/><path d="M17 41l7-7 7 7" fill="none" stroke="#254b3c" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  check: '<svg viewBox="0 0 48 48"><circle cx="24" cy="24" r="20" fill="#254b3c"/><path d="M14 25l7 7 13-15" fill="none" stroke="#d8ef78" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  warn: '<svg viewBox="0 0 48 48"><path d="M24 6l19 34H5z" fill="#fbe4dc" stroke="#e0714f" stroke-width="3" stroke-linejoin="round"/><path d="M24 18v10" stroke="#a8442a" stroke-width="4" stroke-linecap="round"/><circle cx="24" cy="34" r="2.6" fill="#a8442a"/></svg>'
};
const icon = (name, px = 56, css = '') => `<span class="ic" style="width:${px}px;height:${px}px;${css}">${ICONS[name]}</span>`;
const logoSvg = '<svg viewBox="0 0 46 46"><rect class="g-bg" width="46" height="46" rx="12"/><path class="g-page" d="M14 9h13l7 7v20a2 2 0 0 1-2 2H14a2 2 0 0 1-2-2V11a2 2 0 0 1 2-2z"/><path class="g-fold" d="M27 9v7h7z"/><rect class="g-line" x="16" y="21" width="12" height="2.4" rx="1.2"/><rect class="g-line" x="16" y="26" width="9" height="2.4" rx="1.2"/><circle class="g-dot" cx="32.500" cy="33.500" r="5"/></svg>';
