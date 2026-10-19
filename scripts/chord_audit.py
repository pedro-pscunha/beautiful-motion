#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow", "numpy"]
# ///
"""Does a frame stay inside its Wada combination? Every pixel with Lab chroma over 12 is a colour; the rest are the
neutrals (paper, ink, greys, mortar). Each colour is matched to the nearest colour of the combination by hue angle in
Lab: lightening toward the paper or darkening toward the ink keeps the hue, so it stays in the combination. A colour
more than 22 degrees from every hue of the combination is off it: a stray a critic will name.
usage: uv run <skill>/scripts/chord_audit.py <frame.png> <#hex> [#hex ...] [--box x0,y0,x1,y1]
The hexes are the combination's (`wada.py show <n>` prints them), plus any colour the film keeps constant on purpose
(a recurring object's own red). --box measures one region.
Prints the share of coloured pixels near each colour, the share off the combination (of the colour and of the frame),
and where the off colours cluster, by 30-degree hue band. Thin blends at edges between two colours of the combination
land here too: a fraction of a percent of the frame is normal; a cluster is a stray."""
import sys

import numpy as np
from PIL import Image

CHROMA_MIN, OFF_DEG = 12.0, 22.0
a = sys.argv[1:]
box = None
if '--box' in a:
    i = a.index('--box')
    if i + 1 >= len(a):
        sys.exit(__doc__)
    box = tuple(int(v) for v in a[i + 1].split(','))
    del a[i:i + 2]
if len(a) < 2 or not all(h.startswith('#') and len(h) == 7 for h in a[1:]) or (box and len(box) != 4):
    sys.exit(__doc__)
path, hexes = a[0], a[1:]


def lab(rgb):
    c = rgb / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


im = np.asarray(Image.open(path).convert('RGB'), dtype=np.float64)
if box:
    im = im[box[1]:box[3], box[0]:box[2]]
Ww = im.shape[1]
L = lab(im.reshape(-1, 3))
C = np.hypot(L[:, 1], L[:, 2])
h = np.degrees(np.arctan2(L[:, 2], L[:, 1])) % 360
chord = lab(np.array([[int(x[i:i + 2], 16) for i in (1, 3, 5)] for x in hexes], dtype=np.float64))
cC = np.hypot(chord[:, 1], chord[:, 2])
ch = np.degrees(np.arctan2(chord[:, 2], chord[:, 1])) % 360
col = C > CHROMA_MIN
if not col.any():
    sys.exit(f'{path}: no coloured pixels (chroma over {CHROMA_MIN:g})')
dist = np.abs(((h[col, None] - ch[None, :]) + 180) % 360 - 180)
dist = np.where(cC[None, :] < 18, dist * 0.6, dist)   # a near-neutral colour owns little hue: let its tints match it
near, off = dist.argmin(1), dist.min(1) > OFF_DEG
print(f'{path}: {col.mean():.1%} of the pixels are coloured (chroma over {CHROMA_MIN:g})')
for k, x in enumerate(hexes):
    print(f'  {x}  hue {ch[k]:5.1f}  chroma {cC[k]:5.1f}  {np.mean(near == k):6.1%} of the colour')
print(f'  off the combination (over {OFF_DEG:g} degrees from every hue): {off.mean():.2%} of the colour, '
      f'{off.sum() / len(C):.2%} of the frame')
idx = np.flatnonzero(col)[off]
ys, xs, hs = idx // Ww, idx % Ww, h[col][off]
for lo in range(0, 360, 30):
    m = (hs >= lo) & (hs < lo + 30)
    if m.sum() > 0.0005 * len(C):
        print(f'    hue {lo:3d}-{lo + 30:3d}: {int(m.sum()):7d} px, centred near x {int(np.median(xs[m]))}, '
              f'y {int(np.median(ys[m]))}')
