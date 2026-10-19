#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow", "numpy"]
# ///
"""One-frame pops in an export: a region that steps in a single frame and holds (a pose that snaps, a stroke laid
whole, a layer swapped, a cache rebuilt differently), where motion changes it over several frames in a row. (A flash
that goes back the next frame is flicker: flicker.py.) Per 48 px tile, the mean luma change from frame f-1 to f is a
pop when it is over 6 levels and over 3x the change on either side of it (f-2 to f-1 and f to f+1). A cut is a step by design: list the cut frames in --cuts and they are skipped. A piece
placed opaque (a shard pressed in, a clay lump slapped on) is a pop by construction: list those frames as contacts
and judge them on a strip of consecutive frames.
usage: uv run <skill>/scripts/glitch_scan.py <frames dir> [from] [to] [--cuts f1,f2,...] [--fps N]
from and to are frame numbers (default: the whole export); --fps (for the times printed) defaults to the export's
timeline.json (written by render_frames.mjs), else 24.
Prints each frame with pops, its worst tile (centre and jump in levels) and up to three more. Exit 1 when it finds
any, 0 when it finds none."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

a = sys.argv[1:]
fps, cuts = None, set()
for name in ('fps', 'cuts'):
    if f'--{name}' in a:
        i = a.index(f'--{name}')
        if i + 1 >= len(a):
            sys.exit(__doc__)
        v = a[i + 1]
        del a[i:i + 2]
        fps, cuts = (float(v), cuts) if name == 'fps' else (fps, {int(x) for x in v.split(',') if x})
if not 1 <= len(a) <= 3:
    sys.exit(__doc__)
d = Path(a[0])
have = sorted(int(p.stem[1:]) for p in d.glob('f*.png') if p.stem[1:].isdigit())
if not have:
    sys.exit(f'{d}: no frames (f0000.png ...)')
f0 = int(a[1]) if len(a) > 1 else have[0]
f1 = int(a[2]) if len(a) > 2 else have[-1]
if fps is None:
    fps = float(json.load(open(d / 'timeline.json'))['fps']) if (d / 'timeline.json').exists() else 24.0
T, ABS, RATIO = 48, 6.0, 3.0
present = set(have)
cache = {}


def tiles(f):
    if f not in cache:
        x = np.asarray(Image.open(d / f'f{f:04d}.png').convert('L'), dtype=np.float32)
        h, w = x.shape[0] // T * T, x.shape[1] // T * T
        cache[f] = x[:h, :w].reshape(h // T, T, w // T, T)
        if len(cache) > 6:
            cache.pop(min(cache))
    return cache[f]


pops, gaps = {}, 0
for f in range(f0 + 2, f1):   # each test needs f-2 .. f+1
    if any(c in cuts for c in (f - 1, f, f + 1)):
        continue
    if not all(g in present for g in range(f - 2, f + 2)):
        gaps += 1
        continue
    A, B, C, D = (tiles(g) for g in range(f - 2, f + 2))
    before = np.abs(B - A).mean(axis=(1, 3))
    now = np.abs(C - B).mean(axis=(1, 3))
    after = np.abs(D - C).mean(axis=(1, 3))
    bad = (now > ABS) & (now > RATIO * np.maximum(before, 0.5)) & (now > RATIO * np.maximum(after, 0.5))
    if bad.any():
        ys, xs = np.nonzero(bad)
        pops[f] = sorted(((int(x * T + T // 2), int(y * T + T // 2), round(float(now[y, x]), 1))
                          for y, x in zip(ys, xs)), key=lambda p: -p[2])
if gaps:
    print(f'warning: {gaps} frames in {f0}-{f1} were not tested: a frame next to them is missing')
print(f'{d}: frames {f0}-{f1}, {len(pops)} with one-frame pops (tile {T} px, over {ABS:g} levels and over {RATIO:g}x '
      'the change on both sides)')
for f, ts in pops.items():
    x, y, lv = ts[0]
    more = ', '.join(f'({p[0]}, {p[1]})' for p in ts[1:4])
    print(f'  f{f:04d} ({f / fps:7.3f} s): {len(ts)} tiles, worst {lv} levels at x {x}, y {y}' + (f'; also {more}' if more else ''))
sys.exit(1 if pops else 0)
