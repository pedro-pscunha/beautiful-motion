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
| "it glitches sometimes" | one-frame pops: a stroke laid whole, a pose that snaps, a boil redrawn over a figure | `glitch_scan.py` on every export, strokes faded in behind the tip, feature swaps cut not dissolved (`techniques.md`) |
| "the letters look disconnected from the background" | a font's outline with a texture inside, revealed by a wipe | the word laid stroke by stroke in its scene's own material, on the font's skeleton |
| "the arm seems broken" / "it comes out of his hip" | a far arm behind the body in a three-quarter view, a hand with no forearm, a bare shoulder | the arm and hand traps in `techniques.md`, audited every frame |
| "raise the volume before the voice" / "the dips are too intense" | an intro far under the voice; a dip cut into the music | lift the intro and ease it under; duck instead of dipping (`sound.md`) |
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
Under a cap on how many run at once, fold two lenses into one grader (craft and colour, one score each) and give each
builder several scenes.

**Lenses** (3-4, always one whole-film lens):
- picture: craft and material; colour; composition and motion; the film's arc;
- an explainer: clarity and truth (does the audience understand it alone, is anything said or shown false);
- music: composition; performance; orchestration and sound; music against the picture;
- foley: sync; mix and subtlety; realism.

**Files** (`<project>/.work/panel/`). They carry the whole state, so a grader can be a fresh agent every round:
- `PANEL-BRIEF.md`: the film, the user's history as quotes, every path, the scale, the lenses, the grade template
  below (the project's own `BRIEF.md` stays the user's brief). When the film changes between rounds (a new scene, an
  ending), put a "From round N" section at its top with the new frame map and how earlier rounds' frame numbers map
  to it;
- `RULINGS.md`: the user's notes first, verbatim and numbered (their annotated screenshots in `.work/panel/user/`,
  each with a copy at most 1000 px wide for agents to read), then each round's numbered build list with the lead's
  verdict on each (accepted, partly, declined and why) and a "Known, not done" list for the next version;
- `PANEL-STATE.md`: scores per candidate and lens, decisions, blind labels;
- `ROUNDn.md` (the blind pick, written to the grader's folder before it opens the next file), `ROUNDn-part2.md` (the
  key, what to grade), `roundn/CHANGES-candN.md` (what changed, note by note: done, partly or declined, and what is
  still open) and `roundn-<lens>.md` (each grade as delivered);
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
2. Calibrate on the version the user graded; re-brief a grader more than 1.5 off their number in that round. Later,
   a grader past the line whose lift rests on measured fixes is not re-briefed when its verdict would be the same on
   either side of it (one lens at +1.6 after two fixes measured in the final pixels: 8.2 or 8.1, the bar met either
   way); one with no anchor of its own is not held to a stand-in's.
3. Evidence or no points: every point off cites frames or times and a concrete fix; a 9 names what keeps it from 10.
4. Blind pick first: show the best graded candidate and the new one as X and Y (a coin decides), and get the pick
   written down before the change list is read. Expect it to be weak: graders recognise the baseline, and a grader
   that runs its scripts first knows the candidate by its numbers. Say "pictures before scripts". It is not blind at
   all when the two differ visibly or in length (a new scene, an added ending, the very change the user asked for,
   which the graders have just read in the rulings): in eight rounds of one film every lens picked the newer
   candidate every time. Keep it for subtle changes, and say when it could not be blind.
5. On colour and craft, offer 2-3 variants of a contested plate.
6. A fresh, cold grader on the final candidate catches a panel gone soft on its builder.

**Loop.**
1. Panel brief, rulings, freeze the current version as cand0, start the graders.
2. Round 1 calibrates and grades cand0. Merge the notes into numbered rulings.
3. Build the next candidate; report point by point against the rulings (done / tried and dropped with the number /
   refused with the reason). Reread the rulings right before building and before sending: a candidate that skips a
   note is not graded.
4. Freeze, give the round to every grader at once (the same graders, or fresh ones that read the files), and build
   nothing until every grade is in. Tell them to grade against the scale and the user's notes, not only against the
   last candidate: a point fixed is not a point earned while the result is still weak. Put the lead's own doubts in
   the round file as questions to confirm or reject with evidence, never as findings.
5. Bar: the median of the lenses at 8 or more, and no lens under 7.
6. Stop after the number of rounds the user agreed (6 is a good default); report where it stalled and the measured
   reason. After a delivery, more notes and a request to pass again get their own cap (three more rounds once); when
   it is spent, the lead and the builder check the user's notes on the frames, with no panel.
7. Dry-run the delivery while the last round grades.
8. A panel pass is not the user's approval: deliver as a new version; their grade re-anchors the scale.

**After the panel: the user's own notes.** A small note (an angle halved, a line removed, a hand redrawn) is faster
done by the lead, who holds the code, than briefed to a builder. Show a before/after board before any export (the
frame at 1x and the detail at 3x, side by side and labelled), re-render only the frames that change once the user
approves it, and deliver a new version.

**Lessons that saved rounds.**
- Check a grader's reading against the frames before ruling. Region means mislead: a mean over a patterned area can
  average two colours into a third that is not there; a colour "inside" a shape can be the ground showing between
  thin parts; a motion measure can flag something still being built (measure late in the hold); the centroid of an
  object leaving the frame slows as the edge clips it, which reads as a false speed kink.
- Check a builder's report on the frames too, before it reaches the change list: a "wave" a builder reported under a
  fade moved the hand by under 8 px, too small to read.
- Every fact a prompt or a brief gives a grader (each scene's colour combination, frame ranges, the film's length)
  comes from the code and the current files, never from a brief's table or the last round's prompt: a table left at
  an earlier pick (scene 7's first chord, changed in round 1) reached a colour grader six rounds later, and a prompt
  copied forward carried it two rounds more.
- Check a change reaches the final pixels before building: copy the page, swap the constant for an extreme, render one
  still, measure. A wash multiplied onto paper, an ink composited by multiply, or a light band too faint to move a grey
  level can all look right in code and change nothing.
- Compare candidates against a baseline exported in one run; renders that depend on what came before differ between
  exports.
- Constants move colour and motion; they do not move craft. Once craft's tells are shapes drawn wrong, plan redraws.
- A builder subagent kept across rounds grows its context with every image it reads, and near 600k-900k tokens every
  request fails (API 499, client closed). Have builders read images small (stills at `--scale 0.5`, crops under
  800 px, strips under 1600 px wide, never the same image twice), keep their state in files (reports, a state note,
  the workspace), and replace a builder past ~500k tokens with a fresh one that reads a takeover brief. Its context
  size is the last `usage` (input + cache read + cache creation) in its `subagents/*.jsonl` transcript.
- Each builder works in its own copy of the page and edits only the files named in its brief; the lead merges and
  checks that the merged page renders each builder's frame range identically to the builder's own export (max
  difference 0), and the untouched scenes identically to the last candidate.
- Some agent harnesses refuse report files from a subagent: ask for the report in its final message and file it
  yourself. Before re-sending a request a builder seems to have missed, read its latest report and state file: a
  request that crosses its answer starts a second pass that rewrites its outputs while you merge them.
- A fix for one lens can take from another (lifting a ground for colour can flatten its motion and its texture):
  re-run the other lenses' measures on the plates you touched.
- A ruling that sets a recipe by count and size (patches × dabs × px) also sets how much of the frame it covers. Work
  that area out against the role it plays before ruling: 96 dabs of 2-7 px fixed a stamped carpet of flowers and left
  the meadow empty, against the user's "more joyful". The user's notes outrank a round's numbers.
- A ruling that encodes a physical quantity in colour or size must name the true reference: "fade the pull with
  distance" keyed to the child (not the Earth's centre) showed a weaker pull at the surface, a false science point.
- A scene too heavy for one builder can be split between two on disjoint modules (each in its own workspace, neither
  renaming what the other uses); the lead merges the module sets, rebuilds, and passes each the other's findings.
