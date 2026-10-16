# Keys and the `.env` file

Ask for a key only when a step needs it, and only for the provider the user picked. The file is `<project>/.env`, kept
out of git (`.gitignore`) before anything is committed.

## How to ask

1. Say which step needs it, what it will be used for, and what it costs. Before the first paid call, get the user's
   explicit OK and a spending cap ("at most 20 images", "at most 5,000 characters of voice").
2. If `<project>/.env` does not exist yet, create it from the template (never over an existing one: that wipes their
   keys). bash: `[ -f .env ] || cp <skill>/assets/env.example .env`. PowerShell:
   `if (-not (Test-Path .env)) { Copy-Item <skill>\assets\env.example .env }`.
3. Ask the user to open `.env` in an editor, fill the one line, save, and say "done". On Windows: Notepad or VS Code,
   saved as UTF-8; not `>` or `Out-File` in PowerShell 5.1, which write UTF-16. Do not ask them to paste a key in the
   chat; if they do anyway, do not repeat it back, and suggest they rotate it.
4. Check: `uv run <skill>/scripts/check_env.py ELEVENLABS_API_KEY` prints `set` or `missing`, never the value.
5. Use it only at run time, loaded by the tool: `uv run --env-file .env <script>.py`, or `node --env-file=.env
   <script>.mjs` (Node 20.6+, which the doctor checks). Read it in code from the environment (`os.environ[...]`, `process.env...`).
6. Never open, print, cat or grep `.env` or a key variable, never put a key literal in a command, a script, a log or a
   file you hand to a critic.
7. If they would rather not use a provider, take the no-key path below.

## Which variable, for what

| Step | Variable(s) | Provider | No-key path |
|---|---|---|---|
| Generated images (a texture, a painted backdrop, a plate code cannot draw) | `HF_API_KEY` and `HF_API_SECRET` (the platform issues both; the SDK also takes one `HF_KEY="key:secret"`) | Higgsfield (Soul, Nano Banana, GPT Image, Seedream, FLUX...) | draw it in code; the user's own photos or scans |
| Generated images, another provider | `OPENAI_API_KEY`, `GEMINI_API_KEY`, `FAL_KEY`, `REPLICATE_API_TOKEN` | OpenAI, Google (Imagen), fal, Replicate | as above |
| Voiceover | `ELEVENLABS_API_KEY` | ElevenLabs (text to speech; billed by characters or credits) | the user records it (a phone in a quiet room, WAV) |
| Voiceover, another provider | through Higgsfield's API: `HF_API_KEY` + `HF_API_SECRET`; through its app: none (the user hands over the file) | Higgsfield (its Eleven voices, Seed Speech) | as above |
| Music | `ELEVENLABS_API_KEY` | ElevenLabs Music (`model_id` `music_v2`, or newer; pass it, since the API default can still be v1) | a track the user owns or licenses; Pixabay Music, the YouTube Audio Library |
| Music, another provider | Higgsfield through its API: `HF_API_KEY` + `HF_API_SECRET` (an MCP server keeps its own credentials, in the agent's setup); Higgsfield's app and Suno: none (the user hands over the file) | Higgsfield (Seed Audio), Suno (no public API) | as above |
| Sound effects, foley | `ELEVENLABS_API_KEY` (sound generation), `FREESOUND_API_KEY` | ElevenLabs, Freesound | recordings the user makes; Freesound CC0 sounds downloaded by hand |

No generated video: this method draws the motion in code. A user's own footage can still come in as a plate
(`craft.md`, "Plates").

Notes:
- ElevenLabs Music v2 builds a piece from a composition plan of sections and can regenerate one section and keep the
  rest (inpainting): the right tool for "change only the ending". Ask for instrumental music (no vocals) under a
  voiceover. Its terms clear generated tracks for commercial use; record the model and date anyway.
- Higgsfield's Seed Audio makes music, or a whole scene of voice, music and effects in one pass. For a film you mix
  yourself, ask it for the music alone, so the voice and effects stay separate and measurable. An agent with the
  Higgsfield MCP connected can call it directly; otherwise the user generates it and hands over the file.
- Suno: the user generates in Suno's app and hands over the track (and its stems, if their plan exports them). Commercial
  use depends on their plan: ask them to check. Unofficial Suno APIs break its terms: do not use them.
- Google's `google-genai` SDK prefers `GOOGLE_API_KEY` when both it and `GEMINI_API_KEY` are set: set only one.
- `FREESOUND_API_KEY` is this skill's name for the token, sent as `token=` on requests. A token searches and downloads
  the previews (MP3/OGG); the original files need OAuth2. CC-BY sounds need a credit line; CC-BY-NC ones cannot go in
  a commercial film.
- Endpoints, model names, prices and limits change: before the first call, read the provider's current documentation
  on the web and note the model and its price in the project's `BRIEF.md`.
- Record every generated asset's prompt, model, date, cost and licence terms next to the file (`<asset>.json`), so the
  user can prove its origin.

## Generated media in the film

- Keep them in `<project>/assets/gen/`, each with its `.json` record.
- An image: the page loads it as a local file in `window.READY` and draws it as a layer (`craft.md`, "Plates").
- Audio: in `<project>/audio/`, 48 kHz WAV (convert an mp3 once: `ffmpeg -i track.mp3 -ar 48000 audio/music.wav`).
- Generate plates and textures, not finished shots: a generated image as a ground under drawn work keeps the motion
  and the type in your hands.
- Ask for the material, not the style word: "a sheet of handmade cotton paper, raking light from the left, fibres
  visible" beats "vintage".
- Check every generated image at 1:1 for the tells (six fingers, melted letters, a smeared texture); a generated asset
  must be as good as the drawn ones or it does not go in.
