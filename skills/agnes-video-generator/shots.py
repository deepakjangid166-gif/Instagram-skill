#!/usr/bin/env python3
"""
shots.py - turn a Reel script into a timed shot list of AI video prompts.

One beat per line in, one or more clip prompts out. Durations come from the
spoken length of each line, camera moves and shot sizes rotate so neighbouring
clips differ, and every prompt carries the repeated subject and style, the
9:16 frame, the safe zone and a no-text instruction.

Usage
  python3 shots.py script.txt
  python3 shots.py script.txt --subject "a freelance designer" --style "warm documentary"
  python3 shots.py script.txt --wpm 185 --max-clip 5 --target 30
  pbpaste | python3 shots.py -
  python3 shots.py script.txt --json
"""

import argparse
import json
import math
import re
import sys

WORD_RE = re.compile(r"[A-Za-z0-9$%'’-]+")
CONCRETE_RE = re.compile(r"\$\s?\d|\b\d[\d,.]*\b|(?<!^)\b[A-Z][a-z]{2,}\b")

CAMERA = ["fast push-in", "slow pan", "orbit around the subject", "handheld follow",
          "overhead top-down", "tilt up", "slow pull-back", "whip pan"]
SIZE = ["close-up", "medium shot", "wide shot", "extreme close-up"]
ROLE_FIRST = "hook"
HOOK_WINDOW = 3.0
SAFE = ("vertical 9:16, 1080x1920, subject centred, keep the top 230px, bottom "
        "480px and right 230px free of important detail")
NEGATIVE = "no text, no captions, no logos, no watermarks"


def words(text):
    return WORD_RE.findall(re.sub(r"(?<=\d),(?=\d)", "", text))


def tc(s):
    m, sec = divmod(s, 60)
    return f"{int(m)}:{sec:04.1f}"


def clip_seconds(n_words, wpm):
    return max(1.0, math.ceil(n_words / (wpm / 60) * 2) / 2)


def role(i, last):
    if i == 0:
        return "hook"
    if i == 1:
        return "stake"
    if i == last:
        return "payoff"
    return "body"


def build(raw, wpm, max_clip, subject, style):
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    clips, t = [], 0.0
    for li, line in enumerate(lines):
        total = clip_seconds(len(words(line)), wpm)
        parts = 2 if total > max_clip else 1
        for p in range(parts):
            dur = min(max_clip, total / parts if parts > 1 else total)
            dur = max(1.0, math.ceil(dur * 2) / 2)
            n = len(clips)
            cam, size = CAMERA[n % len(CAMERA)], SIZE[n % len(SIZE)]
            r = role(li, len(lines) - 1) if p == 0 else "body"
            opener = "Opens mid-action, motion in the first frame. " if n == 0 else ""
            who = subject or "the subject"
            prompt = (f"{size.capitalize()}, {cam}. {opener}{who}: {line} "
                      f"[REWRITE: show this line as one concrete visible action]. "
                      f"{style + '. ' if style else ''}{SAFE}. {NEGATIVE}.")
            clips.append({"n": n + 1, "start": t, "end": t + dur, "dur": dur,
                          "role": r, "camera": cam, "size": size,
                          "line": line, "prompt": prompt})
            t += dur
    return clips


def flags(clips, subject, target):
    out = []
    if not subject:
        out.append("NO_SUBJECT: pass --subject so clips match each other")
    if clips and clips[0]["end"] > HOOK_WINDOW:
        out.append(f"HOOK_LONG: clip 1 ends at {clips[0]['end']:.1f}s, past {HOOK_WINDOW:.0f}s")
    run = 0
    for c in clips:
        run = 0 if CONCRETE_RE.search(c["line"]) else run + 1
        if run >= 3:
            out.append(f"ABSTRACT: clips {c['n']-2}-{c['n']} show nothing concrete")
            break
    if clips and target:
        total = clips[-1]["end"]
        if abs(total - target) > 0.15 * target:
            out.append(f"TOTAL_OFF: {total:.1f}s vs target {target}s")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", help="script file, one beat per line, or - for stdin")
    ap.add_argument("--wpm", type=int, default=165)
    ap.add_argument("--max-clip", type=float, default=5.0)
    ap.add_argument("--target", type=float)
    ap.add_argument("--subject", default="")
    ap.add_argument("--style", default="")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    raw = sys.stdin.read() if a.script == "-" else open(a.script, encoding="utf-8").read()
    clips = build(raw, a.wpm, a.max_clip, a.subject, a.style)
    if not clips:
        sys.exit("empty script")
    fl = flags(clips, a.subject, a.target)

    if a.json:
        print(json.dumps({"clips": clips, "flags": fl, "total": clips[-1]["end"]}, indent=2))
        return
    total = clips[-1]["end"]
    print(f"SHOT LIST  {len(clips)} clips, {total:.1f}s, 9:16")
    for c in clips:
        print(f"{c['n']:>2}  {tc(c['start'])}-{tc(c['end'])}  {c['role']:<7} {c['camera']} / {c['size']}")
        print(f"    {c['prompt']}")
    print("\nAI VIDEO READY")
    print(f"clips:      {len(clips)}")
    print(f"total:      {total:.1f}s")
    print("flags:      " + ("none" if not fl else "\n            ".join(fl)))
    print("on-screen:  add in the edit, not in the render")


if __name__ == "__main__":
    main()
