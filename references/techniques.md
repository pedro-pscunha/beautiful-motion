# Techniques: drawing and animating materials in code

Each shot is a material: chalk, a woodcut, glass, wool. Draw it the way the material is made, build it in front of
the viewer in the order a maker would, then keep it alive until the cut. Everything here works inside the render
contract (`craft.md`): `renderFrame(t)` is a pure function of time, and every random value comes from a seeded
generator keyed by what it draws. The colours come from one Wada combination per shot (`colour.md`). The sketches
use the starter's `rng(...key)`, `clamp`, `ease`, `W`, `H`, `CX`, `CY` and `FPS`, and this helper:

```js
const smoothstep = (a, b, x) => { const u = clamp((x - a) / (b - a)); return u * u * (3 - 2 * u); };
```

## The picture

### Ground and subject are one picture

- Ground and subject share pigments, light and brushwork. Warm light from the subject spills onto the nearest ground,
  and their edges are lost and found. A clean subject on a decorative ground reads as a sticker.
- Compose asymmetrically: overlap, varied scale and angle, negative space, a dominant diagonal. A regular ring of
  identical leaves round a subject reads as "placed".
- A drop shadow under something drawn INTO its ground (ink, paint, chalk, stitches, glass) reads as a sticker. Cast
  shadows only from things that stand proud: a tile in relief, thread on nails, petals, a folded medallion.
- The subject reads first, at phone size (390 px wide). Check every shot as a phone-size contact sheet
  (`sheet.py --cell 390`), and check each subject is recognisable as itself: a sunflower needs its anatomy (a dark
  seed head in spirals, petals, bracts, rough leaves) before it reads as one.
- No text in a shot: not asemic "lettering", not numerals, not a crayon loop that reads as a cursive e or l. Use
  ornament, coils or hatching. No mark or prop that reads as something else: a hand stamp's carved potato read as an
  egg, French knots as beads, an ear drawn as a ring and a dot as a third eye, a highlight drawn as a closed loop as a
  "2", a forked twig as a "Y", round dabs above a ridge as birds, wide blobs on two trunk ticks as sheep, a medallion of
  rays as a sun (a false reading in a film about falling things). Let the work appear by itself, or use a motif
  native to the craft.
- What reads digital: a flat fill, a perfect circle, one texture stamped many times, a Voronoi diagram, a vector edge,
  Gaussian-blur shading, CG light wedges, mesh-like hatching, geometric facets lit by a key light. When a material
  reads digital at 1:1, find the tell and draw it the way the material is made.

### Many thin layers

Build every surface in many thin layers that behave like the medium: pigment pools and granulates, wet edges dry
darker, paper shows through, wax skips over the tooth, thread twists and shines, glaze has depth, an engraved line
swells with the slope. Constants move colour and motion; they do not move craft. When the tells are shapes drawn
wrong, redraw the shapes.

### The tooth field: where pigment catches

The paper's tooth decides where a dry medium lands, so every layer of chalk, crayon, printing ink or a baren's rub
skips in the same valleys. Build one tooth field: white noise, blurred, then equalised so each value is its own
quantile. A stroke of pressure `p` covers the top `p` of the tooth: light pressure catches only the peaks.

```js
function toothField(key, n = 512) {                 // a repeating tile, built once
  const r = rng('tooth', key), a = Float32Array.from({ length: n * n }, () => r()), b = new Float32Array(n * n);
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {   // a 3x3 blur that wraps, so the tile repeats seamlessly
    let s = 0; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) s += a[((y + dy + n) % n) * n + (x + dx + n) % n];
    b[y * n + x] = s / 9;
  }
  [...b.keys()].sort((i, j) => b[i] - b[j]).forEach((i, k) => { a[i] = k / (n * n - 1); });   // value = quantile
  return a;
}
// the colour a stroke of pressure p leaves on that tooth: pigment on the top p, with a soft edge
function catchTile(T, n, [r, g, b], p, soft = 0.07) {
  const c = document.createElement('canvas'); c.width = c.height = n;
  const x = c.getContext('2d', { willReadFrequently: true }), im = x.createImageData(n, n);
  for (let i = 0; i < n * n; i++) {
    const u = Math.min(1, Math.max(0, (T[i] - (1 - p - soft)) / (2 * soft)));
    im.data.set([r, g, b, 255 * u * u * (3 - 2 * u)], 4 * i);
  }
  x.putImageData(im, 0, 0); return c;
}
// g.strokeStyle = g.createPattern(catchTile(T, 512, [244, 226, 190], 0.4), 'repeat'); then stroke the path
```

The pattern is anchored to the page, not to the stroke, so every layer lines up on the same tooth. Round `p` to about
twelve steps and cache one tile per colour and step.

### One key light for the whole film

One light, about upper left, drifting slowly on smooth noise, never reset at a cut. Every glint, sheen, raking light
and cast shadow reads it, so the light carries across the cuts. The same effect repeated on every shot (one sheen band
crossing each subject) is the most mechanical thing a film can have.

```js
function noise1(t, seed) {                            // smooth 1D value noise in -1..1
  const i = Math.floor(t), f = t - i, u = f * f * (3 - 2 * f);
  const h = (k) => ((Math.sin((k + seed * 101.3) * 127.1) * 43758.5453) % 1 + 1) % 1;
  return (h(i) * (1 - u) + h(i + 1) * u) * 2 - 1;
}
function keyLight(t) {                                // (lx, ly): the unit vector toward the light on the page
  const az = -0.75 * Math.PI + 0.16 * noise1(t * 0.06, 1) + 0.04 * noise1(t * 0.15, 2);
  return { az, lx: Math.cos(az), ly: Math.sin(az), el: 0.55 + 0.08 * noise1(t * 0.12, 3) };
}
```

Keep it slow: a glint 420 px from its pivot must move under about 1.5 px per drawing.

### Bake once, draw many

- Paint heavy, static layers once into offscreen canvases and lay them every frame; draw per frame only what moves
  (glints, the hand, the light). Create each offscreen context with `getContext('2d', { willReadFrequently: true })`:
  without it Chrome can defer the drawing and dump about 800 ms onto one frame.
- Bake a layer in the subject's own frame at its own mid-hold angle, so its baked light keeps its true direction, and
  turn only the small remainder at draw time, with `imageSmoothingQuality = 'high'` (`'low'` tripled the shimmer on
  thin lines).
- A layer that builds up item by item keeps its count and rebuilds from scratch when `t` goes backwards (the cache
  rule in `craft.md`).
- Seed each object by what it is (`rng('shard', x, y)`), not from one stream shared by all, so revealing items one by
  one, or adding one, never reshuffles the rest.

## Materials

Each material has its build (the order a maker works in), what makes it physical, and its tell (what makes it read
digital).

### Chalk on a slate

- Build: side-of-the-chalk strokes accumulate, pass over pass.
- Physical: wide strokes that catch only the slate's tooth; the subject modelled by the key light, heavy on the lit
  side, cooler hatching in its shade and a smudged shadow on the board; dust that falls and settles; the board keeps
  the ghosts of an erased lesson (a compass circle, an older drawing).
- Tell: a line of one even width; a clean black board.

### Wax crayon

- Build: a light first pass, the shade colours worked over it, then the burnisher.
- Physical: wax catches the peaks of the tooth, so every pass leaves the valleys white (pressure per stroke on the
  tooth field). Hatch in overlapping bands, row after row: loose loops read as handwriting. Shade with pressure and a
  second and third colour, not with black. Burnishing presses the wax into the valleys in its own colours and gives it
  a sheen; a glint can travel the burnished wax through the hold.
- Tell: a flat fill; strokes that never skip.

### Woodcut

- Build: the print is pulled in front of the viewer, block by block. Each block's ink comes up where the baren rubs,
  in small circles along rows, peak first. Then a raking light crosses once and finds the emboss.
- Physical: the cut, the plank and the ink.
  - The cut: V-gouges with a quick entry, widest a third along, a long taper out. Cuts widen on the lit side, so the
    cutting itself models the light.
  - The block: the plank's grain in the ink, the baren's uneven pressure, a darker squeeze of ink at every edge.
  - The ink's salt: ink stays off the paper where the paper is low (the tooth field again).
  - Several blocks: one colour each, the key block a hair (2 px) off register.
- Tell: an even ink fill; cuts of one width.

```js
// a V-gouge along polyline P (fill it in the cleared colour, or cut it out of the block's mask)
function gouge(g, P, w, r, entry = 0.3) {
  const A = [], B = [];
  P.forEach((p, i) => {
    const u = i / (P.length - 1), a = P[Math.max(0, i - 1)], b = P[Math.min(P.length - 1, i + 1)];
    const nx = a[1] - b[1], ny = b[0] - a[0], l = Math.hypot(nx, ny) || 1;
    const half = w * (u < entry ? Math.sqrt(u / entry) : 1 - 0.94 * (u - entry) / (1 - entry)) * (0.95 + 0.1 * r()) / 2 + 0.25;
    A.push([p[0] + nx / l * half, p[1] + ny / l * half]); B.push([p[0] - nx / l * half, p[1] - ny / l * half]);
  });
  g.beginPath(); [...A, ...B.reverse()].forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); g.fill();
}
```

### The stamp (a hand-cut block print)

- Build: prints land one by one; the hand fills the ground row by row. The stamp is re-inked every few prints, so the
  prints go from full and wet to starved and grainy, and back. The wet ink dries matte in the order it was printed.
- Physical: one cut face is the same in every print it makes (its texture, a low patch where the cut was not flat,
  the knife's chatter). Model the face once as fields; each print is that face inked: denser where the ink pooled at
  the cut edge, a faint squash past the edge, grains skipped, one side pressed harder. Lay every print with
  `multiply`: ink is transparent, and overlaps darken. Never show the tool.
- Tell: one sprite stamped identically; a print with a clean even edge.

```js
// one print of a face. Per face, built once: M its shape (0/1), E the shape blurred 3 px (how far in from the edge),
// F how readily each spot takes ink (cells, a low patch, chatter), G a clumped salt. load: 1 fresh .. 0.4 nearly dry
function printAlpha(i, x, y, face, load, press) {   // press: -1..1 along the direction pressed harder
  const { M, E, F, G } = face, th = 0.9 - 0.78 * load, rim = Math.min(1, Math.max(0, (0.95 - E[i]) / 0.45)) * M[i];
  let a = smoothstep(th - 0.13, th + 0.13, F[i] + 0.35 * press + 0.3 * rim) * M[i] * (0.72 + 0.28 * load);
  if (G[i] > 0.82 + 0.13 * load) a *= 0.3;                                    // grains the ink skipped
  const squash = 0.2 * load * smoothstep(0.04, 0.45, E[i]) * (1 - M[i]);      // ink pressed out past the edge
  return { alpha: Math.max(a, squash), darken: 0.7 * rim };                   // the pooled rim prints darker
}
```

### Stained glass

- Build: the lead first, then the glass set piece by piece from the centre out. Once the subject is glazed, a slow
  swell of light runs out along the leading, ring by ring, each pane brightening in its own colour.
- Physical: pieces a glazier could cut: gentle convex shapes, no deep inner corners, no slivers. Streaky glass (two
  colours rolled together, drawn out in one direction), seedy with bubbles (each a small lens with a dark rim and a
  bright eye), brighter toward the light behind. The glass darkens under the lip of the came. The cames are rounded
  lead with a narrower dark heart and a highlight on the side the room's key light comes from, with a blob of solder
  wherever three or more meet. The window is lit from behind: clouds drift behind it, each pane tinting them through
  its wavy glass, and dust motes drift in front.
- Tell: Voronoi cells; flat panes; lead of one flat grey.

```js
function lead(g, paths, w, L) {                     // L = keyLight(t)
  const all = () => { g.beginPath(); for (const P of paths) P.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); };
  g.save(); g.lineJoin = 'round'; g.lineCap = 'round'; all();
  g.strokeStyle = '#3a3940'; g.lineWidth = w; g.stroke();                     // the came
  g.strokeStyle = '#2b2a31'; g.lineWidth = w * 0.5; g.stroke();               // its rounded heart
  g.translate(L.lx * w * 0.26, L.ly * w * 0.26);
  g.strokeStyle = 'rgba(175,175,188,0.3)'; g.lineWidth = Math.max(1.2, w * 0.18); g.stroke();   // lit side
  g.restore();
}
```

### Mosaic, pebble floors and broken tile (trencadís)

- Build: the sinopia (a red-ochre underdrawing) on the bed, then a strip along the contour, the figure, the field and
  the floor, slowing to one piece at a time; the last piece is set at the cut. Broken tile: shards pressed into the
  mortar from the middle out, a jewel set last.
- Physical: the rows follow the outline (andamento). Take them from the isolines of a signed distance field to the
  outline: the outline row first, then rows inward; the ground in looser, straighter rows. Each piece is its own
  object:
  - A pebble is a dome of stone with its own grain and polish, sunk in the mortar so the joints hold shadow.
  - A tile shard has a glazed, lit bevel on the key light's side, glaze pooled dark at its broken edge, chipped
    bisque and crazing on the whites, and its own small tilt, so a moving light runs glints across the wall.
  - Mortar and grout are neutrals with grit, darker while wet. A wet floor dries in a slow front, and while it is wet
    a highlight slides over every dome.
- Press, never fade: each shard opaque from its first frame, a hair large, a few px off and tilted in the fingers, with
  a cast shadow on the wet bed, pushed home flat over about 0.2 s. A 3-frame fade-in reads as an effect, not a hand.
  Plain opaque presses gave 60 frames with one-frame pops in a 2 s build; the tilt, the notched trowel and the lumps
  brought them to 10. Shading a shard's glaze toward the bed's tone for its first frames softens the step too (with
  the shading at 70 %, 14 frames popped; at 30 %, 29), but on a figure that much reads as a pale ghost: keep the
  figure's pieces under about 25 %.
- The bed: lay the wet mortar in trowel passes, bands about 90 px deep outward from the nearest object, each pass a
  few strokes with a raw, bulged leading edge (a notched trowel on fast runs, daubed lumps on domes), each band done
  before its first shard; dry each joint after its shard is home. A threshold on noise lays it as islands ahead of
  the front, and a bed that arrives after its shard shows the shard floating. A figure in shards gets its own bed on
  bare paper, left clear from the start (no wall shards under it), laid in a few opaque strokes, then its rows, so the
  field never shows through it.
- The fall: break the wall into lumps of a few cells that keep their joints, with a darker raw edge where they part
  and crumbs, so the mortar falls with its shards instead of fading. A piece that leaves its bed leaves a broken edge
  and crumbs behind, not a clean die-cut hole.
- Tell: a Voronoi diagram (crazing too); identical tiles; a grid; a bed laid in even stripes or shaded like an
  airbrush.

### Maps and the real Earth

- Real coastlines (Natural Earth, public domain) read as our planet at a child's glance; invented blobs do not. Keep
  them as data, simplified (Douglas-Peucker, small islands dropped, a few thousand points), in a page file with the
  source, version and licence at its top, written by a tool from the download; parse the download, never run it.
- Natural Earth's land joins Africa to Eurasia and the two Americas in one ring: cut them at Suez and Panama before a
  continent can be its own piece or projected alone.
- A field-driven drawing (passes that read a land field by thresholds) takes the real shapes when the field becomes
  the signed distance to the real coast, scaled to the old field's slope at the coast: every tuned threshold keeps
  its meaning. Bake it once in init; never project per pixel per frame.
- A whole globe: an orthographic view on the drawing's own axis (the Atlantic facing is the classic). The top of a
  huge Earth, seen close: an orthographic view squashes the land at the rim, so lay an azimuthal equidistant map
  centred below the rim and let the rim cut it like a horizon. Use one view for every whole Earth in the film, so they
  read as one planet.
- Figures standing round a globe's rim land where the view puts them, often on the sea. Find the real island nearest
  under each foot (a scan of the rim against the data) and draw it large enough to stand on, a soft oval hugging the
  rim, in the scene's own land passes: less visible than turning the globe or sliding the figures.

### Embroidery

- Build: stitch by stitch, with the needle still working in the hold.
- Physical: real stitches. Fishbone satin stitch for a leaf or a ray, long-and-short shading for a disc, a cord
  couched along the outline; a woven-wheel rose instead of a knot cluster. The floss shows its strands. Each stitch
  has a sheen that depends on its direction against the light, so as the light drifts the satin turns, ray by ray.
  The linen's weave is real (over and under), drum-taut in the hoop and gathered beyond it.
- Tell: a filled shape with a stitch texture on top; one highlight on every stitch.

```js
// a stitch or thread at angle th shines when it lies across the light
const sheen = (th, az, k = 4) => Math.abs(Math.sin(th - az)) ** k;
// bin the stitches by angle (a dozen bins), stroke each bin once: a highlight of alpha 0.06 + 0.74 * sheen, offset a
// hair toward the light. Read az from keyLight(t), swung slowly (+-0.8 rad) so the two halves of a fishbone flip.
```

### Knitting

- Build: knitted in front of the viewer, round by round from a centre or row by row from the hem, the yarn running
  from the stitch being worked to its ball.
- Physical: every V stitch is two legs of plied yarn with slanted ply ridges, shaded round, lit from the key light,
  with a halo of loose fibre. The fabric hangs in soft folds that shade whole columns; a rib at the hem.
- A knitted subject that turns with its whole garment reads as still. Knit it as a medallion in the round (a cast-on
  ring, rounds, increase wedges, a bind-off), sewn on, and turn the medallion over the still garment.
- Tell: a knit texture tiled over a flat shape; stitch rows that ignore the shape's outline.

### Pointillism

- Build: patch by patch: the base dabs, then the light and the shade, then a halo of complementary flecks.
- Physical: pure dabs side by side on a pale ground, laid along a calm flow. Model the subject with the dabs' colours
  (pale and warm on the lit side, deeper and cooler in shade), never by darkening. Through the hold the halo vibrates
  outward and light flickers slowly across the lit side.
- Tell: identical round discs on a grid.

### String art

- Build: thread wound nail to nail in front of the viewer, a free end running to the spool; in the hold, a last
  thread still winding.
- Physical: nails with their own light and shadow. Envelopes: a star winding for a disc, parabolic envelopes for a
  ray. Each thread sags a hair, casts a shadow on what lies beneath and catches the light by its direction
  (`sheen` above).
- Where many threads cross within a few pixels (a hub), draw the layer at 4x into an offscreen canvas and filter it
  down. At 1x they alias into a moiré that changes at every step of a turn.

```js
function thread(g, a, b, col, w) {                  // nail a to nail b, light from the upper left
  const s = 0.012 * Math.hypot(b[0] - a[0], b[1] - a[1]), mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2 + s;
  for (const [dx, dy, c, lw] of [[1.6, 2.4, 'rgba(40,22,8,0.38)', w + 1], [0, 0, col, w]]) {   // shadow, then thread
    g.beginPath(); g.moveTo(a[0] + dx, a[1] + dy); g.quadraticCurveTo(mx + dx, my + dy, b[0] + dx, b[1] + dy);
    g.strokeStyle = c; g.lineWidth = lw; g.stroke();
  }
}
```

### Contour map

- Build: surveyed from the summit down, level by level, the colour following wet; through the hold the washes dry
  lighter and the light drifts.
- Physical: one height field under the whole sheet. An engraver's hachures run downhill between contour levels,
  heavier where the ground is steep and on slopes turned from the light. A fine pen contour every second level and an
  index contour every eighth, a little unsteady by hand. The tints are stepped watercolour washes with dried rims,
  granulation and a few blooms, lifted off the lit slopes. Aged paper, a border, a compass rose; no lettering, real or
  asemic.
- Tell: Gaussian-blur hillshade, CG light wedges, a mesh of crossing hatches.
- Turn the whole terrain inside the border, never one massif alone: that doubles the contours.

### Cut and folded paper

- A cut-out: sheets brushed with gouache, shapes cut with scissors so the white core of the paper shows at the cut
  edge, pinned a hair above the ground, laid down one by one.
- A fold: paper dyed with watercolour before it is folded (colours running wet into each other, a bloom where they
  met, the paper's long fibres), pleated by hand in radial mountain and valley folds. The light falls softly across
  the pleats: each face a little brighter toward its ridge, the shaded faces glowing with light bounced in from their
  neighbours, never grey. It folds up in a wave, then relaxes through the hold.
- Tell: flat facets lit by a key light read as CG.
- Check each shot against what the words say about it: if the voice says "fold", the paper must fold.

### Brush

- Build: one gesture. The brush presses down, winds out and, without leaving the paper, runs into every part of the
  shape.
- Physical: a damp ground first (a pale underwash), then a wet-in-wet charge that blooms and opens back-runs. The
  stroke shows its bristle tracks; where the load runs out it breaks into dry brush on the tooth (the tooth field with
  pressure falling along the stroke); where the painter reloads, it lands again in a fresh, wet pool. The wet paint
  glistens and dries matte in the order it was laid.
- Tell: a stroke of constant width and constant opacity.

### The child's drawing

- Build: the crayon itself draws, lifting between marks. The outline goes round once, pressed hard; the fill is a
  quick zigzag scribble in two or three passes whose step and swing change as the hand goes, running past the line
  here and there, a few patches left bare; simple features last.
- Physical: cheap ruled school paper with a coarse tooth.
- Tell: ruled rows of identical chevrons; handwriting (it is text in the shot).

### Ink and watercolour

- A wash is many near-transparent layers of one shape, each deformed again, with holes. Pigment migrates to the wet
  edge, so the rim dries darker; it granulates in the tooth; where wet meets damp it blooms. The paper shows through.
- Ink starts glossy and dries matte and a little lighter, in the order it was laid. That keeps a finished image
  changing through its hold.
- A print of several inks: each ink on its own pass, a small offset between passes, `multiply` where they overlap.

```js
function deform(P, depth, r, amp) {                 // move each edge's midpoint by up to amp x its length
  if (depth === 0) return P;
  const out = [];
  P.forEach((p, i) => {
    const q = P[(i + 1) % P.length], l = Math.hypot(q[0] - p[0], q[1] - p[1]);
    out.push(p, [(p[0] + q[0]) / 2 + (r() - 0.5) * amp * l, (p[1] + q[1]) / 2 + (r() - 0.5) * amp * l]);
  });
  return deform(out, depth - 1, r, amp * 0.7);
}
// base = deform(shape, 3, rng('wash', k), 0.5); then 30-60 layers of deform(base, 3, rng('wash', k, j), 0.35) at
// alpha 0.02-0.04, each cut by a few holes (a noise threshold); stroke each layer's edge a little darker
```

## Motion

### Build, then live

- Every shot builds itself in its own idiom, then lives. A shot that holds a finished image reads as "this is still".
- Three layers of motion per shot:
  - primary: the build (strokes accumulate, glass is set, rows are knitted, contours drawn level by level);
  - secondary: the material answers the light (glints travel, threads catch, glaze shimmers, washes dry lighter);
  - ambient: the ground breathes (a gust, a cloud shadow, settling pigment).
- The build reads within about 1.1 s; slow hand work can go on after it. Drive it from the shot's own clock,
  `prg = ease(clamp((t - t0) / 1.1))`, and show the medium from the shot's first frame: a bare page or an empty
  subject at a cut is a defect. Builds can quicken through a film (scale them down to about 0.55 by the end).
- Life in a hold is slow and continuous: rates that never line up (incommensurate), sparse local events over a moving
  field, motion that comes from the medium itself. The best shots still have a hand working at the cut: the crayon,
  the stamp, the needle.
- Steady to the cut: no ambient motion ramps down before a transition. A drifting light band must move the paper by a
  few grey levels to be seen at all.
- Easing: long cubic ease-out and ease-in-out, no overshoot. No scale pump on the beat (it reads as dance music); a
  warm light lift on arrival instead.
- An opening can construct the subject with the tools of a drawing lesson (a compass swings the circle, a ruler lays
  the lines, a pen closes the outline), keyed to the voice.
- Measure the holds: the mean absolute frame difference over 1 s, per shot, late in each hold. The weak holds are the
  ones far under the film's median; fix them before anyone sees the cut.

### One clock for every turn

When a subject turns, every shot turns it on ONE clock, continuous in film time and never reset. With a rate per shot,
the subject's angle jumps at every cut and a match cut shows two subjects instead of one changing material.

```js
const TURN_W = 0.0225, TURN_SWELL = 0.15, TURN_PHI = 0;   // rad/s, +-15 % swell, phase
// the exact integral of a rate that swells on two incommensurate frequencies
const turn = (t) => -Math.PI / 2 + TURN_PHI + TURN_W * (t - TURN_SWELL * (0.62 / 0.83 * Math.cos(0.83 * t + 0.4) + 0.38 / 1.91 * Math.cos(1.91 * t + 2.2)));
```

- The fastest edge on screen sets the rate: at the peak of the swell it must move under 1.5 px per drawing. On 2s at
  24 fps, corners 760 px from the centre allow `1.5 / (760 / 12)` = 0.024 rad/s at the peak: 0.020 rad/s with a
  ±15 % swell. The sketch's 0.0225 keeps every edge within about 690 px of the centre. Much slower than 0.02 rad/s,
  viewers stop seeing the turn.
- Choose the phase so the poses that matter land: for example the longest ray straight up where the ending begins.
- What turns follows what is true for the medium:

  | Medium | What turns | What stays |
  |---|---|---|
  | print, woodcut, stamp | the printed image | the sheet |
  | brush | the subject in its reserve of bare paper | the wash |
  | map | the whole terrain inside the border | the border |
  | tile, mosaic | the subject as a panel set into the floor or wall | the wall |
  | stained glass | the subject and its rose, as a wheel in the window | the window |
  | knitting | a medallion knitted in the round | the garment |
  | embroidery | the cloth in the hoop | the hoop |
  | string art | the nails and threads, redrawn each frame | the board |

  Never tear the medium: no layer turning alone over a still one it belongs to (doubled contours, bared paper,
  stitches sliding over cloth).
- A subject that turns with its ground reads as still. Measure each shot: the subject's angle against the frame's
  corners, not against its ground.

### The camera breath

A camera that breathes a few pixels keeps a hold alive. Scale it by an envelope that is 0 under titles (type must not
weave) and where shots must line up (a closing grid), and overscan in step with it, so no edge is ever bared.

```js
function camBreath(t, e) {                          // e: 0..1
  return { x: 3 * e * noise1(t * 0.1, 22), y: 3 * e * noise1(t * 0.1 + 7.3, 23),
           s: 0.004 * e * noise1(t * 0.15, 21) + 0.012 * e };   // the + 0.012 * e is the overscan
}
// const b = camBreath(t, e); g.translate(CX + b.x, CY + b.y); g.scale(1 + b.s, 1 + b.s); g.translate(-CX, -CY);
```

- The overscan per side (`W * s / 2`) must exceed the drift plus the breath-out: at 1080 px, 0.8 % gives 4.3 px
  against a 3 px drift.
- Add a slow push-in across the whole film (scale 1.00 to 1.05), and let the subject layer drift a little further
  than its ground (about 1.3x the ground's breath) for depth.
- Check all four edges every 0.5 s across the film: compare the outer column and row with the ones 4-10 px in. Ignore
  borders that are drawn on purpose.

### Timing to the music

- The music's measured downbeats are the clock: shot `i` starts on downbeat `i`, one shot per bar, an opening of one
  or two bars. Measure the beats (`sound.md`); never assume a grid from the tempo. A film put on a fixed grid before
  its music (`sound.md`) keeps that grid as its clock, and each soundtrack is measured and laid onto it.
- Give a shot the time its line needs: a voice line plays over its own image, never spilling onto the next.
- A shot's arrival starts a little before its downbeat (about 0.17 s), so the transition is about two thirds done on
  the beat.
- A shot designed for one bar length plays in another by warping its own clock:
  `local = (t - t0) * DESIGN_HOLD / hold`. Every build and hand gesture then spans the new bar. Keep the transition,
  the turn clock and the ambient motion in real seconds. Any hard-coded moment ("mid-hold", "the next cut") must use
  the warped time too.

### Soak transitions between materials

The subject keeps its place, so a cut can be a change of material: the new medium soaks through the old like ink or
water through paper. It is softer than a hard cut and better than a crossfade, which passes through a muddy middle.
(A hard cut needs a strong change of value, or a match.)

```js
// the arrival-time map of one cut, N x N, built once: a designed shape plus paper noise, rank-equalised, so at
// progress p exactly a fraction p of the frame has soaked, whatever the shape
function soakField(cut, shape, N = 320) {
  const T = new Float32Array(N * N);
  for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
    const x = (i + 0.5) / N, y = (j + 0.5) / N;
    T[j * N + i] = shape(x, y) + 0.11 * paperNoise(x, y, cut);   // shape: Math.hypot(x - 0.5, y - 0.5) blooms, (x + y) / 2 runs on a diagonal
  }
  [...T.keys()].sort((a, b) => T[a] - T[b]).forEach((q, k) => { T[q] = k / (T.length - 1); });
  return T;
}
// each frame of the transition, at eased progress p: per cell, d = p - T[q]
//   the outgoing frame's alpha = 1 - smoothstep(-0.004, 0.004, d)
//   a warm dark wet rim just behind the front = d > 0 ? 0.72 * smoothstep(0, 0.002, d) * Math.exp(-d / 0.007) : 0
// scale both maps to W x H with 'high' smoothing; mask the outgoing frame with the first ('destination-in') over the
// live incoming frame, and lay the rim with 'multiply'
```

- `paperNoise` is a cloudy formation (value noise at three scales) plus fibres (noise stretched along one direction),
  so the front wanders like a wet edge in real paper.
- Vary the front's shape along the film: an iris, a bloom from the centre, drops, a diagonal from the key light, a
  clock sweep, along the subject's own lines, a rising tide.
- Let the incoming material make the cut where it can: lead lines first and the panes after them, dabs that grow
  until they close, knitted rows, tesserae laid along the outline, threads strung across. Each cell opens the old
  frame over at least two drawings, so nothing pops. Key the material soak to the incoming shot, not to the cut's
  position: a reorder must not bring a stamp in through lead lines.
- Hold the subject back: the ground soaks first, then the subject once its build is under way. Otherwise a slow
  build shows an empty subject at the cut.
- The outgoing shot stays live under the soak: its own clock keeps running (light, glints, turn).
- After any reorder, compare every cut window: a cut from a light shot into one whose build starts dark in the middle
  flashes light, dark, light. Choose a different neighbour.

### Passing on a fall

A film with one travelling object (an apple through every scene) can pass between scenes on its flight: the figure
tosses it up, it slows and leaves through the top, the cut lands on its apex, and it falls into the next scene from
above, on ½·g·t² the whole way. Where "down" is toward a globe's centre (a whole Earth in frame), leave through the top,
so the object never seems to fall away from the Earth. Give each scene its own g, so a fall lasts about as long at
every drawing's scale, and say honestly what that g is (about 0.56 of real g at those drawings' scale): the motion is
a true fall, the scale is a convention. Time each toss so its apex lands exactly on the next cut, and key the catch
and the landing to their words.

An object that falls from something hangs from it first, where the viewer can see it: an apple by its stem from a
branch that shows from the trunk out (open the crown under it, and let more branches show through it), not out of a
mass of leaves. Thrown back, it lodges in a fork of that branch.

### Figures that act

- A figure drawn small (80-150 px tall) at 1x loses its face: draw it at 3x and filter it down, with the face designed
  for the size it shows at. At phone size a figure under about 130 px reads as a dot; enlarge the figure, not the
  object it holds (an object 0.5-0.8x the head's width).
- Every object a figure holds sits in a drawn hand at the rig's hand point (a mitten with a thumb nub about 0.28x the
  head's width in a child's drawing), never floating beside it.
- Holds live: a breath, blinks every 2.5-4.5 s with both lids alike, a gaze that follows the object, a weight shift
  or one gesture every 2 s or so, and a joy beat (a lean, a second bounce) alive to the last frame.
- A throw gets 3-4 frames of anticipation (a reach back) before it, and two in-betweens wherever a hand would jump
  more than a few px in a frame. A jump's first airborne frame that lifts 50 px reads as a pop: ease the take-off over
  3-4 frames.
- A child tosses something up with both hands: both arms swing up together from beside the legs, in front of the
  chest, to above the head, and stay up after the release; whenever the child holds the object, both hands hold it. No
  arm passes behind the torso in any frame: a one-armed throw wound back behind the body reads as a broken arm.
- One table of limb proportions for every figure in the film (a child's upper arm about 0.15 of its height, the
  forearm 0.14), shared by every scene's rig: limbs set by hand in one scene read as too long.
- A child needs a neck (a short one, the head turned 20-30 degrees toward the body); a chin on the shirt reads as
  hunched or sad.
- Draw a pose with asymmetry and overlap. Both arms set from one rig with mirrored values (straight, parallel, the
  hands side by side, the sleeves stacked) read as posed: one lower and bent, one reaching a little further.

### The many-into-one ending

A catalogue can end by gathering every shot into one image and dividing it again. What made it read:

- It grows out of the last shot, and no drawing appears twice. Name that shot in the code (`const ENDING_FROM = ...`);
  never assume it is still the last one after a reorder.
- Divide the whole frame into equal parts, one per craft, each showing its whole world, with the subject continuous
  across the parts. The same gentle spiral seam, rotated, reads as one object; straight seams meeting at the centre
  read as a pie chart. Cut the seams by hand (a few px of wobble).
- Each part arrives in its own idiom, slowly (about 1.2-1.4 s each), the most legible first, the last landing on a
  measured strike in the music.
- In flight: scale changes in one direction only and never under about 60 % of the final size; the flying layer moves
  on 1s (on 2s it strobes); a piece becomes its destination opaquely, never through a translucent double image; a
  landing hands over to the finished print over about 0.35 s (a 2-frame swap blinks; keep each part's luminance step
  under 0.5 %).
- Light laid over the last shot must not wash out its colour: a warm screen took 24-34 % of a crayon shot's
  saturation. Keep the screen low, darken with `multiply`, and measure saturation before and after.
- The last touchdown lands on the final chord; a title is written after the last spoken line, not over it.

### On 2s, and flicker

A new drawing every 2 frames at 24 fps gives the hand-made feel. Re-draw the hand's wobble (the boil) per drawing,
and drive everything else from continuous time.

```js
const frame = Math.round(t * FPS), drawing = Math.floor(frame / 2);   // the boil changes on even frames only
const wobble = rng('outline', drawing);                                // the hand drawn again, per drawing
const drift = 3 * noise1(t * 0.2, 5);                                  // ambient motion: continuous in t, never keyed by drawing
```

- Per drawing: at most about 1.5 px of travel and 3 % of alpha; nothing faster than about 3 Hz; smooth noise or
  incommensurate sines. Cross-fade a cached layer instead of re-seeding it.
- No boil on hard geometric outlines (facets, tiles, glass): it reads as flicker. Keep those alive with light instead.
  A layer that turns inside a clip that also boils flickers at the edge.

Most "it flickers" notes are aliasing, not animation:
- thin lines (under about 1.5 px) that turn or move crawl: draw them at 2-4x into an offscreen canvas and scale down;
- fine high-contrast textures (a pixel checker, a dither) shimmer when they move: supersample them;
- never add a weave or shake in the final grade; if a plate needs a weave, apply it to that plate only, sub-pixel.

Measure it: `uv run <skill>/scripts/flicker.py <frames> <t0> <t1> [--vs <older frames>]`. It scores reversals (a move
goes one way; a flicker goes back and forth) per 24 px tile and per pixel, at every frame and every other frame.
Intended grain or boil scores too, so judge a change against the previous export of the same window (`--vs`), not
against zero. You cannot see flicker in stills.

"It glitches sometimes" is usually a one-frame pop: a stroke laid whole in one frame, a pose that snaps, a boil
redrawn over a whole figure, a cache rebuilt differently. Scan every export:
`uv run <skill>/scripts/glitch_scan.py <frames> [from] [to] --cuts <cut frames>`. It lists each frame where a 48 px
tile steps in that one frame (over 6 levels and over 3x its change on either side), with where. Compare a new export
with the last one's list: no new pops, and every pop left is a cut or a contact you can name.

## The finish on the canvas

One finish over every frame makes many techniques read as one body of work. Build each layer once; apply it in screen
space after the frame is drawn:

- the paper: a cloudy formation, a few thousand short fibres both light and dark, and a fine tooth, centred on mid
  grey and laid with `overlay` at about 0.34: zero-mean, so the mean colour does not move;
- the vignette: one cached layer, a little deeper toward the lower right (away from the key light), `overlay` 0.42;
- the key light pooled: a soft radial gradient that follows `keyLight(t)`;
- the canvas's own grain: one full-frame noise field, slid to a new offset per drawing (on 2s), `overlay` 0.2;
- a restrained bloom: only true highlights (luma above about 238) glow, from a 1/8-size copy, `screen` 0.3.

```js
const r = rng('grain', Math.floor(Math.round(t * FPS) / 2)), ox = Math.floor(r() * W), oy = Math.floor(r() * H);
g.globalCompositeOperation = 'overlay'; g.globalAlpha = 0.2;
for (const [x, y] of [[-ox, -oy], [W - ox, -oy], [-ox, H - oy], [W - ox, H - oy]]) g.drawImage(GRAIN, x, y);   // wraps
```

- Use `overlay`, not `soft-light`: soft-light lifted and desaturated dark shots (a slate went olive). Measure luma and
  saturation with and without the finish; the combination's hues must hold.
- The canvas grain and `grain.py` do different jobs. The canvas grain is texture in the picture, on 2s with the
  drawings. The H.264 delivery keeps only part of its movement: 24-59 % in one measured film. `grain.py`
  (`finish.md`) adds a fine luma grain to the exported frames, built to survive the encode. Use both, at their
  defaults. Never add a second paper, vignette or bloom in the grade: the canvas has them.

## Traps

- Shutter blur from sub-frames spaced more than about 0.7 px apart ladders thin edges into stepped copies (a smile, a
  paper edge), and reads as a glitch: use n = ceil(move / 0.7) sub-frames (cap 64), or draw stop-motion materials
  (cut paper, felt, clay) crisp, with a drawn smear for a fast move. Check a 4x crop of the fastest frame.
- A build that shows a patch's finished pixels the moment the tip passes is a one-frame pop: fade each stroke in over
  about 3 frames behind the tip, ease every reveal in, and spread stroke starts so no tile gets several in one frame.
  That is for drawn strokes: a placed piece (a shard, a clay lump, a paper cut) arrives opaque, and a fade reads as an
  effect (see the stop-motion arrival below).
- A stroke that grows from nothing starts at nothing: a round start cap drawn whole while the stroke's length is
  still 0 is a dot in its first frame, and a word's strokes starting together pop their tiles. Run the reveal over the
  caps too. Grow it evenly (a smoothstep over about 0.28 s), not mostly in its first frame (an ease-out).
- A stroke carried through a flow keeps the colour it was born with. Coloured by where it is now, it flips colour in
  one frame each time it crosses a band's edge (63 of 192 frames popped in an 8 s sky; none once coloured at birth).
- An overlay switched on at any strength (a shadow, a glow) pops in its first frame: fade it in from 0.
- Blinks at an even pace (3 frames closing, 2 shut, 4 opening), both eyes on the same frames, never pop.
- A cache that evicts a subject's rest drawing and rebuilds it later pops when the subject returns to rest: keep the
  rest drawing as one fixed image.
- Averaging many sub-frames with `lighter` in 8 bits loses the small shares: accumulate in groups of 8, then combine.
- Revealing a baked layer through a stroke mask uncovers neighbouring strokes wherever the mask is wider than the
  stroke: bake crumbs and dots on their own layer, and stop overlapping strokes short of each other.
- A shared figure rig that turns the head centre with the body's lean but builds the eyes upright slides the eyes
  across a head the scene rotates itself: draw every feature in the head's one transform.
- A cue written as a time goes stale when the voice is re-laid: key every cue to its word (`wordT`).
- A shared effect added over every shot can damage the ones that build themselves: a generic arrival glow drew a pale
  ghost of the subject before its build, and a lift-off shadow outlined a blank shape under prints, which have no
  relief. Give such shots an opt-out.
- `isPointInPath` uses the context's current transform. Hit-test on a separate context with an identity transform.
- A `ctx.save()` that slid into a comment left its `restore()` to pop the frame's outer state, which leaked into
  later draws, invisibly in stills. Count save/restore depth per frame when you edit shared code.
- To make a line thinner, scale its whole stroke stack with one constant: the shadow, the body, the shade and
  highlight offsets, the joints. Otherwise the shadow and highlights stay fat round a thin line.
- After moving any type, crop it at the moments a drawing that builds under it reaches it, not only on the last frame.
- While any cache still depends on which frame was rendered first (the cold-render test in `craft.md` finds it), two
  exports of the same code differ by a few levels. Fix the cache; until then, A/B a change on stills rendered at the
  same times, and compare exported frames with a tolerance.
- A fix to a few shots does not need a full export: compare old and new page renders frame by frame, re-render only
  the frames that differ (`--from N --to M`), and splice them over the previous export.
- A change in code can vanish before the final pixels (a wash multiplied onto paper, a light band too faint to move a
  grey level). Swap the constant for an extreme, render one still, and measure.
- A two-bone IK that picks "the outer side" flips the elbow in one frame (60-90 px) when the hand passes its shoulder
  or the horizontal. Solve it in 3D with a pole (out, down, back) and a hand depth near the shoulder, or let the elbow
  change side only while the arm is straight; audit every joint's step per frame, not only the hand's.
- A throw that becomes a reach keeps the arm up: the follow-through settles at the top and the arm stays raised.
  Swinging it down past the hip and back up across the chest to change the elbow's side reads as the arm going round
  through the back, a broken arm. If the elbow must change side, change it while the arm is straight overhead.
- Both arms raised overhead on a child with a big head (arms shorter than head and neck) cross the face if only the
  arms move: lift the shoulders 10-20 % of the arm's length as the arms go up and tip the head back to look up; the
  hands then clear the top of the head. A follow-through that keeps the release's rate and settles at a top is an
  exponential with time constant (top - release angle) / rate; a Hermite with that start slope overshoots its top
  whenever rate x duration > 3 x (top - release angle).
- A far arm in a three-quarter view reads as coming out of the hip, the bottom or the back wherever its hand shows and
  its forearm does not. Draw it behind everything but the far leg, with the torso, shorts and near leg cut out of it,
  and audit every frame: a visible far hand needs its forearm visible (or the hand hidden too). Give the far hand a
  natural job in every pose: beside the near hand on the ground, on the far rim of an object both hands hold.
- A hand gripping something round and bigger than it (a child's hand on an apple) must stay the hand's size: four
  fingers together over the object's near front spanning about one limb width, not spread round its rim, and the
  thumb from lower on the rim, tilted up toward the fingertips (it opposes them), not lying flat or far away. A grip
  drawn as angles round the object grows with the object; compute its span in limb widths.
- Halving each joint angle of a kicked-out pose (thighs near vertical, shins out) narrows it into knock-knees. To open
  a pose less, scale the foot's offset from the hip and keep each knee on the hip-to-foot line.
- An outline traced off a raster starts wherever the trace began, so a line laid from a keyed index along it jumps
  when the shape is redrawn: rotate the traced points to start at a point the rig fixes.
- A cubic in-out ease peaks at 3x its mean speed, minimum jerk at 1.9x, smoothstep at 1.5x: a fast lift or a camera
  move on the cubic reads as a jump. Use smoothstep or minimum jerk for those.
- Additive height fields (clay) let a thick slab's edge print through a ball laid over it, a seam across a face. Lay
  thick pieces with the max of the heights.
- A cheap zoom blur: draw the frame once offscreen, then a binary cascade of two copies scaled about the zoom centre
  per pass (2^n copies, ≤ 0.7 px apart at the far corner), and lay the sharp centre back: 16-20 ms a frame.
- Blurring a whole jumping figure doubles its face. Give the body a shorter shutter and draw the head once, crisp, at
  the frame's own time.
- Chrome's canvas takes a variable font's optical size from the pixel size, so a big title gets the display cut's
  hairlines. Load the face as its own `FontFace` with `variationSettings: "'opsz' 9"` (or the size you want) and wait
  for it in `READY`.
- A stroke routine fed a NaN width can loop forever (its run never advances) and hang the page with no error: treat a
  non-finite width as a gap.
- Scratch art: a ring scratched closed in one stroke leaves a black speck where its lift meets its start; run it on a
  few px past the start. Where two scratches cross, the second dig goes down to the card and shows as a pale dot (a
  "nose" on a face): dig a face's layer toward a tint of its own crayon.
- Widening a scratched or revealed line at the same stylus speed raises each frame's reveal and the one-frame scan
  flags it: keep the area revealed per frame, not the speed (a 3.8 px line at ≤ ≈ 33 px a frame).
- An opaque stop-motion arrival (a clay lump slapped on) is a one-frame step on every tile it covers, so
  `scripts/glitch_scan.py` flags each one by construction: list those frames as contacts, and judge them on a strip.
- A feature swap (mouth, eyes, lids, a grip) done as a cross-fade reads as a ghost frame of both drawings: cut it in one
  frame, or through one drawn in-between each way. A bare cut on a big shape can trip the one-frame scan; the
  in-between fixes that too. A stop-motion change of state (a lumpy pile to a smooth ball) is never a dissolve either:
  sweep it in under the tool's path (a thumb wipe), keeping some seams as creases.
- A slow fade or swell over a large area that is still running in a hold quantises to one-level steps over the whole
  area and raises fine flicker (1.5x measured): end it before the hold.
- Detail finer than a pixel at 1x (fingerprint ridges) only shimmers as the figure breathes: fade it in with the
  camera's zoom. Scratch art: the wax gives way ≈ 0.3 px beyond the stylus, so a black hairline needs ≈ 1 px nominal,
  and features drawn over a hatched field (eyes, mouth) need a clean margin that moves with them.
- A ground reserve drawn a pixel larger than a shape whose wash dries inward leaves a 1-2 px strip of bare paper round
  every shape (a sticker's matte fringe). Run the ground 1-2 px under the shape's edge and let paper show only in a few
  short breaks. Measure it: the luma across the edge must not rise above both sides.
- Parts of one piece painted one by one show every part's rim, shade and lit sliver inside the union (a capsule
  puppet). Paint the union once (nonzero paths with consistent windings), with lines only where one piece crosses in
  front of another. A wash run past the ink onto a transparent sheet (a shutter's layer) multiplies over nothing and
  leaves a pale fringe: stop it inside the ink's outer half.
- Averaging shutter copies in an 8-bit canvas biases dark tones (each blend rounds down): average in
  `getContext('2d', { colorType: 'float16' })`.
- `in`/`xor`/`copy` compositing on a scratch canvas clears every pixel the canvas allows: clip it to the box you use, and
  clear a few px wider, because a sub-rect `drawImage` under a scaled transform samples a pixel or two past the rect.
- Lowering a shoulder's root does not keep an IK elbow off the head: with the bend side fixed, a raised target swings
  the elbow toward it. Audit the elbow's distance from the head every frame, and route the hand's keys out behind.
- Scratch art reverses engraving: crowding scratches toward the shade lightens it; thin them there instead.
- A scratched globe left mostly black on its shade side reads unfinished ("incomplete and poor"). Scratch the night
  side too, at nearly the lit side's line density (a floor of 0.9) with thinner strokes, so the land and sea read all
  the way round. It took the black share of the shade third from 55 % to 30 %.
- Stitches sewn round a figure (a hug drawn as thread) read as ropes tying it up, more so the thicker they are. Keep
  the thread fine (about 3.5 px at 1080p; 6-7 px reads as rope), sew it on the word, fade it after, and let the
  gesture carry the hug: the arms tighten a few px and the figure presses into the felt.
- A coloured-pencil sea hatched in long strokes with gaps between them reads as pale streaks. Lay short strokes that
  overlap at 0.8x their width (22-24 px long, ±6°), denser than the land's.
- A composition note on a scene whose motion is physics (a small Earth on its orbit in an empty frame) is answered by
  the camera, not by moving the object: push in after the action, hold, pull back to reveal what comes next (the Sun),
  at 1x at both cuts so the passages hold. Draw through the camera's transform, check the extremes stay in frame, and
  keep the move out of the line that names the next action, or the frame's slide reads as the object moving.
- A scratch canvas reused across frames keeps its state: an `imageSmoothingQuality` set on it for one frame changed a
  rotated layer on the next (up to 17 levels, a frame that depended on history). Copy the frame context's smoothing
  state onto the sheet each frame, and wrap your own settings in save/restore.
- A CSS `filter = 'blur(...)'` on a full-frame scratch canvas costs about 35 ms a frame: bake the soft mask once (at 2x)
  and draw it through the transform.
- Scratch art: concentric rings on a face read as a target, and the black between them as features. Scratch a face in
  one even direction (as a child fills a shape), a second pass between the strokes for the light, and keep a clean
  black margin round each feature; audit every frame for black crossing a feature.
- A shoe drawn as an oval in front of the leg leaves the shin's end showing at the heel or under the sole in some
  poses: make the shoe one piece with a cuff round the ankle, end the shin inside it, and audit every leg-frame for shin
  pixels outside the shoe.
- An arm whose outline starts at the shoulder joint shows bare skin over the shoulder whenever the arm lifts: make each
  sleeve a band round the shoulder joint and down the upper arm to the hem, a little wider than the arm, joined to the
  shirt's top line, so the arm shows only out of the hem. Audit it every frame: bare upper-arm pixels above the hem
  (count the upper arm only, and stop at the hem).
- In pen and wash, a pen line across a limb at a sleeve's hem reads as a ring round the arm (closed, a washer; an open
  C, still a bracelet), and a straight pen line across the shorts reads as a cut: stop the garment's own line at the
  hem and let the paint's edge be the hem.
- A hand blended from a world key (on an object) into a shoulder-relative key while the arm is near full reach and the
  body moves pops the elbow: park the hand where the arm stays bent (on a knee) before the hand-over.
