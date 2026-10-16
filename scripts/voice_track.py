#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "soundfile", "scipy"]
# ///
"""Lay the voice lines onto one track from lines.json, so each line's timing lives in one place.
usage: uv run <skill>/scripts/voice_track.py <lines.json> <voice.wav> [--length <seconds>]
lines.json: [{"text": "...", "file": "audio/lines/01.wav", "start": 2.05, "end": 3.13}, ...] (seconds on the film's
clock; file paths relative to the working directory). Each line is folded to mono (a stereo file: the mean of its
channels, or one channel with "channel": 0 or 1 in its entry), resampled to 48 kHz, placed at its start, and written
as a stereo 32-bit float WAV with the same signal in both channels at full level (what voice_margin.py --mix expects).
It warns when a line overlaps the next or runs past its "end", and prints the end of any line that has none."""
import json
import sys
from math import gcd

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

SR = 48000
a = sys.argv[1:]
length = None
if '--length' in a:
    i = a.index('--length')
    if i + 1 >= len(a):
        sys.exit(__doc__)
    length = float(a[i + 1])
    del a[i:i + 2]
if len(a) != 2:
    sys.exit(__doc__)
placed = []
for k, ln in enumerate(json.load(open(a[0], encoding='utf-8')), 1):
    if 'file' not in ln or 'start' not in ln:
        sys.exit(f'line {k}: every entry needs "file" and "start"')
    x, sr = sf.read(ln['file'], always_2d=True, dtype='float32')
    if 'channel' in ln and not 0 <= ln['channel'] < x.shape[1]:
        sys.exit(f'line {k}: "channel": {ln["channel"]}, but {ln["file"]} has {x.shape[1]} channel(s) (0 is the first)')
    x = x[:, ln['channel']] if 'channel' in ln else x.mean(axis=1)
    if sr != SR:
        g = gcd(SR, sr)
        x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    s = int(round(ln['start'] * SR))
    placed.append((k, s, s + len(x), x))
    ends = (s + len(x)) / SR
    if 'end' not in ln:
        print(f'line {k}: the audio ends at {ends:.2f} s: add "end": {ends:.2f} to its entry')
    elif ends > ln['end'] + 0.01:
        print(f'warning: line {k} runs to {ends:.2f} s, past its "end" ({ln["end"]:.2f} s)')
if not placed:
    sys.exit(f'{a[0]} has no lines')
by_start = sorted(placed, key=lambda p: p[1])
for (k, _, e, _), (k2, s2, _, _) in zip(by_start, by_start[1:]):
    if s2 < e:
        print(f'warning: line {k2} starts {(e - s2) / SR:.2f} s before line {k} ends')
n = int(round(length * SR)) if length else max(e for _, _, e, _ in placed) + SR // 2
out = np.zeros(n, np.float32)
for _, s, e, x in placed:
    m = max(0, min(e, n) - s)
    out[s:s + m] += x[:m]
sf.write(a[1], np.stack([out, out], axis=1), SR, subtype='FLOAT')
print(f'{a[1]}: {len(placed)} lines, {n / SR:.2f} s, stereo 48 kHz 32-bit float')
