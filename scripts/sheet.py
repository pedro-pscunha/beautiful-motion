#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=10.1"]
# ///
"""A numbered contact sheet from images (stills, or frames picked from an export), for feedback by number.
usage: uv run <skill>/scripts/sheet.py <out.jpg> <img> [<img> ...] [--cols 5] [--cell 360] [--labels "chalk|map|woodcut"]
       uv run <skill>/scripts/sheet.py <out.jpg> --frames <dir> --times 1.5,4.0,6.5 [--fps 24] [...]
Each cell is titled "N. label" (the label: the time with --frames, else the file name). --fps defaults to the
export's timeline.json, else 24. Phone-size check: --cell 390."""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

for stream in (sys.stdout, sys.stderr):
    stream.reconfigure(errors='replace')
a = sys.argv[1:]


def opt(name, default=None):
    if f'--{name}' in a:
        i = a.index(f'--{name}')
        if i + 1 >= len(a):
            sys.exit(__doc__)
        v = a[i + 1]
        del a[i:i + 2]
        return v
    return default


cols, cell = int(opt('cols', '5')), int(opt('cell', '360'))
labels, frames, times, fps = opt('labels'), opt('frames'), opt('times'), opt('fps')
if fps is None and frames and (Path(frames) / 'timeline.json').exists():  # written by render_frames.mjs
    fps = json.load(open(Path(frames) / 'timeline.json'))['fps']
fps = float(fps or 24)
if not a or bool(frames) != bool(times) or (frames and len(a) != 1) or (not frames and len(a) < 2):
    sys.exit(__doc__)
out = Path(a[0])
if frames:
    files = [Path(frames) / f'f{round(float(t) * fps):04d}.png' for t in times.split(',')]
    names = [f'{t} s' for t in times.split(',')]
else:
    files = [Path(x) for x in a[1:]]
    names = [f.stem for f in files]
if labels:
    names = labels.split('|')
    if len(names) != len(files):
        sys.exit(f'{len(names)} labels for {len(files)} images: give one label per image')
absent = [str(f) for f in files if not f.exists()]
if absent:
    sys.exit('not found: ' + ', '.join(absent))
pad, bar = 12, 34
rows = -(-len(files) // cols)
sheet = Image.new('RGB', (cols * (cell + pad) + pad, rows * (cell + bar + pad) + pad), (242, 236, 224))
d = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype('DejaVuSans.ttf', 18)
except OSError:
    font = ImageFont.load_default(size=18)
for k, (f, name) in enumerate(zip(files, names)):
    im = Image.open(f).convert('RGB')
    im.thumbnail((cell, cell), Image.LANCZOS)
    x, y = pad + (k % cols) * (cell + pad), pad + (k // cols) * (cell + bar + pad)
    sheet.paste(im, (x, y))
    d.text((x, y + im.height + 6), f'{k + 1}. {name}', fill=(30, 26, 22), font=font)
out.parent.mkdir(parents=True, exist_ok=True)
sheet.save(out, quality=90)
print(f'{out}: {len(files)} cells, {cols} columns, {cell} px')
