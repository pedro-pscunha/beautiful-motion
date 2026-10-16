---
name: beautiful-motion
description: Make, fix or grade short motion films that look hand-made and professionally finished - an animated film, a motion piece, an explainer, a social reel (9:16), a title or end card, an animated poem, a catalogue of styles. Use it whenever someone wants a film animated, made "more beautiful / less AI-looking", re-rendered, de-flickered, re-mixed, critiqued or graded, even if they never say "motion". The picture and its motion are drawn in code (an HTML canvas exported frame by frame with Playwright), with the resources the user picks at the start - optional generated images (Higgsfield or another provider), voiceover, music (ElevenLabs, Higgsfield, Suno or their own) and sparse foley - then finished with ffmpeg to delivery specs and raised by subagent reviews or a grading panel.
---

# beautiful-motion

A method for making short films (10 s to 3 min) that read as made by hand and finished by a studio, with an agent
that writes code, measures what it makes, and uses other agents as critics.

The core idea: draw the picture and its motion in code (deterministic, re-renderable, editable to the pixel), take a
generated image only where code cannot do it, measure everything (you cannot see motion in a still, and you cannot hear), and let
critics with one lens each push the quality up in rounds.

## Conventions

- `<skill>` is this skill's folder; `<project>` is the film's folder. Run every command with `<project>` as the
  working directory.
- Scratch goes in `<project>/.work/` (renders, logs, grading rounds), one folder per version (`.work/v1/`); what the
  user receives goes in `<project>/out/`. Add `.work/`, `.env` and `node_modules/` to `.gitignore`. Never keep state in
  a system temp folder: a reboot can wipe it.
- Python scripts run as `uv run <skill>/scripts/<name>.py ...`: uv brings Python and each script's libraries (they are
  declared inside the script). Without uv: `python3` (Windows: `py`) and `pip install pillow numpy soundfile scipy`.
- Commands here are written for bash/zsh. In Windows PowerShell 5.1 there is no `&&` (one command per line),
  `cp -r` works as is, and `npm`/`npx` may need to be `npm.cmd`/`npx.cmd` (`references/setup.md`).

## Keys stay out of the transcript

- Never ask for keys up front. When a step needs a provider, ask the user to fill the one line in `<project>/.env`
  themselves, never in the chat. Create `.env` from `<skill>/assets/env.example` only if it does not exist yet: a
  second copy wipes their keys.
- Never open, print, cat, grep or read `.env` or a key variable, and never put a key literal in a command. Check with
  `uv run <skill>/scripts/check_env.py VAR [VAR ...]` (set / missing, never a value). Load keys only at run time:
  `uv run --env-file .env <script>.py` or `node --env-file=.env <script>.mjs`.
- Critics and graders never read `.env`.
- Before the first paid call, say what it costs and get the user's OK and a spending cap.

Which variable for which provider, and the no-key paths: `references/env.md`.

## Your first film (the shortest path)

```
uv run <skill>/scripts/doctor.py                     # 1. tools: install what it lists, then run it again
cp -r <skill>/assets/starter picture                 # 2. the starter page (only if picture/ does not exist yet)
node <skill>/scripts/render_frames.mjs picture/index.html --still 1,4 .work/v1/stills.png    # 3. look at stills
node <skill>/scripts/render_frames.mjs picture/index.html .work/v1/frames                    # 4. every frame
ffmpeg -framerate 24 -i .work/v1/frames/f%04d.png -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709" -c:v libx264 -preset slow -crf 16 -colorspace bt709 -color_primaries bt709 -color_trc bt709 -movflags +faststart .work/v1/picture.mp4     # 5. encode
ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=nb_read_frames:format=duration -of default=nw=1 .work/v1/picture.mp4     # 6. verify
```

Line 5 encodes (its `-framerate` is the page's `TIMELINE.fps`); line 6 must report the page's frame count and
duration (the starter: 144 frames, 6 s). A silent film is then done: copy it to `out/<name>-v1.mp4`. With sound, mix
and mux it (`references/sound.md`, `references/finish.md`).

## Step 0: setup, with the user

Run the doctor. It checks Node 20.6+, Python, uv, ffmpeg (with libx264), Playwright and Chromium, and prints the install
command for this OS for anything missing. Run the safe ones yourself; hand the user the ones that need a password, a
UAC prompt, a GUI installer or a licence, and wait for "done". If your shell is sandboxed, installs and downloads need
network access: ask the user to allow them. Per OS: `references/setup.md`.

## Step 1: the brief and the resources

Ask only what changes the work: length and format (16:9, 1:1, 9:16), where it will be seen (phone, screen, festival),
the subject and the tone, words (a voiceover? on-screen text?), references they love and hate.

Then, before starting, ask which resources they want to use, one answer per line ("none" is an answer):
- **Music**: their own or a licensed track; a royalty-free library (Pixabay Music, the YouTube Audio Library, Freesound
  CC0); generated with ElevenLabs Music (v2: a whole piece built section by section, and one section regenerated
  without touching the rest), Higgsfield (Seed Audio, in the Higgsfield app or its MCP), or Suno (made by the user in
  Suno's app: no public API); a score written in code (MIDI through an instrument they have); or silence.
- **Voiceover**: ElevenLabs, Higgsfield (its Eleven voices), their own recording, or none.
- **Sound effects**: ElevenLabs sound generation, Freesound, their own recordings, or none.
- **Generated images** (a paper texture, a painted backdrop): Higgsfield, OpenAI, Google, fal, Replicate; or everything
  drawn in code (the default).

Do not offer generated video: the motion is drawn in code, and that is the method. Say which key each choice will need
(`references/env.md`), but ask for the key only when its step starts. Write the answers to `<project>/BRIEF.md`.

With no keys at all, the film is still complete: the picture drawn in code, and the user's own audio, a library track
or silence.

## Step 2: look first, then motion

1. Pick the look and a palette from a real source (a colour dictionary such as Sanzo Wada's, a painting, a print
   tradition), not generic "vibrant". Name the materials: chalk, woodcut, felt, glass, paper.
2. Build stills first: one frame per shot at full size, shown as a numbered contact sheet. One still per shot, then
   the sheet (here for two shots, at 1.5 s and 4.5 s):
   ```
   node <skill>/scripts/render_frames.mjs picture/index.html --still 1.5 .work/v1/stills/s1.png
   node <skill>/scripts/render_frames.mjs picture/index.html --still 4.5 .work/v1/stills/s2.png
   uv run <skill>/scripts/sheet.py .work/v1/sheet.jpg .work/v1/stills/s1.png .work/v1/stills/s2.png --labels "chalk|ink"
   ```
   The user answers by number ("keep 2, 3; redo 5").
3. Only then animate. Each shot builds itself in its own idiom (the chalk draws, the woodcut is cut, the paper folds),
   then lives (a slow turn, a light that drifts, a camera breath). A shot that holds a finished image reads as "still".

How to draw in code, the render contract and the traps: `references/craft.md`.

## Step 3: render

The picture is one HTML page that exposes `window.TIMELINE`, `window.renderFrame(t, canvas)` (a pure function of
time) and, if it loads images or plates, `window.READY`. `render_frames.mjs` exports every frame as PNG
(`--from N --to M` for a range, `--still t1,t2 out.png` for stills side by side) and fails loudly on a missing file, a
font that did not load or a page error. Render each version into its own folder.

## Step 4: sound

Voice first (it sets the timing), then music measured and aligned to the cut, then foley only where a hand works. Mix
to the delivery loudness with the voice clear on every line (`voice_margin.py`, `loudness.py`). `references/sound.md`.

## Step 5: finish and deliver

Encode with colour tags (a fine film grain on the frames first, if the film wants one), mux, make the 9:16 cut if
asked, and verify frame count, duration, loudness and true peak on the delivered file, not the intermediate.
`references/finish.md`. Never overwrite a version the user has seen: every change is a new version number.

## Step 6: review and raise the quality

Three tools, chosen by the situation (`references/review.md`):
- **Judge**: one read-only critic for one honest opinion on a finished cut.
- **Adversarial reviewer**: for a new animation or a proposal, before the user sees it.
- **Grading panel**: to raise a grade ("it's a 5, make it an 8"): one grader per lens over frozen candidates, in rounds,
  until the lenses reach the bar. Ask the user how many subagents and which models; default to a small panel (you
  build, three graders).

If you cannot spawn subagents, run each critic as a fresh session that reads only the files, or do the review yourself
as a separate pass, and say which.

## Rules that keep it honest

- You measure; you do not see motion in stills or hear audio. Say so with every delivery, and back each claim with a
  number (frames, dB, LUFS, ms).
- Check a change reaches the final pixels before building on it: a constant can be swallowed by a later layer.
- Before acting on a critic's reading, check it against the frames yourself.
- Restraint: when the user says "don't exaggerate", every change is toward calm and truth to the medium, not a new
  effect. When unsure, offer the restrained option first.
- Keep every version, every grade and every decision in files in the project, so the work survives a lost session.

## Files

| Path | What |
|---|---|
| `references/setup.md` | installing uv, Node, ffmpeg, Playwright, optional Blender and fonts on macOS, Windows, Linux, with the user |
| `references/env.md` | the `.env` contract: providers and their variables, how to ask, cost, generated media |
| `references/craft.md` | drawing in code: the render contract, determinism, materials, colour, motion, flicker, the quality bar |
| `references/sound.md` | voiceover, music, foley, the mix command, loudness, voice margins |
| `references/finish.md` | encoding with colour tags, film grain, masters, mux, 9:16, verification, versions |
| `references/review.md` | judge, adversarial reviewer, grading panel (roles, lenses, files, grade template, loop, lessons) |
| `scripts/doctor.py` | dependency check with per-OS install commands |
| `scripts/check_env.py` | which `.env` variables are set (never prints values) |
| `scripts/render_frames.mjs` | export frames or stills from a page that follows the render contract |
| `scripts/sheet.py` | numbered contact sheet from frames or stills |
| `scripts/flicker.py` | flicker and shimmer per tile and per pixel, at 1s and 2s, and old against new |
| `scripts/grain.py` | fine film grain on exported frames: luma only, by tone, one grain per drawing, deterministic |
| `scripts/voice_track.py` | lay the voice lines onto one track from `lines.json` |
| `scripts/levels.py` | RMS over time for several files side by side (ducking, the music's tail) |
| `scripts/loudness.py` | integrated loudness and true peak of a file; two-pass normalisation |
| `scripts/voice_margin.py` | the voice's speech-band margin over everything else, per line |
| `scripts/freeze.py` | freeze a candidate folder (SHA256SUMS, read-only), check it, or print checksums |
| `assets/env.example` | the variables, commented |
| `assets/starter/index.html` | a minimal page that follows the render contract (copy it to start) |
