#!/usr/bin/env python3
"""Prepare timestamped public Arise MCP viewport captures for the 90-second cut.

python3 demo/video/capture/prep-arise.py docs --crop 0 250 2100 866
python3 demo/video/capture/prep-arise.py blog --crop 0 270 2100 866

Needs Pillow and ffmpeg. Raw frames stay in ignored demo/out/footage/arise/<name>.
This is an edited sequence: caret-only/idle frames are removed, pauses shortened,
and the final frame held. Label it REAL CAPTURE / EDITED, never a timed benchmark.
The edit manifest retains each original file and capture timestamp.
"""
import argparse
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('name', choices=['docs', 'blog'])
parser.add_argument('--crop', type=int, nargs=4, required=True, metavar=('X', 'Y', 'W', 'H'))
args = parser.parse_args()
repo = Path(__file__).resolve().parents[3]
source = repo / 'demo/out/footage/arise' / args.name
capture = json.loads((source / 'frames.json').read_text())
frames = capture['frames']
assert len(frames) > 2, 'need a genuine multi-frame recording'
x, y, width, height = args.crop
assert min(x, y) >= 0 and min(width, height) > 0
chosen, previous, previous_time = [], None, -1
for index, frame in enumerate(frames):
    assert math.isfinite(frame['t']) and frame['t'] > previous_time, 'timestamps must increase'
    previous_time = frame['t']
    file = (source / frame['file']).resolve()
    assert file.parent == source.resolve(), 'frame path must stay in its capture directory'
    with Image.open(file) as image:
        assert x + width <= image.width and y + height <= image.height, 'crop outside viewport'
        thumb = image.crop((x, y, x + width, y + height)).convert('L').resize((444, 183))
        change = 255 if previous is None else ImageStat.Stat(ImageChops.difference(thumb, previous)).mean[0]
        if change > 0.08 or index == len(frames) - 1:
            chosen.append(frame)
            previous = thumb
assert len(chosen) > 5, 'recording must show changing editor content'
weights = [min(0.8, max(0.12, b['t'] - a['t'])) for a, b in zip(chosen, chosen[1:])]
scale = 30 / sum(weights)
durations = [weight * scale for weight in weights] + [2.0]
lines = ['ffconcat version 1.0']
for frame, duration in zip(chosen, durations):
    lines += [f"file '{frame['file']}'", f'duration {duration:.6f}']
lines.append(f"file '{chosen[-1]['file']}'")
concat = source / 'edit.ffconcat'
concat.write_text('\n'.join(lines) + '\n')
out = source.parent / f'{args.name}-edited.mp4'
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(concat),
                '-vf', f'crop={width}:{height}:{x}:{y},scale=1776:732:flags=lanczos,fps=30,format=yuv420p',
                '-frames:v', '960', '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16',
                '-movflags', '+faststart', str(out)], check=True)
manifest = {'source': capture['source'], 'raw_elapsed_s': capture['elapsed_s'], 'raw_frames': len(frames),
            'crop': args.crop, 'output': str(out.relative_to(repo)), 'duration_s': 32,
            'label': 'REAL CAPTURE · EDITED', 'frames': [dict(**f, edited_duration_s=d) for f, d in zip(chosen, durations)]}
(source / 'edit.json').write_text(json.dumps(manifest, indent=2))
print(f'{out}: {len(frames)} captured frames -> {len(chosen)} editor changes, 32 seconds')
