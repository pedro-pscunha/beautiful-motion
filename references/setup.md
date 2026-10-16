# Setup: the tools, on macOS, Windows and Linux, with the user

Install uv first (it brings Python), then run the doctor with the project folder as the working directory:
`uv run <skill>/scripts/doctor.py`. It prints what is present, what is missing, and the command for this machine.
Install what you can yourself; hand the user anything that needs a password, a UAC prompt, a GUI installer, a sign-in
or a licence, and wait for them to say it is done. Re-run the doctor after.

If your shell is sandboxed (no network, no writes outside the project), the installs, the Chromium download, the
first `uv run` of each script and every provider call need network access: ask the user to allow them or to run them.

## Required

| Tool | Why | macOS | Windows | Linux |
|---|---|---|---|---|
| uv | runs the Python scripts with their libraries; downloads a Python if there is none | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `winget install -e --id astral-sh.uv` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js 20.6+ | runs the browser renderer (Playwright needs 20+; `--env-file` needs 20.6) | `brew install node` | `winget install -e --id OpenJS.NodeJS.LTS` (UAC prompt) | nvm: `nvm install --lts`; Fedora `sudo dnf install nodejs`; Arch `sudo pacman -S nodejs npm` |
| ffmpeg (with libx264) | encode, mux, measure loudness | `brew install ffmpeg` | `winget install -e --id Gyan.FFmpeg` | Debian/Ubuntu `sudo apt install ffmpeg`; Fedora: RPM Fusion, then `sudo dnf swap ffmpeg-free ffmpeg --allowerasing`; Arch `sudo pacman -S ffmpeg` |
| Playwright + Chromium | renders the page frame by frame | in the project, three commands: `npm init -y` (only without a package.json), `npm i -D playwright`, `npx playwright install chromium` | the same with `npm.cmd` / `npx.cmd` | the same; on Debian/Ubuntu, if Chromium does not launch, the user runs `sudo env "PATH=$PATH" npx playwright install-deps chromium` |

Notes:
- macOS without Homebrew: the user installs it (`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`,
  it asks for their password). On Apple Silicon, `brew` is then not on PATH in the current shell until
  `eval "$(/opt/homebrew/bin/brew shellenv)"`.
- After the uv installer, open a new terminal or run `source $HOME/.local/bin/env` (macOS, Linux).
- apt's `nodejs` is too old on most Debian and Ubuntu releases (12 on Ubuntu 22.04, 18 on 24.04 and Debian 12). Use
  nvm (https://github.com/nvm-sh/nvm), fnm or NodeSource, and check `node --version` says 20.6 or more.
- Fedora's default `ffmpeg-free` has no libx264, so the encode fails with "Unknown encoder 'libx264'"; the doctor
  checks for it.
- `install-deps` uses `sudo apt-get`, whose password prompt an agent cannot answer, and supports only Debian and
  Ubuntu. On other distributions, install the libraries Chromium's error lists. With Node from nvm, `sudo` does not
  see `npx`: the user runs `sudo env "PATH=$PATH" npx playwright install-deps chromium`.
- nvm puts `node` on PATH only in shells that load it: in an agent's non-interactive shell run
  `. "$NVM_DIR/nvm.sh"` (or `export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"`) before `node` and `npx`.
- Windows:
  - Add `--accept-source-agreements --accept-package-agreements` to every winget call an agent runs, or the first
    run waits for a Y/N. Node, Python and Blender bring up a UAC prompt: tell the user before.
  - Open a new terminal after a winget install, so PATH refreshes. If `winget` is missing, the user installs "App
    Installer" from the Microsoft Store.
  - Windows PowerShell 5.1 (the default) has no `&&`: run one command per line.
  - `npm` and `npx` resolve to `npm.ps1` / `npx.ps1`, which the default execution policy blocks ("running scripts is
    disabled on this system"). Call `npm.cmd` and `npx.cmd`, or ask the user to run
    `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- Playwright goes into the project, not globally: `render_frames.mjs` and the doctor resolve it from the working
  directory. In a folder that is already a JS project, `npm i -D playwright` adds it to their `package.json` and
  lockfile: say so first. Chromium is a download of about 150-300 MB into a per-user cache, once per machine.
- Without uv: Python 3.10+ (`brew install python`, `winget install -e --id Python.Python.3.13`,
  `sudo apt install python3 python3-venv`), then `python -m pip install pillow numpy soundfile scipy` in a venv, and
  run the scripts with `python3` (Windows `py`) instead of `uv run`.

## Optional, when the brief needs it

| Tool | When | Install |
|---|---|---|
| Blender 5.x | real 3D: path-traced objects, a camera move through a set | macOS `brew install --cask blender`; Windows `winget install -e --id BlenderFoundation.Blender`; Linux `sudo snap install blender --classic`, `flatpak install flathub org.blender.Blender`, or the tarball from blender.org |
| Fonts | type in the film | download from Google Fonts or the foundry, keep the file in the project, and load it in the page with `@font-face` (the render then does not depend on the machine) |
| A DAW or audio editor | the user wants to fine-tune the mix by hand | their choice (Reaper, Audacity, Logic); hand over stems as WAV |

Blender is not on PATH after install on macOS (`/Applications/Blender.app/Contents/MacOS/Blender`) or Windows
(`C:\Program Files\Blender Foundation\Blender 5.x\blender.exe`). Render a PNG sequence at the film's size and fps,
headless, numbered from 0 like the page's frames: `blender -b scene.blend -o //render/f#### -F PNG -s 0 -e <last frame> -a`. Then draw those frames in the page as a plate by frame
index (`craft.md`, "Plates").

## Verify

The doctor shows every required tool as OK. Then render the starter (copy it only if `picture/` does not exist yet):

```
cp -r <skill>/assets/starter picture
node <skill>/scripts/render_frames.mjs picture/index.html --still 1.5,4.5 .work/check.png
```

Look at the image: a chalk sun on a dark slate, and an orange sun on paper. If the render fails, read the errors it
prints: a file that did not load, a font that did not load, or a page error with its message.
