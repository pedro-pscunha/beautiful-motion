#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "soundfile"]
# ///
"""RMS level over time, in dBFS, for one or more audio files side by side: where the music sits, where it ducks under
the voice, and whether the mix drops out before the end (a mix that falls far below its own music file in the last
seconds lost the music there).
usage: uv run <skill>/scripts/levels.py <file> [<file> ...] [--every 1.0] [--from 0] [--to <seconds>]"""
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

a = sys.argv[1:]
opts = {'every': 1.0, 'from': 0.0, 'to': None}
for name in list(opts):
    if f'--{name}' in a:
        i = a.index(f'--{name}')
        if i + 1 >= len(a):
            sys.exit(__doc__)
        opts[name] = float(a[i + 1])
        del a[i:i + 2]
if not a or opts['every'] <= 0:
    sys.exit(__doc__)
tracks = []
for f in a:
    x, sr = sf.read(f, always_2d=True, dtype='float32')
    tracks.append((Path(f).name, x.mean(axis=1), sr))
end = opts['to'] or max(len(x) / sr for _, x, sr in tracks)
print('    time  ' + ''.join(f'{name[:14]:>16}' for name, _, _ in tracks))
t = opts['from']
while t < end - 1e-9:
    row = []
    for _, x, sr in tracks:
        seg = x[int(t * sr):int(min(t + opts['every'], end) * sr)]
        row.append(f'{20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-12):16.1f}' if len(seg) else f'{"(ended)":>16}')
    print(f'{t:8.2f}  ' + ''.join(row))
    t += opts['every']
