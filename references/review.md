# Review: judges, adversarial reviewers and grading panels

Use other agents as critics. They read files and images and run measurements; they do not edit the project, and they
never read `.env`. Give every critic absolute paths, the brief, the user's own notes so far, what to judge, and the
exact shape of its answer. If you cannot spawn subagents, run each critic as a fresh session that reads only the
files, or do the review yourself as a separate pass, and say which.

## The quality bar (notes a director gives, and what they usually mean)

| Note | What it meant | Fix |
|---|---|---|
| "this is still" | a shot held a finished image | build in the medium's idiom, then a slow continuous life (`techniques.md`) |
| "it's flickering" | thin lines or boil aliasing, a weave in the grade | supersample thin work, no boil on geometric edges, no grade weave |
| "the background looks digital" | vector decoration around the subject | paint ground and subject as one picture |
| "it looks like a sticker" | a shadow under something drawn into its ground, a hard rim light | shadows only where things stand proud |
| "the colours look random" | palettes picked shot by shot, or a hue from outside the shot's combination | one Wada combination per shot, nothing outside it but neutrals (`colour.md`) |
| "pixelated / blotchy" | coarse grain, 8-bit grading, heavy compression in dark areas | grade in 16-bit, fine grain (`grain.py`) encoded at CRF 23 or lower with `-tune grain`, a lower CRF for dark films |
| "a stripe at the edge" | a camera move bared the page | overscan matched to the move, check all four edges |
| "the music is too low" / "the effects are too loud" | first-guess levels | measure: music clearly under the voice, effects well under the music |
| "too much reverb on the voice" | any reverb on narration | a dry voice chain |
| "the line plays over the next image" | a long line pushed later lines off their shots | one short line per shot, placed on its own image |
| "don't exaggerate" | effects added for their own sake | restraint: fewer notes, softer, truer to the medium |

## Judge (one opinion on a finished cut)

One read-only critic. It extracts frames, measures the audio, says what it could not check, and returns
Critical / Major / Minor findings concrete enough to implement (which shot, which frames, which colours, what to draw).
Apply the findings as a new version.

## Adversarial reviewer (a new animation or a proposal)

Before the user sees an ending, a reorder or a new idea: a reviewer told to find what is wrong. It steps through
frames, builds flip-books and phone-size sheets, measures per-frame changes and the music's onsets, reads the code for
hidden assumptions, and ends with a numbered fix list. Fix, then re-check only the Critical items.

## Grading panel (raise a grade)

When the user gives a grade out of 10, or asks to raise one: graders, one lens each, grade frozen candidates in rounds
while a builder improves them, until the bar.

**Roles.** A team lead (rulings, conflicts, freezing, the bar), a builder (whoever knows the code; often the lead), and
3-4 graders. Ask the user how many subagents and which models; give the most subjective lens the strongest model.

**Lenses** (3-4, always one whole-film lens):
- picture: craft and material; colour; composition and motion; the film's arc;
- music: composition; performance; orchestration and sound; music against the picture;
- foley: sync; mix and subtlety; realism.

**Files** (`<project>/.work/panel/`). They carry the whole state, so a grader can be a fresh agent every round:
- `PANEL-BRIEF.md`: the film, the user's history as quotes, every path, the scale, the lenses, the grade template
  below (the project's own `BRIEF.md` stays the user's brief);
- `RULINGS.md`: the user's overrides first, then each round's numbered build list;
- `PANEL-STATE.md`: scores per candidate and lens, decisions, blind labels;
- `ROUNDn.md` and `roundn-<lens>.md`: what to grade, and each grade as delivered;
- `candN/`: frozen candidates (`uv run <skill>/scripts/freeze.py .work/panel/candN`). Graders run
  `uv run <skill>/scripts/freeze.py --check .work/panel/candN` before and after grading. Never rebuild a graded
  folder; a fix is a new letter.

**The grade template** (in `PANEL-BRIEF.md`, so every grader answers the same way):
1. The blind pick (when asked): X or Y, and why, written before reading the change list.
2. The score for the lens, out of 10, to one decimal.
3. What keeps it from one point more.
4. Each point off: the frames or times, what is wrong, and a concrete fix.
5. What the grader could not check, and why.

**Scale.** 3 amateur; 5 competent with problems a professional flags; 8 a professional pass a director signs off
without notes; 10 indistinguishable from a top-tier hand-made short. If the user gave a number, that version is the
anchor.

**Taste devices.**
1. The user's own notes are the canon: graders read them before grading.
2. Calibrate on the version the user graded; re-brief a grader more than 1.5 off their number.
3. Evidence or no points: every point off cites frames or times and a concrete fix; a 9 names what keeps it from 10.
4. Blind pick first: show the best graded candidate and the new one as X and Y (a coin decides), and get the pick
   written down before the change list is read. Expect it to be weak: graders recognise the baseline, and a grader
   that runs its scripts first knows the candidate by its numbers. Say "pictures before scripts".
5. On colour and craft, offer 2-3 variants of a contested plate.
6. A fresh, cold grader on the final candidate catches a panel gone soft on its builder.

**Loop.**
1. Panel brief, rulings, freeze the current version as cand0, start the graders.
2. Round 1 calibrates and grades cand0. Merge the notes into numbered rulings.
3. Build the next candidate; report point by point against the rulings (done / tried and dropped with the number /
   refused with the reason).
4. Freeze, give the round to every grader at once (the same graders, or fresh ones that read the files), and build
   nothing until every grade is in.
5. Bar: the median of the lenses at 8 or more, and no lens under 7.
6. Stop after an agreed number of rounds (6 is a good default); report where it stalled and the measured reason.
7. Dry-run the delivery while the last round grades.
8. A panel pass is not the user's approval: deliver as a new version; their grade re-anchors the scale.

**Lessons that saved rounds.**
- Check a grader's reading against the frames before ruling. Region means mislead: a mean over a patterned area can
  average two colours into a third that is not there; a colour "inside" a shape can be the ground showing between
  thin parts; a motion measure can flag something still being built (measure late in the hold).
- Check a change reaches the final pixels before building: copy the page, swap the constant for an extreme, render one
  still, measure. A wash multiplied onto paper, an ink composited by multiply, or a light band too faint to move a grey
  level can all look right in code and change nothing.
- Compare candidates against a baseline exported in one run; renders that depend on what came before differ between
  exports.
- Constants move colour and motion; they do not move craft. Once craft's tells are shapes drawn wrong, plan redraws.
- A fix for one lens can take from another (lifting a ground for colour can flatten its motion and its texture):
  re-run the other lenses' measures on the plates you touched.
