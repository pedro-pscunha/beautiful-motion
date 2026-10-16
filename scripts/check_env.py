#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Which keys are set, from <project>/.env and the environment. Prints set / missing per variable, never a value.
Exits 1 if any asked variable is missing. Reads .env the way python-dotenv and node --env-file do: `export`, quotes,
comments (a # after a space ends an unquoted value), the last duplicate wins.
usage: uv run <skill>/scripts/check_env.py VAR [VAR ...] [--env path/to/.env]   (default: .env in the working directory)"""
import os
import re
import sys
from pathlib import Path

args = sys.argv[1:]
path = Path('.env')
if '--env' in args:
    i = args.index('--env')
    if i + 1 >= len(args):
        sys.exit(__doc__)
    path = Path(args[i + 1])
    del args[i:i + 2]
if not args:
    sys.exit(__doc__)

found = {}
if path.exists():
    raw = path.read_bytes()
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
        sys.exit(f'{path} is saved as UTF-16 (PowerShell 5.1 ">" and Out-File do this): open it in Notepad or VS Code, '
                 'save it as UTF-8, then run this again')
    for line in raw.decode('utf-8-sig', errors='replace').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        k, v = k.removeprefix('export ').strip(), v.strip()
        if v[:1] in ('"', "'") and v[0] in v[1:]:
            v = v[1:v.index(v[0], 1)]
        else:
            v = re.split(r'(?:^|\s)#', v, maxsplit=1)[0].strip()
        found[k] = v
missing = []
for var in args:
    where = path.name if found.get(var) else 'environment' if os.environ.get(var) else ''
    if where:
        print(f'set      {var} (from {where})')
    else:
        print(f'missing  {var}')
        missing.append(var)
if not path.exists():
    print(f'(no {path} here: copy the skill\'s assets/env.example to {path} and fill only the lines you need)')
sys.exit(1 if missing else 0)
