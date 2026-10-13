---
name: agnes-video-generator
description: >-
  Turn a finished Reel script into shot-by-shot prompts for an AI text-to-video
  generator - one prompt per beat, timed to the voiceover, 9:16, with the
  on-screen text kept out of the render. Use when the user wants to generate
  the footage for a Reel with AI instead of filming it, asks for "video
  prompts", "b-roll prompts", "AI video from this script", or runs
  /agnes-video-generator after /ig-reel.
---

# agnes-video-generator

`/ig-reel` writes the script. This skill turns that script into a shot list an
AI video generator can render, one clip per beat, so the user can assemble the
Reel without filming anything.

It is tool-agnostic. The output is plain prompts plus durations, so it works
in any text-to-video generator that takes a prompt and a clip length.

```bash
python3 shots.py script.txt --style "clean documentary" --subject "a freelance designer"
python3 shots.py script.txt --json        # machine-readable, for scripting
python3 shots.py script.txt --wpm 185 --max-clip 5
```

## Before you start

1. Read `~/.claude/instagram/voice.md` if it exists, for the tone and what the
   user never shows on screen.
2. Get the script. If the user has none, run `/ig-reel` first. Do not invent
   one here.
3. Ask for, in one batched question: the **subject** that recurs (a person, a
   product, a place), and a **style** line. Both repeat in every prompt so the
   clips look like one video. Without them the generator gives you ten
   unrelated looks.

## The loop

1. Save the spoken script, one beat per line, and run `shots.py`.
2. Read each prompt against its beat. The tool writes a scaffold: the beat's
   subject matter, the camera move, the repeated subject and style. **Rewrite
   the scene description** in each prompt to show what the line says, with a
   concrete visible action. The tool cannot see your idea.
3. Fix every flag the tool raises (see below). Re-run until clean.
4. Print the block, then tell the user which clips to generate first: the hook
   clip decides the Reel, so render it first and regenerate it until the first
   frame has motion.

## What the tool enforces

- **Clip length from the voiceover.** Each beat's duration is its spoken
  length at the given wpm, rounded up to the next half second and capped at
  `--max-clip` (default 5s). Longer beats are split into two clips.
- **A different shot every clip.** Camera moves rotate (push-in, pan, orbit,
  handheld, overhead, tilt up) and shot sizes alternate, so no two neighbours
  match. This is the "frame changes every beat" rule from `/ig-reel`.
- **Motion in the first frame.** Clip 1 always opens mid-action. A generator
  that starts on a still face loses the viewer before the hook lands.
- **9:16, 1080x1920.** Every prompt carries the aspect ratio.
- **Safe zone.** Subject stays in the centre; nothing important in the top
  230px, the bottom 480px, or the right 230px.
- **No text in the render.** Generators garble lettering. Every prompt says
  "no text, no captions, no logos", and the on-screen cards are added in the
  edit, not generated.
- **No real people.** Prompts describe a generic subject. Do not prompt for a
  named person's likeness, and do not generate a "testimonial" or a fake
  result under the user's name.

## Flags

| flag | meaning |
| --- | --- |
| `HOOK_LONG` | clip 1 runs past 3s; shorten the spoken hook |
| `NO_SUBJECT` | no `--subject`, so clips will not match each other |
| `ABSTRACT` | the beat has nothing visible to show; rewrite it concretely |
| `TOTAL_OFF` | total length is not within 15% of `--target` |

## Output

```
SHOT LIST  9 clips, 28.5s, 9:16
 1  0:00-0:02.0  hook      push-in / close
    Close-up, camera pushes in fast, a freelance designer slams a laptop shut ...
 2  0:02-0:05.5  stake     slow pan / medium
    ...

AI VIDEO READY
clips:      9
total:      28.5s
flags:      none
on-screen:  add in the edit, not in the render

Reply "yes" to finish, or tell me which clip to rewrite.
```

## Rules

- **Never publish.** The user renders, assembles and posts.
- **Never fabricate.** No invented metrics, clients, results or testimonials
  shown as real footage. AI footage should be disclosed as AI-generated where
  the platform asks for it; remind the user to switch on Instagram's AI label.
- **No third-party likeness or brand marks** in prompts.
- **Keep the voiceover real.** This skill makes pictures; the user's voice
  still carries the Reel.
