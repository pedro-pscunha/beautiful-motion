# Craft: the render contract

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
paper, a photo, frames of the user's own footage (extract them at the film's fps and size into a folder you create first,
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

Use generated images for what code cannot do well (a photographic texture, a painted backdrop), and keep motion, type
and composition in code: bring a generated image in as a plate and animate over it. No generated video: the motion is
the code's. Keys, providers and asset records: `env.md`.

## Where the rest is

- Colour: `colour.md`. Sanzo Wada's combinations by default, one per shot, picked with `scripts/wada.py` and judged
  on the material.
- Drawing each material, the motion (build then live, one clock for turns, the camera breath, timing to the music,
  soak transitions, the many-into-one ending, stepping on 2s and flicker), the finish on the canvas, and the traps:
  `techniques.md`.
- The quality bar (the notes a director gives, what they usually mean, and the fix): `review.md`.
