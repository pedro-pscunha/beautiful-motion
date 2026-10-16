#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Sanzo Wada's colour combinations (A Dictionary of Color Combinations), from the open dataset at
github.com/mattdesl/dictionary-of-colour-combinations (MIT licence, (c) 2020 Matt DesLauriers; first compiled by
Dain M. Blodorn Kim). The first run downloads its colors.json, pinned to one commit and checked by SHA256, to
.work/wada/colors.json under the working directory (the project folder); later runs read that copy, offline.
usage:
  uv run wada.py show N [N ...]     the colours of combination N, and a comment line to paste next to them in the code
  uv run wada.py find [filters]     the combinations that pass every filter, the most chromatic first
Each colour is classed by its HSV hue h (degrees) and saturation s, and its Lab lightness L. A colour with
s < --sat is a neutral: it counts for --dark, but never as warm, cool, earth or in a --hue range."""
import argparse
import colorsys
import hashlib
import json
import math
import os
import sys
import urllib.request
from pathlib import Path

for stream in (sys.stdout, sys.stderr):
    stream.reconfigure(errors='replace')

URL = ('https://raw.githubusercontent.com/mattdesl/dictionary-of-colour-combinations/'
       'd44d2b5a18cf595aa536676a5cf67046a6b503f6/colors.json')
SHA256 = '555f11c32eb8133078fd470dd7d5320533aaa8b636f12fa06a8dd3d0ee2703b4'
CACHE = Path('.work') / 'wada' / 'colors.json'


def check(colours, where):
    ids = {n for c in colours for n in c.get('combinations', [])}
    if len(colours) != 159 or ids != set(range(1, 349)):
        sys.exit(f'{where}: want 159 colours in combinations 1-348, found {len(colours)} colours, {len(ids)} combinations')
    return colours


def load(data):
    if data:
        return check(json.loads(Path(data).read_text(encoding='utf-8')), data)
    if not CACHE.exists():
        print(f'downloading the dataset once, to {CACHE}', file=sys.stderr)
        try:
            with urllib.request.urlopen(URL, timeout=30) as r:
                raw = r.read()
        except OSError as e:
            sys.exit(f'cannot download {URL}: {e}\nDownload that file by hand into {CACHE} (or pass --data <file>), '
                     'then run this again.')
        if hashlib.sha256(raw).hexdigest() != SHA256:
            sys.exit(f'the download from {URL} is not the pinned file (SHA256 differs): nothing written')
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE.with_suffix('.part')
        tmp.write_bytes(raw)
        os.replace(tmp, CACHE)  # written whole, then renamed: a killed run leaves no half file
    raw = CACHE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA256:
        sys.exit(f'{CACHE} is not the pinned file (SHA256 differs): delete it to download it again')
    return check(json.loads(raw.decode('utf-8')), str(CACHE))


def describe(c, sat):
    h, s, _ = colorsys.rgb_to_hsv(*(v / 255 for v in c['rgb']))
    L, a, b = c['lab']
    h, chroma = h * 360, math.hypot(a, b)
    tags = [t for t, ok in (('warm', s >= sat and (h < 70 or h >= 330)),
                            ('cool', s >= sat and 90 <= h < 300),
                            ('earth', s >= sat and 5 <= h <= 48 and 25 <= L <= 75),
                            ('dark', L < 30),
                            ('neutral', s < sat)) if ok]
    return {'name': c['name'], 'hex': c['hex'], 'rgb': c['rgb'], 'h': h, 's': s, 'L': L, 'C': chroma, 'tags': tags}


def combinations(colours, sat):
    out = {}
    for c in colours:  # the dataset's own order, which is the book's
        for n in c['combinations']:
            out.setdefault(n, []).append(describe(c, sat))
    return out


def comment(n, cs):
    return f'// Wada {n}: ' + ', '.join(f"{c['name']} {c['hex']}" for c in cs)


def in_range(h, lo, hi):
    return lo <= h <= hi if lo <= hi else h >= lo or h <= hi


def numbers(text):
    try:
        return [int(x) for x in text.split(',') if x.strip()]
    except ValueError:
        raise argparse.ArgumentTypeError(f'want numbers separated by commas, got {text!r}')


def hue_range(text):
    try:
        lo, hi = (float(x) for x in text.split('-'))
    except ValueError:
        raise argparse.ArgumentTypeError(f'want LO-HI in degrees (for example 15-60, or 330-20), got {text!r}')
    if not (0 <= lo <= 360 and 0 <= hi <= 360):
        raise argparse.ArgumentTypeError(f'hues run 0-360, got {text!r}')
    return lo, hi


def main():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--data', help='read this colors.json instead of the cached download')
    common.add_argument('--sat', type=float, default=0.25, help='HSV saturation under which a colour is a neutral (0.25)')
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    sh = sub.add_parser('show', parents=[common], help='the colours of one or more combinations')
    sh.add_argument('n', type=int, nargs='+', help='combination numbers, 1-348')
    fd = sub.add_parser('find', parents=[common], help='filter the 348 combinations')
    fd.add_argument('--count', type=numbers, help='2, 3 or 4 colours; several as 3,4')
    fd.add_argument('--hue', type=hue_range, action='append', default=[],
                    help='at least one colour with its hue in LO-HI degrees (330-20 wraps); repeat for another colour')
    fd.add_argument('--warm', type=int, default=0, help='at least N warm colours (hue under 70 or from 330)')
    fd.add_argument('--cool', type=int, default=0, help='at least N cool colours (hue 90 to 300)')
    fd.add_argument('--earth', type=int, default=0, help='at least N earth colours (hue 5-48, Lab L 25-75)')
    fd.add_argument('--dark', type=int, default=0, help='at least N dark colours (Lab L under 30), neutrals included')
    fd.add_argument('--no-cool', action='store_true', help='no cool colour at all')
    fd.add_argument('--used', type=numbers, default=[], help='leave out these combinations (the film already uses them)')
    fd.add_argument('--limit', type=int, default=20, help='print at most this many (20)')
    a = p.parse_args()

    combos = combinations(load(a.data), a.sat)
    if a.cmd == 'show':
        bad = [n for n in a.n if n not in combos]
        if bad:
            p.error(f'no combination {bad}: they are numbered 1-348')
        for n in a.n:
            cs = combos[n]
            print(f'Wada {n} ({len(cs)} colours)')
            for c in cs:
                print(f"  {c['name']:<22} {c['hex']}  rgb {','.join(map(str, c['rgb'])):<11}  h {c['h']:3.0f}  "
                      f"s {c['s']:.2f}  L {c['L']:3.0f}  C {c['C']:3.0f}  {' '.join(c['tags'])}")
            print('  ' + comment(n, cs))
        return

    def passes(n, cs):
        count = lambda tag: sum(tag in c['tags'] for c in cs)  # noqa: E731
        return (n not in a.used and (not a.count or len(cs) in a.count)
                and all(any(in_range(c['h'], lo, hi) and 'neutral' not in c['tags'] for c in cs) for lo, hi in a.hue)
                and count('warm') >= a.warm and count('cool') >= a.cool and count('earth') >= a.earth
                and count('dark') >= a.dark and not (a.no_cool and count('cool')))

    hits = sorted((n for n, cs in combos.items() if passes(n, cs)),
                  key=lambda n: (-round(sum(c['C'] for c in combos[n]) / len(combos[n]), 6), n))
    print(f'{len(hits)} of {len(combos)} combinations pass' + (f'; the {min(a.limit, len(hits))} most chromatic:'
                                                                 if hits else ''))
    for n in hits[:a.limit]:
        cs = combos[n]
        print(f"{n:>4}  " + ', '.join(f"{c['name']} {c['hex']}" for c in cs)
              + f"   (chroma {sum(c['C'] for c in cs) / len(cs):.0f}, L {min(c['L'] for c in cs):.0f}-{max(c['L'] for c in cs):.0f})")


if __name__ == '__main__':
    main()
