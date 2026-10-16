#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "opencv-python-headless"]
# ///
"""Fine film grain over exported frames, deterministic: run it on the frames before the encode.
Reads every f<digits>.png in <in dir> (8- or 16-bit, RGB or RGBA; alpha is kept) and writes the same names to <out dir>,
plus timeline.json if there is one.
The grain is:
  luma only     the same offset on R, G and B: hue and saturation stay, and nothing lands on the colour planes, which
                a 4:2:0 encode halves into blotches;
  fine          white noise blurred to --size px, minus its own blur at twice that, so nothing is left at the scale of
                blotches (a 24 px patch keeps its mean);
  zero-mean     region means do not move;
  by tone       full strength in the midtones, about half in deep shadows (where compressed grain turns to blocks)
                and a third at white;
  per drawing   seeded by frame // --on, so a film on 2s keeps each held pair identical, and a re-run gives the same
                pixels in any order.
usage: uv run grain.py <in dir> <out dir> [--amount 2.8] [--size 0.8] [--on 2] [--seed 1] [--from N] [--to M] [--workers N]
       <frames> | uv run grain.py --raw <W>x<H> [--start N] [the same options] | <encoder>
  --amount  grain std in 8-bit code values in the midtones, on the output frames (2.5-3: subtle but visible)
  --size    grain radius in px at the film's own size (Gaussian sigma; 0.8 at 1080 px, scale it with the short side)
  --on      frames per drawing: 2 for a film on 2s (the drawings change on even frames), 1 for a new grain every frame
  --raw     read raw 16-bit RGB frames (ffmpeg -f rawvideo -pix_fmt rgb48le -) from stdin and write them grained to
            stdout, in order, so the frames never go to disk; --start is the number of the first frame (the seed), and
            the pixels equal what the folder mode gives for frames with those numbers"""
import os
import re
import shutil
import sys
from collections import deque
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import cv2
import numpy as np

CURVE_Y = [0.0, 0.12, 0.40, 0.72, 0.92, 1.0]  # luma, 0 = black
CURVE_S = [0.25, 0.50, 1.00, 1.00, 0.70, 0.35]  # share of --amount at that luma
NUM = {'amount': float, 'size': float, 'on': int, 'seed': int, 'from': int, 'to': int, 'workers': int, 'start': int, 'raw': str}


def opts(a):
    o = {'amount': 2.8, 'size': 0.8, 'on': 2, 'seed': 1, 'from': None, 'to': None, 'workers': os.cpu_count() or 4, 'start': 0,
         'raw': None}
    pos = []
    while a:
        x = a.pop(0)
        if x.startswith('--') and x[2:] in NUM and a:
            o[x[2:]] = NUM[x[2:]](a.pop(0))
        elif x.startswith('--'):
            sys.exit(f'unknown or incomplete option {x}\n\n{__doc__}')
        else:
            pos.append(x)
    if (len(pos) != (0 if o['raw'] else 2) or o['amount'] < 0 or o['size'] <= 0 or o['on'] < 1 or o['workers'] < 1
            or (o['raw'] and not re.fullmatch(r'\d+x\d+', o['raw']))):
        sys.exit(__doc__)
    return pos, o


def field(h, w, n, o):
    rng = np.random.default_rng([o['seed'], n // o['on']])  # keyed by the drawing, never by render order
    g = cv2.GaussianBlur(rng.standard_normal((h, w), dtype=np.float32), (0, 0), o['size'], borderType=cv2.BORDER_REFLECT)
    g -= cv2.GaussianBlur(g, (0, 0), 2 * o['size'], borderType=cv2.BORDER_REFLECT)
    return g / g.std()


def add(im, n, o):
    """frame n with its grain; im is 8- or 16-bit, channels in OpenCV's order (B, G, R[, A])"""
    full = 65535.0 if im.dtype == np.uint16 else 255.0
    rgb = im[..., :3].astype(np.float32) / full
    y = 0.0722 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.2126 * rgb[..., 2]
    s = np.interp(cv2.GaussianBlur(y, (0, 0), 2.0), CURVE_Y, CURVE_S).astype(np.float32)
    d = (o['amount'] / 255.0) * s * field(*y.shape, n, o)
    out = im.copy()
    out[..., :3] = np.clip(np.rint((rgb + d[..., None]) * full), 0, full).astype(im.dtype)
    return out


def one(job):
    src, dst, n, o = job
    im = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
    if im is None or im.ndim != 3 or im.shape[2] not in (3, 4):
        raise ValueError(f'{src}: not an RGB or RGBA PNG')
    tmp = dst.with_name(dst.stem + '.part.png')  # written whole, then renamed: a killed run leaves no half frame
    if not cv2.imwrite(str(tmp), add(im, n, o), [cv2.IMWRITE_PNG_COMPRESSION, 1]):
        raise OSError(f'cannot write {tmp}')
    os.replace(tmp, dst)


def one_raw(job):
    buf, w, h, n, o = job
    rgb = np.frombuffer(buf, '<u2').reshape(h, w, 3)
    return add(rgb[..., ::-1], n, o)[..., ::-1].astype('<u2').tobytes()  # RGB in, B-G-R for add(), RGB out


def stream(o):
    w, h = (int(v) for v in o['raw'].split('x'))
    size, n, pending = w * h * 6, o['start'], deque()
    src, dst = sys.stdin.buffer, sys.stdout.buffer
    with ProcessPoolExecutor(max_workers=o['workers']) as ex:
        while True:
            buf = src.read(size)
            if buf and len(buf) != size:
                sys.exit(f'grain: stdin ended inside frame {n} ({len(buf)} of {size} bytes): is it {o["raw"]} rgb48le?')
            if buf:
                pending.append(ex.submit(one_raw, (buf, w, h, n, o)))
                n += 1
            while pending and (len(pending) >= 2 * o['workers'] or not buf):
                dst.write(pending.popleft().result())  # in order: frame n leaves before frame n + 1
            if not buf:
                break
    dst.flush()
    print(f'grain: {n - o["start"]} raw frames ({o["start"]}-{n - 1}), {w}x{h}: amount {o["amount"]}, size {o["size"]} px, '
          f'on {o["on"]}s, seed {o["seed"]}', file=sys.stderr)


def main():
    pos, o = opts(sys.argv[1:])
    if o['raw']:
        return stream(o)
    src, dst = (Path(p) for p in pos)
    frames = sorted((int(m.group(1)), p) for p in src.glob('f*.png') if (m := re.fullmatch(r'f_?(\d+)', p.stem)))
    frames = [(n, p) for n, p in frames if (o['from'] is None or n >= o['from']) and (o['to'] is None or n <= o['to'])]
    if not frames:
        sys.exit(f'no f<digits>.png frames in {src}')
    dst.mkdir(parents=True, exist_ok=True)
    if src.resolve() == dst.resolve():
        sys.exit('write to a new folder: the source frames stay as they are')
    if (src / 'timeline.json').exists():
        shutil.copy(src / 'timeline.json', dst / 'timeline.json')
    with ProcessPoolExecutor(max_workers=o['workers']) as ex:
        list(ex.map(one, [(p, dst / p.name, n, o) for n, p in frames], chunksize=4))
    print(f'grain: {len(frames)} frames ({frames[0][0]}-{frames[-1][0]}) -> {dst}: amount {o["amount"]}, size {o["size"]} px, '
          f'on {o["on"]}s, seed {o["seed"]}')


if __name__ == '__main__':
    main()
