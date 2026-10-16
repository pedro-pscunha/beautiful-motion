# Finish and deliver

## Encode

From the exported frames (`f0000.png` ...). `-framerate` must be the page's `TIMELINE.fps`, and the width and height
must be even (yuv420p). The colour options convert with the BT.709 matrix and tag the file (`setparams` tags the frames, which recent
ffmpeg reads; the `-color*` options cover older builds), so players show the palette you drew. Without them ffmpeg
converts with BT.601 and writes no tags, and every colour shifts on playback.

```
ffmpeg -framerate 24 -i .work/v1/frames/f%04d.png -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709" -c:v libx264 -preset slow -crf 16 -colorspace bt709 -color_primaries bt709 -color_trc bt709 -movflags +faststart .work/v1/picture.mp4
```

- CRF 14-18; the lower end for dark or grainy films (dark gradients block first).
- A master for archive or a client: ProRes 422 HQ in a `.mov` (an mp4 cannot hold ProRes):
  ```
  ffmpeg -framerate 24 -i .work/v1/frames/f%04d.png -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv422p10le,setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709" -c:v prores_ks -profile:v 3 -colorspace bt709 -color_primaries bt709 -color_trc bt709 .work/v1/master.mov
  ```
- Grade, if any, in 16-bit, on the frames, before the 8-bit encode. Light grain at most (below); no weave or shake in
  the grade.
- In a Windows `.bat` file, `%04d` must be written `%%04d`; in PowerShell and bash it is fine as is.

## Film grain (optional, before the encode)

A fine grain makes a drawn film read as printed rather than rendered, and it dithers smooth gradients so they do not
band in 8 bits. Done badly it is the "pixelated / blotchy" note: coarse grain, or grain the encoder turns into blocks.
`grain.py` adds it to the exported frames; then encode those frames instead, with `-tune grain`:

```
uv run <skill>/scripts/grain.py .work/v1/frames .work/v1/grain
ffmpeg -framerate 24 -i .work/v1/grain/f%04d.png -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709" -c:v libx264 -preset slow -crf 23 -tune grain -colorspace bt709 -color_primaries bt709 -color_trc bt709 -movflags +faststart .work/v1/picture.mp4
```

- The grain is luma only (hue and saturation stay; nothing lands on the colour planes, which 4:2:0 halves into
  blotches), fine (about 0.8 px, with nothing left at blotch scale), zero-mean (region means do not move), weaker in
  deep shadows and near white, and seeded by the drawing, so a re-run gives the same pixels.
- `--amount` is the grain's std in 8-bit code values in the midtones: 2.8 (the default) is subtle but visible at 1:1
  and on a phone; 4 and up reads as noise. `--size 0.8` suits a 1080 px film; scale it with the short side (0.8 for
  1920x1080 too). `--on 2` (the default) gives each drawing of a film on 2s one grain, so a held pair stays identical;
  `--on 1` gives every frame a new one.
- A grade that runs in ffmpeg can stream its 16-bit frames through the grain instead of writing PNGs twice (about
  4-9 MB a frame each time at 1080p): `--raw <W>x<H>` reads raw `rgb48le` frames on stdin and writes them grained to
  stdout, in order, as in `ffmpeg … -f rawvideo -pix_fmt rgb48le - | uv run <skill>/scripts/grain.py --raw 1920x1080 --start 1 --on 1 | ffmpeg -f rawvideo -pix_fmt rgb48le -s 1920x1080 -framerate 30 -i - …`.
  `--start` is the number of the first frame (the seed), so the pixels equal the folder mode's for frames with those
  numbers.
- Keep the encode at CRF 23 or lower, with `-tune grain`. Measured on a 1080 px film on 2s: above that, x264 turns the
  grain into block-sized mottle that flickers (24 px tile flicker, grained against clean at the same settings: 1.0x at
  CRF 23, 1.1x at 24, 1.4x at 26; 1.1-1.3x at CRF 24 without `-tune grain`). Grain costs bitrate: that film took
  8.4 Mbit/s at CRF 23 with grain, 3.6 Mbit/s at CRF 24 without.
- Every re-encode removes grain. Build the 9:16 from `.work/v1/grain` with the same `-crf 23 -tune grain`, never from
  an mp4. A messaging app re-encodes again and keeps about half of it (simulated: 720 px, 1.5 Mbit/s); a file sent as
  a document is not re-encoded.
- Check that it adds no flicker, on a nearly still stretch (the fine scale rises by design):
  `uv run <skill>/scripts/flicker.py .work/v1/frames 2.5 3.5 --vs .work/v1/grain`
  On a film with its own texture the tile ratio stays at or under 1.1x. On flat colour the base is near zero, so the
  ratio can read high on a change of a few hundredths of a code value: there, check that the tile max (the worst
  single flip) is unchanged.
  For the delivered file, decode both encodes to frames (`ffmpeg -i <file>.mp4 -vf "scale=in_color_matrix=bt709:in_range=tv:flags=accurate_rnd+full_chroma_int,format=rgb24" -start_number 0 <dir>/f%04d.png`)
  and compare those the same way.
- Not grain: a weave or shake, a flickering exposure, halation (a camera's glow around light sources, foreign to a
  drawn film), or a second vignette over a film that already has one.

## Mux

Add the final mix without re-encoding the picture, into `out/` (create it once: `mkdir out`). `apad` with `-shortest` ends the audio exactly with the picture,
whether the mix is a little shorter or longer:

```
ffmpeg -i .work/v1/picture.mp4 -i .work/v1/mix-final.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 256k -af apad -shortest -movflags +faststart out/<name>-v1.mp4
```

A silent film needs no mux (copy `picture.mp4`). If a platform refuses a file with no audio track, add silence:
`-f lavfi -i anullsrc=r=48000:cl=stereo` as the second input, with the same command.

## 9:16 from a square or 16:9 film

Do not just crop: the film full width on a page of the film's own tone, and the words as captions in the empty band,
clear of the top ~250 px and the bottom ~400 px where the apps draw their interface. The command below scales the
film to 1080 wide and places it at y = 250: a square film fills 250-1330 (captions in 1330-1520), a 16:9 film fills
250-858 (captions below it).

Render the captions as their own page (the same render contract, 1080x1920, a transparent canvas, the text from
`lines.json`) and export its frames. Then build the vertical cut from the film's own frames, so the picture is encoded
once, and copy the sound from the square delivery (`"2:a?"` keeps a silent film silent; quote it, since zsh reads `?`
as a wildcard):

```
ffmpeg -framerate 24 -i .work/v1/frames/f%04d.png -framerate 24 -i .work/v1/captions/f%04d.png -i out/<name>-v1.mp4 -filter_complex "[0:v]scale=1080:-2,pad=1080:1920:0:250:color=0x1b1714[bg];[bg][1:v]overlay=0:0:format=rgb:shortest=1,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709[v]" -map "[v]" -map "2:a?" -c:v libx264 -preset slow -crf 16 -colorspace bt709 -color_primaries bt709 -color_trc bt709 -c:a copy -movflags +faststart out/<name>-v1-9x16.mp4
```

Give every image input its own `-framerate`, equal to the film's, or the vertical cut drifts out of sync.

## Verify the delivered file

- Frame count and duration equal the page's (`TIMELINE.duration * fps` frames):
  `ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=nb_read_frames:format=duration -of default=nw=1 out/<name>-v1.mp4`
- The audio is present, at the delivery loudness and true peak: `uv run <skill>/scripts/loudness.py out/<name>-v1.mp4`.
- The colour tags are there: `ffprobe -v error -select_streams v:0 -show_entries stream=color_space,color_primaries,color_transfer -of default=nw=1 out/<name>-v1.mp4`
  says `bt709` three times.
- Checksums for what you hand over: `uv run <skill>/scripts/freeze.py --sums out` (writes `out/SHA256SUMS`).

## Versions

Every change is a new version (`film-v12.mp4`); never overwrite a version the user has seen. Keep a short notes file per
version: what changed and why, what was measured, what was not checked.
