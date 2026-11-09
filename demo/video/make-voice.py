#!/usr/bin/env python3
"""Adds a voice-over to a silent render of the demo-day video.

  python3 demo/video/make-voice.py --dry-run                      # English is the default; add --lang ko for Korean
  python3 demo/video/make-voice.py demo/out/video/mdm-demo-day.en.mp4 demo/out/video/mdm-demo-day.en.vo.mp4

Reads script.json, the same file the burned-in captions come from. Each beat's `vo` text (its caption when there is no `vo`)
is synthesised once with ElevenLabs and cached by text in demo/out/voice-cache/ (git-ignored), so a rerun only pays for beats
whose text changed. Beats are placed at their start time, sped up to at most 1.25x when longer than their window, mixed,
normalised to -16 LUFS and muxed into the video without re-encoding it.

This sends the narration text to a third-party service and spends credits. Run --dry-run first, and run the real thing only
after the owner has approved it. The key comes from ELEVENLABS_API_KEY or ~/.config/mdm-demo/elevenlabs.key (never commit it;
it needs text-to-speech access). The Korean voice_id in script.json must be chosen by listening first.
"""
import argparse, hashlib, json, os, subprocess, sys, urllib.error, urllib.request

here = os.path.dirname(os.path.abspath(__file__))
repo = os.path.abspath(os.path.join(here, '..', '..'))
cache = os.environ.get('MDM_VOICE_CACHE', os.path.join(repo, 'demo', 'out', 'voice-cache'))

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('--lang', choices=['ko', 'en'], default='en', help='voice-over language (default: en)')
ap.add_argument('--dry-run', action='store_true', help='print the beats and the character count; no network, no key needed')
ap.add_argument('video_in', nargs='?')
ap.add_argument('video_out', nargs='?')
args = ap.parse_args()
if not args.dry_run and not (args.video_in and args.video_out):
    ap.error('video_in and video_out are required unless --dry-run')

spec = json.load(open(os.path.join(here, 'script.json'), encoding='utf-8'))
voice = spec['voice'][args.lang]
beats = [{'id': b['id'], 'start': b['start'], 'end': b['end'], 'text': b[args.lang].get('vo') or b[args.lang]['cap']} for b in spec['beats']]
total = spec['total_s']

if args.dry_run:
    n = 0
    for b in beats:
        n += len(b['text'])
        print(f"{b['id']}  {b['start']:6.1f}-{b['end']:6.1f}s  {len(b['text']):3d} chars  {b['text']}")
    print(f"\n{len(beats)} beats, {n} characters to synthesise ({args.lang}); voice: {voice.get('name') or 'NOT CHOSEN'} {voice.get('voice_id') or ''}")
    sys.exit(0)

if not voice.get('voice_id'):
    sys.exit(f"script.json voice.{args.lang}.voice_id is not set. Pick a voice by listening, then put its voice_id there.")
os.makedirs(cache, exist_ok=True)

def api_key():
    k = os.environ.get('ELEVENLABS_API_KEY')
    if k:
        return k.strip()
    p = os.path.expanduser('~/.config/mdm-demo/elevenlabs.key')
    if os.path.exists(p):
        return open(p).read().strip()
    sys.exit('no ElevenLabs key: set ELEVENLABS_API_KEY or create ~/.config/mdm-demo/elevenlabs.key')

def mp3_for(text):
    h = hashlib.sha1(json.dumps([voice['voice_id'], voice['model_id'], voice['settings'], text], ensure_ascii=False).encode()).hexdigest()[:16]
    path = os.path.join(cache, h + '.mp3')
    if not os.path.exists(path):
        body = json.dumps({'text': text, 'model_id': voice['model_id'], 'voice_settings': voice['settings']}).encode()
        req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{voice['voice_id']}?output_format=mp3_44100_128", data=body,
                                     headers={'xi-api-key': api_key(), 'Content-Type': 'application/json', 'Accept': 'audio/mpeg'})
        try:
            with urllib.request.urlopen(req, timeout=120) as r, open(path, 'wb') as f:
                f.write(r.read())
        except urllib.error.HTTPError as e:
            if os.path.exists(path):
                os.remove(path)
            sys.exit(f"ElevenLabs returned HTTP {e.code}: {e.read()[:300].decode('utf-8', 'replace')}")
        print('synthesised', len(text), 'characters')
    return path

def duration(path):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], text=True))

inputs, chains, labels = [], [], []
for i, b in enumerate(beats):
    p = mp3_for(b['text'])
    d, win = duration(p), b['end'] - b['start']
    tempo = min(1.25, d / win) if d > win else 1.0
    if d / tempo > win + 0.35:
        print(f"warning: beat {b['id']} ({d:.2f} s) does not fit its {win:.2f} s window; shorten its vo text in script.json")
    ms = int(b['start'] * 1000)
    inputs += ['-i', p]
    chains.append(f"[{i}:a]atempo={tempo:.4f},adelay={ms}|{ms},apad[a{i}]")
    labels.append(f'[a{i}]')
fc = ';'.join(chains) + ';' + ''.join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,atrim=0:{total},loudnorm=I=-16:TP=-1.5:LRA=11,apad=whole_dur={total}[aout]"
track = os.path.join(cache, f'track.{args.lang}.wav')
subprocess.check_call(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', fc, '-map', '[aout]', '-ar', '44100', '-ac', '2', track])
subprocess.check_call(['ffmpeg', '-y', '-loglevel', 'error', '-i', args.video_in, '-i', track, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                       '-shortest', '-movflags', '+faststart', args.video_out])
print('wrote', args.video_out)
