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
- Grade, if any, in 16-bit, on the frames, before the 8-bit encode. Light grain at most; no weave or shake in the grade.
- In a Windows `.bat` file, `%04d` must be written `%%04d`; in PowerShell and bash it is fine as is.

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
