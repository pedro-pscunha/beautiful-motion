#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "soundfile", "scipy"]
# ///
"""Is the voice clear on every line? The speech band (300 Hz-8 kHz, mono) of the voice against everything else, per
line and over 200 ms windows, in dB.
usage: uv run <skill>/scripts/voice_margin.py <voice.wav> <rest.wav> <lines.json> [--min 8]
       uv run <skill>/scripts/voice_margin.py <voice.wav> --mix <mix.wav> <lines.json> [--min 8]
voice.wav: the voice alone at its level in the mix; rest.wav: everything else (music, effects) at its level. --mix
takes rest = mix - voice: valid only when voice.wav went through the same master chain as mix.wav, sample-aligned
(otherwise voice is left in the rest and the margins read low).
lines.json: [{"text": "...", "start": 1.20, "end": 3.45}, ...], seconds on the film's clock.
A line the audio does not reach (a mix cut short) is LOW too.
Per line: whole (over the line's span) and worst (the weakest 200 ms window where the voice is within 12 dB of its
loudest window, so pauses do not count). A line is LOW when whole is under --min (exit 1); a worst window under --min
is flagged "weak": a word the music or effects may mask there (duck or thin the bed at that time)."""
import json
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

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


mix, floor = opt('mix'), float(opt('min', '8'))
if len(a) != (2 if mix else 3):
    sys.exit(__doc__)
voice_p, other_p, lines_p = (a[0], mix, a[1]) if mix else a
v, sr = sf.read(voice_p, always_2d=True)
o, sr2 = sf.read(other_p, always_2d=True)
if sr != sr2:
    sys.exit(f'{voice_p} is {sr} Hz and {other_p} is {sr2} Hz: render both at the same rate')
n = min(len(v), len(o))
clipped = int((np.abs(o[:n]) >= 0.9999).sum())
if clipped:
    print(f'warning: {clipped} samples of {other_p} sit at full scale: it is probably clipped (write mixes as 32-bit '
          'float, pcm_f32le)')
v, o = v[:n].mean(axis=1), o[:n].mean(axis=1)
if mix:
    gain = float(np.dot(o, v) / max(np.dot(v, v), 1e-12))  # the voice's level in the mix; the rest is uncorrelated
    if abs(gain - 1) > 0.05:
        print(f'warning: the voice sits in {mix} at gain {gain:.2f}, not 1.00, so mix - voice still holds voice and '
              'these margins read wrong: measure with the voice exactly as mixed (same level, a stereo copy via pan), '
              'or pass the rest as its own file')
    o = o - v
band = butter(4, [300, min(8000, 0.45 * sr)], btype='band', fs=sr, output='sos')
bv, bo = sosfilt(band, v), sosfilt(band, o)


def db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


w, low = int(0.2 * sr), 0
for k, ln in enumerate(json.load(open(lines_p, encoding='utf-8'))):
    s, e = int(ln['start'] * sr), int(ln['end'] * sr)
    if e > n:  # a line the audio does not reach to its end is a failure: the mix was cut short (check its -t)
        low += 1
        print(f"{k + 1:>3}  {ln['start']:7.2f}-{ln['end']:7.2f} s  LOW  the audio ends at {n / sr:.2f} s, before this line"
              f" does  {ln.get('text', '')[:48]}")
        continue
    if e - s < w:
        print(f"{k + 1:>3}  {ln['start']:7.2f}-{ln['end']:7.2f} s  under 200 ms: not measured  {ln.get('text', '')[:48]}")
        continue
    whole = db(bv[s:e]) - db(bo[s:e])
    wins = [(i, db(bv[i:i + w]), db(bo[i:i + w])) for i in range(s, e - w + 1, w)]
    top = max(x[1] for x in wins)
    at, wv, wo = min((x for x in wins if x[1] >= top - 12), key=lambda x: x[1] - x[2])
    ok, weak = whole >= floor, wv - wo < floor
    low += not ok
    print(f"{k + 1:>3}  {ln['start']:7.2f}-{ln['end']:7.2f} s  whole {whole:5.1f} dB  worst {wv - wo:5.1f} dB at "
          f"{at / sr:7.2f} s  {'OK ' if ok else 'LOW'}{' weak' if weak else '     '}  {ln.get('text', '')[:48]}")
print(f'{low} line(s) under {floor:g} dB' if low else f'every line at {floor:g} dB or more')
sys.exit(1 if low else 0)
