#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Loudness of a delivered file or a mix, measured with ffmpeg: integrated loudness, loudness range, true peak. Reads
any file ffmpeg reads (mp4, wav, mp3) and needs no shell pipe, so it runs the same in bash and PowerShell.
usage: uv run <skill>/scripts/loudness.py <file> [--target -14] [--tp -1]
       uv run <skill>/scripts/loudness.py <mix.wav> --normalize <out.wav> [--target -14] [--tp -1.5]
--normalize: two-pass loudnorm to the target, as a plain gain (linear) when the true peak allows it, else dynamic; it
says which. Aim at -1.5 dBTP before an AAC encode, which adds a little peak. Exit 1 if the measured file is more than
0.5 LU off the target or its true peak is over --tp."""
import json
import re
import subprocess
import sys

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


dst = opt('normalize')
target = float(opt('target', '-14'))
tp = float(opt('tp', '-1.5' if dst else '-1'))
if len(a) != 1:
    sys.exit(__doc__)


def ffmpeg(args):
    try:
        r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', *args], capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
    except OSError as e:
        sys.exit(f'ffmpeg did not run: {e}')
    if r.returncode:
        sys.exit(r.stderr[-1500:])
    return r.stderr


def measure(f):
    err = ffmpeg(['-i', f, '-map', '0:a:0', '-af', 'ebur128=peak=true', '-f', 'null', '-'])
    s = err[err.rindex('Summary:'):]
    get = lambda pat: float(re.search(pat, s).group(1))  # noqa: E731
    return get(r'I:\s+(-?[\d.]+|-inf) LUFS'), get(r'LRA:\s+([\d.]+) LU'), get(r'Peak:\s+(-?[\d.]+|-inf) dBFS')


def last_json(err):
    return json.loads(err[err.rindex('{'):err.rindex('}') + 1])


src = a[0]
src_i, src_lra, src_peak = measure(src)
if src_peak >= -0.1:
    print(f'warning: {src} peaks at {src_peak:.1f} dBTP, at or over full scale. A 16- or 24-bit file (or an mp3) is '
          'clipped there: render the mix as 32-bit float (-c:a pcm_f32le) and run this again.')
if dst:
    base = f'loudnorm=I={target}:TP={tp}:LRA=20'
    m = last_json(ffmpeg(['-i', src, '-af', base + ':print_format=json', '-f', 'null', '-']))
    second = (f"{base}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
              f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true:print_format=json")
    kind = last_json(ffmpeg(['-y', '-i', src, '-af', second, '-ar', '48000', '-c:a', 'pcm_s24le', dst]))['normalization_type']
    print(f'{dst}: normalized ({kind}' + (')' if kind == 'linear' else
          ': loudnorm compressed it; for a plain gain, tame the mix peaks first, then run this again)'))
i, lra, peak = measure(dst) if dst else (src_i, src_lra, src_peak)
good = abs(i - target) <= 0.5 and peak <= tp
print(f'{dst or src}: {i:.1f} LUFS integrated, LRA {lra:.1f} LU, true peak {peak:.1f} dBTP   '
      f"{'OK' if good else 'OFF'} (target {target:g} LUFS, peak at most {tp:g} dBTP)")
sys.exit(0 if good else 1)
