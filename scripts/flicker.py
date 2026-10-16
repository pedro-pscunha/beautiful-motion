#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow", "numpy"]
# ///
"""Flicker and shimmer in a time window, measured. A real move or build changes a region one way; flicker, aliasing
crawl and light-dark-light flashes reverse it. Over every three consecutive samples, a reversal scores
min(|first change|, |second change|) where the two changes have opposite signs, in luma levels (0-255).
Two scales:  tile  mean luma per 24 px tile (flashes, light bands, a boil over an area);
             fine  every pixel (thin lines that crawl, a fine texture that shimmers). Grain or boil you want scores
                   here too, so compare against an earlier export of the same window rather than against zero.
Two steps:   1 (every frame: flicker at the frame rate) and 2 (every other frame: a film on 2s). Read the worse.
usage: uv run <skill>/scripts/flicker.py <frames dir> <t0> <t1> [--fps N] [--vs <other frames dir>]
--fps defaults to the export's timeline.json (written by render_frames.mjs), else 24.
Prints per step and scale: osc (mean reversal energy), max (the worst single flip) and the frame where it happens."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

a = sys.argv[1:]
fps, vs = 24.0, None
for name in ('fps', 'vs'):
    if f'--{name}' in a:
        i = a.index(f'--{name}')
        if i + 1 >= len(a):
            sys.exit(__doc__)
        v = a[i + 1]
        del a[i:i + 2]
        fps, vs = (float(v), vs) if name == 'fps' else (fps, v)
if len(a) != 3 or float(a[1]) >= float(a[2]):
    sys.exit(__doc__)
t0, t1 = float(a[1]), float(a[2])
if '--fps' not in sys.argv and (Path(a[0]) / 'timeline.json').exists():  # written by render_frames.mjs
    fps = float(json.load(open(Path(a[0]) / 'timeline.json'))['fps'])
if fps <= 0:
    sys.exit(__doc__)


def tiles(x):
    h, w = x.shape[0] // 24 * 24, x.shape[1] // 24 * 24
    return x[:h, :w].reshape(h // 24, 24, w // 24, 24).mean(axis=(1, 3))


def measure(d, step):
    want = list(range(round(t0 * fps), round(t1 * fps) + 1, step))
    have = [f for f in want if (d / f'f{f:04d}.png').exists()]
    if len(have) < len(want):
        print(f'  warning: {d}: {len(want) - len(have)} of {len(want)} frames in {t0}-{t1} s are missing; '
              'samples on each side of a gap are compared as if adjacent')
    if len(have) < 3:
        sys.exit(f'{d}: fewer than 3 frames in {t0}-{t1} s')
    acc = {s: [0.0, 0, 0.0, None] for s in ('tile', 'fine')}  # sum of means, count, max, frame of max
    window = []
    for f in have:
        x = np.asarray(Image.open(d / f'f{f:04d}.png').convert('L'), dtype=np.float32)
        window.append((f, {'tile': tiles(x), 'fine': x}))
        if len(window) < 3:
            continue
        (_, p), (fb, q), (_, r) = window
        for s, st in acc.items():
            d1, d2 = q[s] - p[s], r[s] - q[s]
            rev = np.where(d1 * d2 < 0, np.minimum(np.abs(d1), np.abs(d2)), 0.0)
            st[0] += float(rev.mean())
            st[1] += 1
            if float(rev.max()) > st[2]:
                st[2], st[3] = float(rev.max()), fb
        window.pop(0)
    return {s: (st[0] / st[1], st[2], st[3]) for s, st in acc.items()}


dirs = [Path(a[0])] + ([Path(vs)] if vs else [])
for step in (1, 2):
    res = [measure(d, step) for d in dirs]
    for d, r in zip(dirs, res):
        line = '   '.join(f'{s}: osc {o:.3f}, max {m:.1f}' + (f' (frame {at})' if at is not None else '')
                           for s, (o, m, at) in r.items())
        print(f'step {step}  {d}  {line}')
    if vs:
        print(f'step {step}  ratio --vs / first  ' + '   '.join(
            f'{s}: {res[1][s][0] / max(res[0][s][0], 1e-9):.2f}x' for s in ('tile', 'fine')))
