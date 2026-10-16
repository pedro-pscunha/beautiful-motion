# Sound: voice, music, foley, mix

You cannot hear. Measure everything (loudness, the voice's margin, RMS per 0.5 s, onsets), say "needs your ears" with
every delivery, and give the user numbers to react to. Work at 48 kHz WAV until the final encode.

## Voice first

The voice sets the timing of the film.
- Write lines short (3-8 words for a poem, one idea per shot) and read slowly; give a comma its breath.
- With ElevenLabs (`ELEVENLABS_API_KEY`): choose a voice by the user's pick, or by measured pitch and clarity; read
  the current docs for the model and its settings; generate each line as its own file. Keep the delivery even:
  no whispering or style effects on single lines unless the brief asks.
- Place each line on its own shot, starting a beat after the cut and ending before the next one. The timings live in
  one file, `<project>/audio/lines.json`, read by `voice_track.py`, `voice_margin.py` and the captions:
  `[{"text": "The sun comes up.", "file": "audio/lines/01.wav", "start": 2.05, "end": 3.13}, ...]` (seconds on the
  film's clock).
- A dry voice: no reverb; a gentle de-esser if the sibilants are hot; check the 6-16 kHz band for fizz.

Lay the lines onto one voice track: `uv run <skill>/scripts/voice_track.py audio/lines.json audio/voice.wav`. It folds
each line to mono (a stereo recording with the mic on one side: set `"channel": 0` or `1` in its entry), places it at
its start, warns about overlaps and lines that run past their end, and writes a stereo 32-bit float WAV with the voice
at full level in both channels. Mixes and stems stay 32-bit float WAV (`pcm_f32le`): a sum can go over full scale,
which float keeps and normalisation brings down, where 16- or 24-bit would clip silently.

## Music

- The source is what the user chose at the brief: their own or a licensed track, a library track, ElevenLabs Music,
  Higgsfield (Seed Audio), Suno, or a score written in code. Generated music: ask for the length of the film, the tempo
  you cut to, and instrumental (no vocals) under a voiceover; ElevenLabs Music v2 can build it section by section to
  the shots and regenerate one section later. Record the prompt, model and date next to the file.
- Measure its beats and downbeats and cut the picture on them, or compose to the picture's grid. A beat list in a few
  lines:
  `uv run --with librosa python beats.py music.wav`, where `beats.py` loads the file with `librosa.load`, calls
  `librosa.beat.beat_track(y=y, sr=sr, units='time')` and prints the tempo and the beat times.
- When you write the score yourself (MIDI rendered through an instrument), keep each part's timing deterministic: if
  timing humanisation uses a random stream, give each part its own stream, so changing one part's ending does not move
  every other part's notes.
- Changing only the end: re-render only the parts whose notes changed, and replace only the span that holds the change,
  joined where the part is silent or both renders agree. Prove it with a sample diff: the voice and effects identical,
  the music different only from the change on.

## Foley

Sparse: a sound only where a hand works (the chalk scratch, the needle, the stamp). Real recordings beat generated
ones for realism; generated effects need cutting to the action and checking for clicks. Pitch nothing to the music's
key unless you measured the key.

## Mix

The voice on top, the music under it and ducked while a line plays, the effects well under the music. `normalize=0`
keeps every level as set (amix otherwise divides by the number of inputs); `pan` keeps a mono voice at full level in
both channels (a voice.wav from `voice_track.py` already is); `aformat` makes the music and effects stereo whether they
came mono or stereo; `apad` keeps the ducking key running after the last line, or the music
would stop where the voice track ends. `<duration>` is the film's length in seconds, frames / fps from `.work/v1/frames/timeline.json` (6.0 for the
starter): the mix ends with the picture, so the
loudness you normalise is the loudness you deliver. A music track longer than the film needs an ending: cut it at a
phrase end, or fade its last bars on its own chain (`afade=t=out:st=4.5:d=1.5` before `volume`).

```
ffmpeg -i audio/voice.wav -i audio/music.wav -i audio/foley.wav -filter_complex "[0:a]pan=stereo|c0=c0|c1=c0,asplit=2[v][k];[k]apad[key];[1:a]aformat=channel_layouts=stereo,volume=-10dB[m];[m][key]sidechaincompress=threshold=0.03:ratio=4:attack=30:release=500[md];[2:a]aformat=channel_layouts=stereo,volume=-16dB[f];[v][md][f]amix=inputs=3:normalize=0:duration=longest[mix]" -map "[mix]" -t <duration> -ar 48000 -c:a pcm_f32le .work/v1/mix.wav
```

Then measure, in this order:

1. The voice on every line: `uv run <skill>/scripts/voice_margin.py audio/voice.wav --mix .work/v1/mix.wav audio/lines.json`.
   The speech band (300 Hz-8 kHz) of the voice against everything else; aim at 8 dB or more on every line, and
   look at every "weak" window (a word the bed may mask). Fix by lowering or thinning the bed there, not by pushing
   the voice into the limiter. (`--mix` works here because this mix is a plain sum of the voice and the rest.)
2. Loudness to the delivery target: `uv run <skill>/scripts/loudness.py .work/v1/mix.wav --normalize .work/v1/mix-final.wav`
   (-14 LUFS, -1.5 dBTP before the AAC encode; check the platform's own target). It says whether the gain was linear;
   a linear gain keeps the voice margins measured in step 1.
3. The music runs to the end: `uv run <skill>/scripts/levels.py .work/v1/mix.wav audio/music.wav --every 1`. From
   one second after the last line to the end, the mix sits about the music's `volume` (10 dB here) under the music
   file; 20 dB or more under it means the music was cut. A row that reads "(ended)" for the mix before the film's
   end means `-t` is wrong.
4. After the mux, the delivered file itself: `uv run <skill>/scripts/loudness.py out/<name>-v1.mp4` (-14 LUFS,
   true peak at or under -1 dBTP). Measure what you deliver, not the mix project.
