---
name: ig-i2v-reel
description: >-
  Turn one or more still images into a vertical 9:16 Instagram Reel with AI
  image-to-video (Agnes Video Generator), then package it with an on-screen
  hook, caption, hashtags and cover text. Use whenever the user wants to
  animate a photo or product shot, make a reel from images, "bring this image
  to life", do image-to-video, make an AI video for Instagram, or has a
  picture and wants a Reel out of it, even if they never say "image-to-video".
---

# ig-i2v-reel

Image(s) in, postable Reel package out. Files only: this skill never posts to
Instagram. The user uploads the MP4 themselves.

Engine: the Agnes Video Generator REST API (free, local, port 8765). If it is
not installed or running, see "Setup" below.

## Workflow

1. **Gather inputs.** Need: image path(s), what the Reel is for (product,
   personal brand, travel, etc.), and desired length (default 5-10s per clip,
   15-30s total). If `~/.claude/instagram/voice.md` exists, read it so the
   hook and caption sound like the user. One batched question if something
   is missing; do not interrogate.
2. **Look at each image** (Read it) before writing motion. The prompt must
   describe what is actually in the frame, otherwise the model invents a new
   scene and the Reel stops matching the photo.
3. **Write one motion prompt per image** using `references/motion-prompts.md`.
   Rule of thumb: one subject action + one camera move + mood. Subtle beats
   busy; image-to-video degrades fast when asked for lots of movement.
4. **Generate clips** at 9:16 with `scripts/agnes_i2v.py` (see below). Run
   clips for different images in parallel; they are independent.
5. **Join** multiple clips with `scripts/agnes_i2v.py concat`. Pair clips so
   motion direction continues (push-in then push-in, not push-in then
   pull-out) and the cut lands on a movement, which hides the seam.
6. **Check the result** by extracting a frame or two (`ffmpeg -ss 1 -i f.mp4
   -frames:v1 f.png`) and viewing them. Confirm it is upright (see the
   rotation defect below), faces/product are not warped, and nothing odd
   appeared. Regenerate with a calmer prompt or new seed if not; say so
   honestly if it still looks off.
7. **Write the package** to `reel-package.md` next to the video: on-screen
   hook (under 8 words, readable in the first second), caption (hook line
   first, because only ~125 characters show before "more"), 3-5 specific
   hashtags, cover text, a suggested audio vibe (the user adds trending audio
   inside Instagram), and the alt text.

## Generating a clip

```bash
python3 scripts/agnes_i2v.py clip IMAGE.jpg "motion prompt" \
    --duration 5 --out clip1.mp4 [--end-frame END.jpg] [--seed N]
python3 scripts/agnes_i2v.py concat clip1.mp4 clip2.mp4 --out reel.mp4
```

- `--end-frame` switches to keyframes mode (first-to-last frame
  interpolation): best for a controlled transition, e.g. product before/after.
- Host defaults to `http://localhost:8765`; override with `AGNES_URL`.
- Durations: v2.0 model accepts 5/10/15/18/20; 2.5-series accepts 4,5,6,8,10,12.
  A 422 reply lists the valid ones.
- The script polls until done (typically a few minutes per clip) and exits
  non-zero with the server's error on failure.

## Known gotchas

- **9:16 rotation defect on Video 2.5 Flash:** the upstream API can return
  portrait clips whose pixels are a sideways landscape frame. Default to the
  Video 2.0 model for 9:16, or set `AGNES_FIX_V25_PORTRAIT_ROTATION=1` on the
  server. Always check a frame (step 6).
- Source image should be sharp and roughly portrait. A landscape photo gets
  cropped or letterboxed for 9:16; tell the user which part will be lost.
- AI motion on people's faces and hands is the most likely thing to look
  wrong. If the image is a person, keep motion to camera movement, hair,
  fabric, and light, and avoid speech or gestures.
- Disclose AI-generated content: Instagram has an "AI info" label. Remind the
  user to switch it on when posting.

## Setup (only if the server is not reachable)

```bash
git clone https://github.com/lcy362/agnes-video-generator.git
cd agnes-video-generator && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env     # set AGNES_API_KEY (free key from platform.agnes-ai.com)
./start.sh               # serves http://localhost:8765
```

Ask the user for their API key; never invent one.
