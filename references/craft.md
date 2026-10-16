# Craft: drawing a film in code

## The render contract

The picture is one HTML page with a canvas and these globals:

```js
window.TIMELINE = { width: 1080, height: 1080, fps: 24, duration: 20.0,
                    shots: [{ id: 1, title: 'chalk', t0: 0.0, t1: 2.5 }, ...] };
window.READY = Promise.all([load('plates/paper.png').then((im) => (paper = im))]);   // optional, see Plates
window.renderFrame = (t, canvas) => { /* draw the frame at time t (seconds) into canvas */ };   // may be async
```

`renderFrame` must be a pure function of `t`: the same `t` gives the same pixels, whatever was rendered before. That is
what lets you re-render one shot, compare two versions frame by frame, and splice a fix into an earlier export.

- Randomness: a seeded generator keyed by what it draws (`rng('rays', k)`), never `Math.random()`.
- Caches are fine only if they do not depend on order. A layer that accumulates strokes frame by frame gives different
  pixels when you render frame 200 cold than when you render 1-199 first. Rebuild such a cache from scratch when the
  requested `t` goes backwards, or key it by `t`.
- The cold-render test, for any page with a cache: render one frame cold twice, and compare with the full export (frame 100 here).
  ```
  node <skill>/scripts/render_frames.mjs picture/index.html .work/cold1 --from 100 --to 100
  node <skill>/scripts/render_frames.mjs picture/index.html .work/cold2 --from 100 --to 100
  cmp .work/cold1/f0100.png .work/cold2/f0100.png && cmp .work/cold1/f0100.png .work/v1/frames/f0100.png
  ```
  (Windows: `fc.exe /b a b`.) All three must be identical.
- Time: step on 2s (a new drawing every 2 frames at 24 fps) for a hand-made feel; keep one global clock for anything
  that must match across cuts (a rotation, a light drift).
- Text in the frame is real type: a font file in the project, declared with `@font-face`. The renderer loads every
  declared face before the first frame. Never let a generator draw letters.
- No network during a render: fonts, images and data are local files next to the page (the renderer allows the page
  to read them) or data URIs.
- `renderFrame` may return a Promise (to decode or seek something first); the renderer waits for it, up to 60 s.
- Every file a frame needs is loaded before the frame returns: in `READY`, or awaited inside `renderFrame`. The
  renderer fails a frame captured while a file is still loading (an image started lazily and drawn "when ready").
- A preview loop (to watch the page in a browser) must not run under the renderer: guard it with
  `if (!navigator.webdriver)`, as the starter does. The renderer fails if the page calls `renderFrame` on its own
  during a render, because an async frame sharing a scratch canvas with the loop gets the loop's pixels.
- WebGL: create one GL canvas once, render into it, then `drawImage` it into the canvas you are given. A new GL context
  per frame recompiles every shader and runs into the browser's limit of about 16 live contexts.

`<skill>/assets/starter/index.html` follows this contract (open it in a browser to watch it loop; `?t=2.5` holds a
time). Copy it to start. Its sizes follow `W` and `H`, so a 9:16 film starts with `W = 1080, H = 1920`.

## Plates

A plate is an image or an image sequence drawn under or over the code-drawn work: a generated texture, a scanned
paper, a photo, frames rendered in Blender, frames of the user's own footage (extract them at the film's fps and size into a folder you create first,
`mkdir -p plates/footage`, then
`ffmpeg -i footage.mp4 -vf "fps=24,scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080,scale=in_color_matrix=bt709:in_range=tv,format=rgb24" -start_number 0 plates/footage/f%04d.png`,
with the film's fps and size; it fills the frame without stretching, and ffmpeg numbers from 1 unless told).

```js
const load = (src) => new Promise((ok, no) => { const im = new Image(); im.onload = () => ok(im); im.onerror = () => no(new Error('cannot load ' + src)); im.src = src; });
let paper; window.READY = load('plates/paper.png').then((im) => { paper = im; });
// a sequence: one image per frame, loaded on demand and awaited
window.renderFrame = async (t, c) => { const f = Math.round(t * TIMELINE.fps); const im = await load(`plates/seq/f${String(f).padStart(4, '0')}.png`); c.getContext('2d').drawImage(im, 0, 0); };
```

Prefer an image sequence to a `<video>` element: seeking a video is not frame-exact in every browser, and frames keep
the film on one clock.

## Look

- One palette per shot, from a real source: a colour dictionary (Sanzo Wada's combinations are a good one), a painting,
  a print tradition. Write the hexes in the code with their source. Judge the palette ON the material, not as swatches:
  the same colours read differently as chalk, glass or wool.
- The subject reads first, at phone size (390 px wide). Check every frame as a phone-size contact sheet
  (`sheet.py --cell 390`).
- Ground and subject are one picture: shared pigments and light, asymmetric, organic. A clean subject on a decorative
  ground reads as a sticker.
- Materials need their own physics. For example: chalk has tooth along the stroke; a woodcut has the cut and the ink's
  salt; stained glass has leading and pieces a glazier could cut; a stamp prints uneven with a pooled rim; thread has
  strands and a sheen. If a material reads digital at 1:1, find the tell (a flat fill, a perfect circle, one texture
  stamped many times, a Voronoi diagram, a vector edge) and draw it the way the material is made.
- A drop shadow under something drawn INTO its ground (ink, paint, chalk, stitches, glass) reads as a sticker. Cast
  shadows only from things that stand proud.

## Motion

- Every shot builds itself in its own idiom, then lives. No shot holds a finished, frozen image for its whole length.
- Life in a hold is slow and continuous: a turn of a degree or two, a drifting light band (it must move the paper by a
  few grey levels to be seen), a camera breath of a few pixels with a matching overscan so no edge is ever bared.
- Cuts land on the beat of the music when there is music (measure the beats; do not guess).
- A transition that turns one material into another (paper spreading, ink soaking) is softer than a hard cut, and
  better than a crossfade, which passes through a muddy middle. A hard cut needs a strong value change or a match
  (the same silhouette in the same place).
- Pacing: give a shot the time its line needs; a voice line plays over its own image, never spilling onto the next.

## Flicker and shimmer

Most "it flickers" notes are aliasing, not animation:
- thin lines (under ~1.5 px) that turn or move crawl; draw them at 2-4x into an offscreen canvas and scale down;
- a hand-drawn boil (re-jittering an outline every drawing) on a hard geometric edge reads as flicker; keep boil off
  geometric outlines;
- fine high-contrast textures (a pixel checker, a dither) shimmer when they move; supersample them;
- never add a weave or shake in the final grade; if a plate needs a weave, apply it to that plate only, sub-pixel.

Measure it: `uv run <skill>/scripts/flicker.py <frames> <t0> <t1> [--vs <older frames>]`. It scores reversals (a
move goes one way; a flicker goes back and forth) per 24 px tile and per pixel, at every frame and every other frame.
Intended grain or boil scores too, so judge a change by comparing against the previous export of the same window
(`--vs`), not against zero. You cannot see flicker in stills.

## The quality bar (notes a director gives, and what they usually mean)

| Note | What it meant | Fix |
|---|---|---|
| "this is still" | a shot held a finished image | build in the medium's idiom, then a slow continuous life |
| "it's flickering" | thin lines or boil aliasing, a weave in the grade | supersample thin work, no boil on geometric edges, no grade weave |
| "the background looks digital" | vector decoration around the subject | paint ground and subject as one picture |
| "it looks like a sticker" | a shadow under something drawn into its ground, a hard rim light | shadows only where things stand proud |
| "pixelated / blotchy" | coarse grain, 8-bit grading, heavy compression in dark areas | grade in 16-bit, fine grain (`grain.py`) encoded at CRF 23 or lower with `-tune grain`, a lower CRF for dark films |
| "a stripe at the edge" | a camera move bared the page | overscan matched to the move, check all four edges |
| "the music is too low" / "the effects are too loud" | first-guess levels | measure: music clearly under the voice, effects well under the music |
| "too much reverb on the voice" | any reverb on narration | a dry voice chain |
| "the line plays over the next image" | a long line pushed later lines off their shots | one short line per shot, placed on its own image |
| "don't exaggerate" | effects added for their own sake | restraint: fewer notes, softer, truer to the medium |

## Generated media in a coded film

Use generated images for what code cannot do well (a photographic texture, a painted backdrop), and keep motion, type
and composition in code. Bring a generated image in as a plate (above) and animate over it. No generated video: the
motion is the code's. Keys, providers and asset records: `env.md`.
