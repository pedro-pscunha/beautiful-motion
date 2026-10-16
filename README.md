# beautiful-motion

An agent skill for making short motion films that look hand-made: chalk that draws itself, a woodcut being cut, paper
that folds. The agent draws every frame in code (an HTML canvas exported with Playwright), measures what it makes,
adds the sound you choose, finishes the film with ffmpeg, and can run other agents as critics to push the quality up.

It follows the [Agent Skills](https://agentskills.io) format, so it works in Claude Code, OpenAI Codex, pi and other
agents that read `SKILL.md`, on macOS, Windows and Linux.

## Install

Clone it into your agent's skills folder.

Claude Code:

```
git clone https://github.com/pedro-pscunha/beautiful-motion ~/.claude/skills/beautiful-motion
```

Codex, pi and other agents that read `~/.agents/skills`:

```
git clone https://github.com/pedro-pscunha/beautiful-motion ~/.agents/skills/beautiful-motion
```

On Windows, in PowerShell, use `$env:USERPROFILE\.claude\skills\beautiful-motion` or
`$env:USERPROFILE\.agents\skills\beautiful-motion` as the last argument. To update later, run `git pull` in that
folder.

## Use

Ask your agent for a film: "make a 20-second animated poem about the sea, 9:16, with a voiceover". On a first run the
agent checks the tools it needs (Node 20.6+, uv, ffmpeg, Playwright with Chromium), tells you what is missing, and walks
you through installing it. Then it asks about the film and about the resources you want to use:

- music: your own track, a royalty-free library, ElevenLabs Music, Higgsfield, Suno, a score written in code, or none;
- voiceover: ElevenLabs, Higgsfield, your own recording, or none;
- sound effects: ElevenLabs, Freesound, your own recordings, or none;
- generated images for textures or backdrops: Higgsfield, OpenAI, Google, fal or Replicate; by default everything is
  drawn in code.

By default the agent colours each shot with one combination from Sanzo Wada's *A Dictionary of Color Combinations*
(348 combinations from his 1933-34 colour books), read from an open dataset.

With no paid service at all you still get a complete film. When a step needs an API key, the agent asks you to put it
in a `.env` file in your project; it never asks for keys in the chat and never prints them. Before the first paid
call it tells you what it will cost and waits for your OK.

## What is inside

- `SKILL.md`: the method, step by step.
- `references/`: setup per OS, keys and providers, the colour book (Sanzo Wada's combinations and how to pick them),
  the drawing and animation techniques (chalk, woodcut, stamp, stained glass, mosaic, embroidery, knitting, string art,
  watercolour and more; build then live, one clock, soak transitions), the render contract, sound, finishing, and
  reviews.
- `scripts/`: the frame renderer, a dependency check, a Wada colour picker, a contact sheet, a fine film grain,
  flicker, loudness and voice-margin measurements, and a tool that freezes a version for grading.
- `assets/`: a starter page that follows the render contract, and the `.env` template (`env.example`).

To see the starter, open `assets/starter/index.html` in a browser; it plays in a loop.

## License

MIT. See `LICENSE`.
