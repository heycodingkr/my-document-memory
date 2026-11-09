#!/usr/bin/env node
// Prepares the real Google Slides clip for the hackathon cut: a sped-up, cropped, privacy-masked copy of the WAM run
// (Arise 0.1.69 + Muse Spark 1.3 builds a 10-slide deck, 2026-11-03; one run; the deck is that project's, not this one's).
//
//   node demo/video/capture/prep-slides.mjs [--speed 45]
//
// Settings are WAM's own (web-agentic-memory demo/video README "The Muse run in scene 3" and captures/run-muse-deck.json):
//   - source seconds 73..1496: the first 72 s are the Arise start page and the Slides start dialog, which greets the account by first name
//   - crop x0 y142 1414x610: the window below the title bar, session header, tab strip and URL bar (keeps the agent chat list and the page)
//   - the account avatar at 1348,0 66x64 (cropped coordinates) is blurred
//   - the raw file has six short moments where another Arise window came to the front already replaced by a freeze of the last good frame
// Output: demo/out/footage/slides-muse-x<speed>.mp4 (30 fps, H.264, no audio). The raw recording is never copied elsewhere.
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { repo } from './lib.mjs';

const args = process.argv.slice(2);
const speed = Number(args.includes('--speed') ? args[args.indexOf('--speed') + 1] : 45);
const SRC_FROM = 73, SRC_TO = 1496;
const wam = process.env.WAM_REPO || path.resolve(repo, '../web-agentic-memory');
const raw = path.join(wam, 'demo/out/slides-real/MU-raw.mp4');
if (!existsSync(raw)) throw new Error(`raw recording not found: ${raw}`);
const out = path.join(repo, `demo/out/footage/slides-muse-x${speed}.mp4`);
mkdirSync(path.dirname(out), { recursive: true });
const vf = [
  '[0:v]crop=1414:610:0:142,split[a][b]',
  '[b]crop=66:64:1348:0,boxblur=lr=30:lp=3:cr=15:cp=3[bl]',
  `[a][bl]overlay=1348:0,setpts=PTS/${speed},fps=30,format=yuv420p`
].join(';');
const r = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-stats', '-ss', String(SRC_FROM), '-t', String(SRC_TO - SRC_FROM), '-i', raw, '-filter_complex', vf, '-an',
  '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: 'inherit' });
if (r.status !== 0) throw new Error('ffmpeg failed');
const p = spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'stream=width,height,r_frame_rate,nb_frames:format=duration', '-of', 'default=nw=1', out], { encoding: 'utf8' });
console.log(`wrote ${out}\n${p.stdout.trim()}\nexpected duration ${((SRC_TO - SRC_FROM) / speed).toFixed(2)} s`);
