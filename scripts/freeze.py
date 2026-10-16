#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Freeze a grading candidate: SHA256SUMS over every file under it (symlinked files and folders followed), then its
own files and folders read-only. Graders check it before and after grading. A frozen folder is never rebuilt: a fix is
a new letter (cand3b). Files reached through a symlink are hashed, not locked: --check still catches a change.
usage: uv run <skill>/scripts/freeze.py <dir>            freeze it
       uv run <skill>/scripts/freeze.py --check <dir>    every file unchanged, none added or missing (exit 1 if not)
       uv run <skill>/scripts/freeze.py --sums <dir>     (re)write <dir>/SHA256SUMS for a delivery, lock nothing
To delete a frozen folder later, unlock it first: chmod -R u+w <dir> (macOS, Linux); on Windows two commands,
attrib -R <dir> and attrib -R <dir>\\* /S /D."""
import hashlib
import os
import stat
import sys
from pathlib import Path

for stream in (sys.stdout, sys.stderr):
    stream.reconfigure(errors='replace')
args = sys.argv[1:]
mode = next((m for m in ('--check', '--sums') if m in args), None)
args = [x for x in args if x != mode]
if len(args) != 1 or not Path(args[0]).is_dir():
    sys.exit(__doc__)
root = Path(args[0]).resolve()
sums = root / 'SHA256SUMS'


def digest(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def files():
    out = {}
    for d, dirs, names in os.walk(root, followlinks=True):
        dirs.sort()
        for n in names:
            p = Path(d) / n
            if p.is_file() and p != sums:
                out[Path(os.path.relpath(p, root)).as_posix()] = p
    return dict(sorted(out.items()))


if mode == '--sums':
    text = ''.join(f'{digest(p)}  {name}\n' for name, p in files().items())
    sums.write_text(text, encoding='utf-8')
    print(text + f'wrote {sums}', end='\n')
elif mode == '--check':
    if not sums.exists():
        sys.exit(f'{root} is not frozen (no SHA256SUMS)')
    want = dict(reversed(line.split('  ', 1)) for line in sums.read_text(encoding='utf-8').splitlines() if line)
    have = files()
    bad = {'CHANGED': [n for n in want if n in have and digest(have[n]) != want[n]],
           'MISSING': [n for n in want if n not in have], 'ADDED': [n for n in have if n not in want]}
    if not any(bad.values()):
        print(f'{root}: all {len(want)} files OK')
    for kind, names in bad.items():
        if names:
            print(f'{root}: {len(names)} {kind}: ' + ', '.join(names))
    sys.exit(1 if any(bad.values()) else 0)
else:
    if sums.exists():
        sys.exit(f'{root} is already frozen: make a new letter')
    fs = files()
    sums.write_text(''.join(f'{digest(p)}  {name}\n' for name, p in fs.items()), encoding='utf-8')
    ro = stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH
    own = [p for p in list(fs.values()) + [sums] if not p.is_symlink() and p.resolve().is_relative_to(root)]
    for p in own:
        os.chmod(p, ro)
    for d, dirs, _ in os.walk(root, topdown=False):  # folders after their files, the root last
        if not Path(d).is_symlink():
            os.chmod(d, ro | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f'froze {root}: {len(fs)} files ({len(fs) - len(own) + 1} through links: hashed, not locked)')
