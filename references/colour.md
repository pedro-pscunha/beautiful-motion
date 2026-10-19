# Colour: Sanzo Wada's dictionary, by default

Use Sanzo Wada's *A Dictionary of Color Combinations* for every film by default: one of its numbered combinations
per shot. It gives the film one coherent, tested family of colours instead of ad-hoc picks, and each combination was
composed so its colours work together. Use another source (a painting, a print tradition, a brand palette) only when
the brief or the user asks for it.

At the brief, propose two or three combinations for the film's mood, by number and with their colour names, as the
starting point for the look. The stills then test them on the material.

## The book

- Sanzo Wada (和田三造, 1883-1967) was a Japanese painter, art teacher, costume designer for film and theatre, and
  kimono designer. In 1927 he founded the Japan Standard Color Association, which became the Japan Color Research
  Institute.
- *Haishoku Sōkan* (配色総鑑, a compendium of colour combinations) is his original work: six volumes, published by
  Hakubisha, Tokyo, in 1933-1934.
- *A Dictionary of Color Combinations* (配色事典, *Haishoku Jiten*), Seigensha, Kyoto, is a selection from that work:
  348 numbered combinations of 2, 3 or 4 colours, drawn from 159 named colours, in Japanese and English
  (ISBN 978-4-86152-247-5; catalogued in Japan in 2010, sold in English from 2011). A second volume (Seigensha, 2020,
  ISBN 978-4-86152-772-2) reprints two of his later works.
- The numbers 1-348 are the book's own. "Wada 124" finds the same page for anyone who has the book.

## The open data

- `colors.json` in github.com/mattdesl/dictionary-of-colour-combinations: the 159 colours, each with its name, the
  book's CMYK values, sRGB and hex, Lab (D50), its chapter, and the numbers of the combinations that use it. Inverted,
  that gives the 348 combinations.
- Licence: MIT (copyright 2020 Matt DesLauriers; the data was first compiled by Dain M. Blodorn Kim, also MIT). The
  skill does not bundle the file: `scripts/wada.py` downloads it once per project, pinned to one commit and checked by
  SHA256, to `.work/wada/colors.json`. If you redistribute the file itself, keep its licence notice.
- The hex values are a profile conversion of printed ink (U.S. Web Coated SWOP to sRGB). They are close to the book,
  not identical: judge the colours on screen, on the material.

## The rules

1. **One combination per shot, plus neutrals.** Its 2-4 colours carry the shot. The neutrals carry the material: the
   paper, a ground's white, the ink's near-black, grout, mortar, lead. One chord per shot reads as one decision.
2. **Nothing in a shot comes from outside its combination.** You can lighten a colour toward the paper, darken it
   toward the ink, glaze it over itself or break it into its own tints: it stays in the chord. A new hue does not. A
   critic spots a stray hue at once (a leaf, a seed head, a thread), and one foreign note breaks the set.
3. **Never repeat a combination within a film.** A shot's chord is part of its identity, and a repeat reads as a
   re-run. Keep the film's list in `BRIEF.md` and pass it to `wada.py find --used`. When several agents build shots,
   the lead hands out the numbers.
4. **Write the number in the code**, next to the colours: `wada.py show` prints the line, for example
   `// Wada 124: Pale Burnt Lake #802626, Yellow Ocher #e2b540, Olive Yellow #a6a159`. Anyone can then check a shot
   against its source, and a reviewer can ask "is everything in this shot from 124?".
5. **Pick against the neighbours.** Alternate light and dark grounds, and warm and cool, from cut to cut, so every cut
   reads as a change.
6. **A world with several places** (a storybook) can give each place its own combination for its sky, light and
   clothes, over one shared combination for the ground. Keep it to those two per shot: the shared ground makes the
   places one world.
7. **A recurring object can keep one colour across the film**, the one exception besides the neutrals: the same apple
   in every scene, like a figure's black hair, keeps one red (in Lab within a few units of one lightness, chroma and
   hue), and only its material changes. Taken from each shot's combination instead, it went crimson in some shots and
   vermilion in others (hue 20-23 against 38-39), and read as different apples. Its highlights and shadows may use the
   shot's own colours.
8. **A figure's clothes part from the ground they touch.** Green shorts on green grass read as part of the grass
   (ΔE 7-14 measured). Give the garment another hue or lightness from the shot's combination, at ΔE 25 or more against
   the ground beside it (33 and 47 measured, and the note did not come back), and measure it on the frame.
9. **A colour-dictionary plate is optional.** It shows "Wada nº 124" with its swatches, set like a page of the book.
   Use it once, as an end card or in a closing grid. On every shot it reads as a caption over the picture.

## Picking: filter by numbers, then judge on the material

The numbers narrow the choice; only the material decides it.

1. **Filter.** Run the commands with the project folder as the working directory. The first run needs the network
   (60 KB); in a sandbox, ask the user to allow it. Offline: download the file by hand and pass `--data <file>`.
   ```
   uv run <skill>/scripts/wada.py show 124 206
   uv run <skill>/scripts/wada.py find --warm 1 --cool 1 --sat 0.6 --limit 10
   uv run <skill>/scripts/wada.py find --earth 2 --no-cool
   uv run <skill>/scripts/wada.py find --hue 30-58 --hue 150-260 --sat 0.6 --used 240,138
   ```
   - `show` lists each colour's hex, RGB, hue `h`, saturation `s`, Lab lightness `L`, chroma `C` and its class (warm,
     cool, earth, dark, neutral), then the comment line for the code.
   - `find` prints the combinations that pass every filter, the most chromatic first. The second command finds a
     subject that must lead (one warm, saturated colour) against a cool ground. The third finds earth tones
     (terracotta, ochre, sienna) with no cool colour. The fourth finds a joyful pair: a vivid warm yellow and a vivid
     colour far round the wheel, leaving out the two combinations the film already uses.
   - `--count 3` keeps three-colour combinations, `--dark 1` asks for a dark colour for a ground, and a hue range can
     wrap (`--hue 330-20` for reds). `uv run <skill>/scripts/wada.py find --help` lists them all.
2. **Shortlist two or three per shot, and draw each on the shot's material.** Render one still per candidate and lay
   them side by side (`sheet.py --labels "124|275"`), at full size and at phone size. Never choose from swatches:
   swatches flatten every colour into a flat chip, and materials change colour. Wax lets the paper through, glass
   glows, stone and grout grey a palette by a step, thread shines.
3. **Choose by what the material does to the colours**, then write the number in the code.
4. **Measure the frames against it**, since a critic will:
   `uv run <skill>/scripts/chord_audit.py <frame.png> <#hex> [#hex ...]`, with the combination's hexes (plus a
   recurring object's constant colour). It prints the share of the coloured pixels near each colour and the share off
   the combination, clustered by hue and place. Thin blends at the edges between two of its colours are normal (0.1 to
   3 % of the frame across one film's scenes, all of them blends); a cluster (a leaf, a sea, a thread) is a stray to
   recolour.

## Worked examples: why a combination fails on one material and works on another

- **Earth tones on pebbles.** 275 (Etruscan Red, Ecru, Madder Brown, Taupe Brown) looked right on paper and went muddy
  as a pebble floor. Its only strong colour is a red at 64 % saturation, and stone and grout grey everything a step.
  124 (Pale Burnt Lake, Yellow Ocher, Olive Yellow) won on stone: the ochre stays bright beside the dark lake red, and
  the olive reads as stone, not as paint.
- **A warm textile.** 206 (Corinthian Pink, Golden Yellow, Cinnamon Rufous) kept the golden subject the brightest thing
  on the cloth. 249 (Hay's Russet, Ecru, Olive Ocher, Dark Medici Blue) read cool and grey on linen: on a woven ground
  the blue-grey wins.
- **A sunflower** needs a vivid yellow, a true leaf green and an earth that glazes to near-black for the seed head:
  319 (Raw Sienna, Apricot Yellow, Yellow Orange, Cossack Green). 278 has the yellows and the greens but no brown, so
  its seed head read green.
- **A joyful pebble floor.** 170 (Rosolanc Purple, Orange Yellow, Red Violet) read plum and moody in every mortar.
  240 (Fresh Color, Yellow, Cerulian Blue) read bright: coral pebbles, a yellow subject, a cerulean edge.
- **A neutral changes the palette.** A pale lime mortar keeps a light palette fresh. It also shows between loosely
  set stones and washes a deep palette out at phone size.
- **Two close candidates.** Make both render from one build (a `?pal=1` / `?pal=2` switch read by the page), show
  both, and when one is chosen, hard-code it and delete the switch and the other palette.
