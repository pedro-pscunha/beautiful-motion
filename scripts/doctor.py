#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check the tools beautiful-motion needs and print, for this machine, the command that installs each missing one.
Installs nothing itself. Run it with the project folder as the working directory (Playwright is a project dependency):
    uv run <skill>/scripts/doctor.py        (without uv: python3, or py on Windows)
Exit 1 if a required tool is missing."""
import platform
import re
import shutil
import subprocess
import sys

for stream in (sys.stdout, sys.stderr):
    stream.reconfigure(errors='replace')


def linux_family():
    for tool, fam in (('apt-get', 'apt'), ('dnf', 'dnf'), ('pacman', 'pacman')):
        if shutil.which(tool):
            return fam
    return 'linux'


OS = {'Darwin': 'mac', 'Windows': 'win'}.get(platform.system()) or linux_family()
W = ' --accept-source-agreements --accept-package-agreements'
CURL_UV = 'curl -LsSf https://astral.sh/uv/install.sh | sh   (then open a new terminal, or: source $HOME/.local/bin/env)'
NVM = 'nvm (https://github.com/nvm-sh/nvm), then: nvm install --lts'
INSTALL = {
    'brew': {'mac': '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
                    '   (the user runs it: it asks for their password)\n'
                    'eval "$(/opt/homebrew/bin/brew shellenv)"   (Apple Silicon: puts brew on PATH in this shell)'},
    'node': {'mac': 'brew install node', 'win': 'winget install -e --id OpenJS.NodeJS.LTS' + W + '   (a UAC prompt)',
             'apt': NVM + '   (apt has Node 18 or older on most releases)',
             'dnf': 'sudo dnf install nodejs   (then check node --version is 20+, else ' + NVM + ')',
             'pacman': 'sudo pacman -S nodejs npm', 'linux': NVM},
    'uv': {'mac': CURL_UV, 'win': 'winget install -e --id astral-sh.uv' + W + '   (then open a new terminal)',
           'apt': CURL_UV, 'dnf': CURL_UV, 'pacman': CURL_UV, 'linux': CURL_UV},
    'ffmpeg': {'mac': 'brew install ffmpeg', 'win': 'winget install -e --id Gyan.FFmpeg' + W + '   (then open a new terminal)',
               'apt': 'sudo apt install ffmpeg',
               'dnf': "Fedora's ffmpeg-free has no libx264: enable RPM Fusion (https://rpmfusion.org), then\n"
                      'sudo dnf swap ffmpeg-free ffmpeg --allowerasing',
               'pacman': 'sudo pacman -S ffmpeg', 'linux': 'a static build from https://ffmpeg.org/download.html'},
    'playwright': {k: ('npm.cmd init -y   (only if this folder has no package.json)\nnpm.cmd i -D playwright\n'
                       'npx.cmd playwright install chromium' if k == 'win' else
                       'npm init -y   (only if this folder has no package.json)\nnpm i -D playwright\n'
                       'npx playwright install chromium'
                       + ('\nsudo env "PATH=$PATH" npx playwright install-deps chromium   (the user runs it, if Chromium still does not launch)'
                          if k == 'apt' else ''))
                   for k in ('mac', 'win', 'apt', 'dnf', 'pacman', 'linux')},
}


def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=90)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:  # a missing, broken or hanging tool is a finding, not a crash
        return 1, str(e)


def report(name, ok, detail, key=None):
    print(f"{'OK     ' if ok else 'MISSING'}  {name:<24} {detail}")
    if not ok and key:
        for line in INSTALL[key][OS].splitlines():
            print(f'         install: {line}')
    return ok


ok = True
if OS == 'mac':
    report('Homebrew (recommended)', bool(shutil.which('brew')), shutil.which('brew') or 'not on PATH', 'brew')
code, out = run(['node', '--version']) if shutil.which('node') else (1, 'not on PATH')
ver = re.match(r'v(\d+)\.(\d+)', out) if code == 0 else None
node_ok = bool(ver) and (int(ver[1]), int(ver[2])) >= (20, 6)
ok &= report('Node.js 20.6+', node_ok, out, 'node')
ok &= report('Python 3.10+', sys.version_info >= (3, 10), platform.python_version())
has_uv = bool(shutil.which('uv'))
report('uv (recommended)', has_uv, shutil.which('uv') or 'not on PATH', 'uv')
code, out = run(['ffmpeg', '-hide_banner', '-encoders']) if shutil.which('ffmpeg') else (1, 'not on PATH')
ok &= report('ffmpeg with libx264', code == 0 and 'libx264' in out,
             'present' if code == 0 and 'libx264' in out else 'this ffmpeg has no libx264' if code == 0 else out, 'ffmpeg')
if code == 0 and 'prores_ks' not in out:
    print('         note: no prores_ks encoder: no ProRes master (the H.264 delivery still works)')
code, out = run(['ffprobe', '-version']) if shutil.which('ffprobe') else (1, 'not on PATH')
ok &= report('ffprobe', code == 0, out.splitlines()[0][:60] if code == 0 else out, 'ffmpeg')
if not node_ok:
    ok &= report('Playwright + Chromium', False, 'not checked: install Node 20.6+ first, then', 'playwright')
else:
    probe = ("const {chromium}=require(require.resolve('playwright',{paths:[process.cwd()]}));"
             "chromium.launch().then(b=>b.close()).then(()=>console.log('chromium launches'))")
    code, out = run(['node', '-e', probe])
    why = [ln.strip() for ln in out.splitlines() if re.search(r'Error|Executable|missing dependencies|Cannot find', ln)]
    ok &= report('Playwright + Chromium', code == 0, 'chromium launches' if code == 0 else (why[0] if why else out)[:110],
                 'playwright')
try:
    import numpy  # noqa: F401
    import PIL  # noqa: F401
    report('Pillow + numpy', True, 'importable')
except ImportError:
    ok &= report('Pillow + numpy', has_uv, 'uv run installs them per script' if has_uv
                 else 'not importable and no uv: install uv, or  python -m pip install pillow numpy', 'uv')
print('\nAll required tools present.' if ok else
      '\nSome required tools are missing: install them (ask the user for anything with a password, UAC or GUI prompt),'
      ' then run this again.')
sys.exit(0 if ok else 1)
