# Sound: voice, music, foley, mix

You cannot hear. Measure everything (loudness, the voice's margin, RMS per 0.5 s, onsets), say "needs your ears" with
every delivery, and give the user numbers to react to. Work at 48 kHz WAV until the final encode.

## Voice first

The voice sets the timing of the film.
- Write lines short (3-8 words for a poem, one idea per shot) and read slowly; give a comma its breath, and leave a
  breath before each line (1-2 s for young children, who look at the picture while nobody talks).
- With ElevenLabs (`ELEVENLABS_API_KEY`): choose a voice by the user's pick, or by measured pitch and clarity; read
  the current docs for the model and its settings. Generate the whole script as one take with word timestamps and cut
  it into lines at the silences between words (one take keeps the performance even), or each line as its own file.
  Keep the delivery even: no whispering or style effects on single lines unless the brief asks.
- Place each line on its own shot, starting a beat after the cut and ending before the next one. The timings live in
  one file, `<project>/audio/lines.json`, read by `voice_track.py`, `voice_margin.py` and the captions:
  `[{"text": "The sun comes up.", "file": "audio/lines/01.wav", "start": 2.05, "end": 3.13}, ...]` (seconds on the
  film's clock).
- The page takes its line and word times from a file a script writes from `lines.json`, never edited by hand, and
  keys each cue to its word: a re-laid voice then moves every cue with it (`techniques.md`, traps).
- A dry voice: no reverb; a gentle de-esser if the sibilants are hot; check the 6-16 kHz band for fizz.

Lay the lines onto one voice track: `uv run <skill>/scripts/voice_track.py audio/lines.json audio/voice.wav`. It folds
each line to mono (a stereo recording with the mic on one side: set `"channel": 0` or `1` in its entry), places it at
its start, warns about overlaps and lines that run past their end, and writes a stereo 32-bit float WAV with the voice
at full level in both channels. Mixes and stems stay 32-bit float WAV (`pcm_f32le`): a sum can go over full scale,
which float keeps and normalisation brings down, where 16- or 24-bit would clip silently.

## Music

- The source is what the user chose at the brief: their own or a licensed track, a library track, ElevenLabs Music,
  Higgsfield (Seed Audio), Suno, or a score written in code. Generated music: ask for the length of the film, the tempo
  you cut to, and instrumental (no vocals) under a voiceover; ElevenLabs Music builds it chunk by chunk to the shots
  (`env.md`). Record the prompt, model, seed and date next to the file.
- Measure its beats and downbeats and cut the picture on them, or compose to the picture's grid. A beat list in a few
  lines:
  `uv run --with librosa python beats.py music.wav`, where `beats.py` loads the file with `librosa.load`, calls
  `librosa.beat.beat_track(y=y, sr=sr, units='time')` and prints the tempo and the beat times.
- A fixed grid first, when the voice leads and the music comes after it: choose a tempo and a meter, make every shot a
  whole number of bars and every cut a downbeat, and start each line on a subdivision (an eighth note). The film is
  then timed before any music exists, and any music, generated or written, sits on it (a 72.5 s explainer: 27 bars of
  3/4 at 67 BPM, scenes of 2 to 5 bars).
- Generated music on a fixed grid: plan one chunk per scene, each a whole number of the film's bars (a chunk is at least
  3 s, so a short last scene shares its neighbour's chunk), and make two seeds. Then check each take: its tempo and
  drift (a straight line fitted through the tracked beats), its downbeat phase (the beat position with the strongest
  low-band attacks), and, once moved so its first downbeat lands on the film's, every downbeat against the film's
  (aim at |d| ≤ 45 ms). A Music 2.5 take asked for 67 BPM held 66.99 with 44 ms of drift and needed only that shift;
  the other seed drifted 102 ms with its downbeat on beat 2. Warp only a take that fails: `rubberband --timemap`
  (`brew install rubberband`). Lay every take the same way: cut its lead-in, a 10 ms fade-in, padded or cut to the
  film's length, one gain to a fixed integrated loudness (-22.5 LUFS on one film), so each soundtrack meets the mix
  at the same level.
- Other styles on the same grid: pick each tempo so whole bars of its own meter fill one film bar (on a 67 BPM 3/4
  grid: 134 BPM 2/4 or 3/4, 89.33 BPM 4/4), so its sections still change on the cuts. A take a little off the tempo
  (89.00 for 89.33) gets one constant stretch, `rubberband -3 -t <ratio>` (the finer engine; the pitch is kept). Where
  the bass accents are too even to name the downbeat, score each candidate shift (the phase plus whole beats) by the
  music's chroma novelty within 60 ms of the cuts: the right one peaks there (on a take whose shift its bass had
  already given, it picked the same one). Track a double-time take from its own tempo: from the grid's it reads 300+ ms
  of false drift.
- When you write the score yourself (MIDI rendered through an instrument), keep each part's timing deterministic: if
  timing humanisation uses a random stream, give each part its own stream, so changing one part's ending does not move
  every other part's notes.
- Changing only the end: re-render only the parts whose notes changed, and replace only the span that holds the change,
  joined where the part is silent or both renders agree. Prove it with a sample diff: the voice and effects identical,
  the music different only from the change on.

## Foley

Sparse: a sound only where a hand works (the chalk scratch, the needle, the stamp). A film about things that move (a
children's explainer) also wants one where something falls, lands, is caught or jumps; a director asked for more of
those, and for them loud enough to hear over the music (the level is in the mix below). Real recordings beat generated
ones for realism; generated effects need cutting to the action and checking for clicks. Pitch nothing to the music's
key unless you measured the key.

When someone else picks a new scene's foley gains, give them the film's own level, not a target peak: measure the
laid foley track's loudest 50 ms RMS per scene, and check the new scene against its neighbours after you lay it. A
builder who aimed main contacts at a "−10 dB peak" laid a scene 18 dB over the rest of the film.

## Mix

The voice on top, the music under it and ducked while a line plays, the effects clear of the music where they land.
Lay `foley.wav` at the film's own level (each event's gain set when you lay it) and mix it at 0 dB, as the recipe
does: a film's effects at -16 dB under the music at -10 dB were inaudible to the viewer, and at 0 dB, 16 dB up, they
were right, the effects track's integrated loudness about 9 LU under the music's in the mix. Start there and check the
voice margins. `normalize=0`
keeps every level as set (amix otherwise divides by the number of inputs); `pan` keeps a mono voice at full level in
both channels (a voice.wav from `voice_track.py` already is); `aformat` makes the music and effects stereo whether they
came mono or stereo; `apad` keeps the ducking key running after the last line, or the music
would stop where the voice track ends. `<duration>` is the film's length in seconds, frames / fps from `.work/v1/frames/timeline.json` (6.0 for the
starter): the mix ends with the picture, so the
loudness you normalise is the loudness you deliver. A music track longer than the film needs an ending: cut it at a
phrase end, or fade its last bars on its own chain (`afade=t=out:st=4.5:d=1.5` before `volume`).

```
ffmpeg -i audio/voice.wav -i audio/music.wav -i audio/foley.wav -filter_complex "[0:a]pan=stereo|c0=c0|c1=c0,asplit=2[v][k];[k]apad[key];[1:a]aformat=channel_layouts=stereo,volume=-10dB[m];[m][key]sidechaincompress=threshold=0.03:ratio=4:attack=30:release=500[md];[2:a]aformat=channel_layouts=stereo,volume=0dB[f];[v][md][f]amix=inputs=3:normalize=0:duration=longest[mix]" -map "[mix]" -t <duration> -ar 48000 -c:a pcm_f32le .work/v1/mix.wav
```

Then measure, in this order:

1. The voice on every line: `uv run <skill>/scripts/voice_margin.py audio/voice.wav --mix .work/v1/mix.wav audio/lines.json`.
   The speech band (300 Hz-8 kHz) of the voice against everything else; aim at 8 dB or more on every line, and
   look at every "weak" window (a word the bed may mask). Fix by lowering or thinning the bed there, not by pushing
   the voice into the limiter. (`--mix` works here because this mix is a plain sum of the voice and the rest.)
   - A weak window on a line's first syllable is often the duck still opening (a sidechain keyed on the voice itself
     closes only after its attack, and a bar that enters loud on that syllable masks it): key the duck ahead of the
     voice, `[k]atrim=start=0.15,asetpts=PTS-STARTPTS,apad[key]` in place of `[k]apad[key]`. The duck stays shallow
     where the voice key sits only a few dB over the threshold; a weak window mid-line is the music swelling there.
   - The 200 ms windows hide a syllable that a music note's onset masks (a trailing "-de?", the "-me" of a word):
     measure again with `--window 0.05`. Fix it with the duck first: a lower sidechain threshold (0.012 instead of
     0.03, ratio 4) lets quiet syllables duck the bed too, and it took a busy bed from 7-12 masked runs to 0-3.
   - Do not cut dips into the music file under single syllables. A dip is heard as a hole in the music, played alone
     and under the voice too: a -20 dB dip of a third of a second inside a sustained note was. If you keep one, make it
     -3 dB or less with 0.3 s ramps.
   - A film that opens on music before the first word: if the intro sits far under the voice (10-18 dB measured), the
     listener turns it up and the voice startles them. Lift the music before the voice to a few dB under the lines'
     loudness and ease it down along a smoothstep over about 1.2 s, starting about 0.5 s before the first word. On the
     music's chain, before its `volume`:
     `asetnsamples=n=240,volume=eval=frame:volume='pow(10,X*(1-(3*pow(S,2)-2*pow(S,3)))/20)'`, where X is the lift in
     dB and each S is `clip((t-A)/1.2,0,1)`, A the first word's start minus 0.5. A solo piano needed +6 dB to sit 5 dB
     under the lines, a very soft composed intro +15 dB to sit 9 under; the first syllable can still sit low while the
     music eases down (0.9 dB measured).
   - Some directors want no ducking and no dips at all, the music at one level under the voice. It is their call: mix
     it (`ratio=1` turns the sidechain off), measure, and report the lines under 8 dB rather than refusing it. On one
     film that left 2 to 5 of 19 lines under 8 dB, depending on the soundtrack, the softest at 4.2 dB.
2. Loudness to the delivery target: `uv run <skill>/scripts/loudness.py .work/v1/mix.wav --normalize .work/v1/mix-final.wav`
   (-14 LUFS, -1.5 dBTP before the AAC encode; check the platform's own target). It says whether the gain was linear;
   a linear gain keeps the voice margins measured in step 1.
   When it reports "dynamic: loudnorm compressed it" (a speech-led mix: the voice's syllables are its peaks), use a
   static gain into a 5 ms true-peak limiter instead, the gain searched on the limited result until -14.0 LUFS:
   `ffmpeg -i mix.wav -af "volume=<G>dB,alimiter=limit=0.79:attack=5:release=80:level=false" mix-final.wav`,
   then measure and adjust G (each step moves less than G, as the limiter takes part of it). A single-band
   limiter turns the whole sum down together, so step 1's margins still hold; `voice_margin.py` on the limited
   mix against the unlimited voice reports false negatives on every line (the limited voice counts as "the rest").
3. The music runs to the end: `uv run <skill>/scripts/levels.py .work/v1/mix.wav audio/music.wav --every 1`. From
   one second after the last line to the end, the mix sits about the music's `volume` (10 dB here) under the music
   file; 20 dB or more under it means the music was cut. A row that reads "(ended)" for the mix before the film's
   end means `-t` is wrong.
4. Every other cut of the same picture (voice and effects alone, or another soundtrack) is its own mix, with its own
   gain search to -14 LUFS (a gain carried over from another mix landed 1.4 LU hot) and its own voice check (a duck
   tuned on one soundtrack left 7-12 masked runs under each of four others).
5. After the mux, the delivered file itself: `uv run <skill>/scripts/loudness.py out/<name>-v1.mp4` (-14 LUFS,
   true peak at or under -1 dBTP). Measure what you deliver, not the mix project.
