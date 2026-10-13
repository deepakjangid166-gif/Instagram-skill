#!/usr/bin/env python3
"""Image-to-video via a local Agnes Video Generator server, plus clip concat.

  agnes_i2v.py clip IMAGE "prompt" --out clip.mp4 [--duration 5] [--end-frame E.jpg] [--seed N]
  agnes_i2v.py concat a.mp4 b.mp4 --out reel.mp4
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time

import requests

BASE = os.environ.get("AGNES_URL", "http://localhost:8765").rstrip("/")


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def clip(a):
    files = {"reference_image": open(a.image, "rb")}
    mode = "i2v"
    if a.end_frame:
        files["end_frame_image"] = open(a.end_frame, "rb")
        mode = "keyframes"
    data = {"prompt": a.prompt, "mode": mode, "duration": a.duration,
            "video_width": 768, "video_height": 1152,  # 9:16 portrait
            "negative_prompt": a.negative}
    if a.seed is not None:
        data["seed"] = a.seed
    try:
        r = requests.post(f"{BASE}/api/tasks/simple", data=data, files=files, timeout=60)
    except requests.ConnectionError:
        fail(f"cannot reach {BASE}; start the server (./start.sh) or set AGNES_URL")
    if r.status_code != 200:
        fail(f"submit failed {r.status_code}: {r.text[:400]}")
    tid = r.json()["task_id"]
    print(f"task {tid} submitted", file=sys.stderr)

    deadline = time.time() + a.timeout
    while time.time() < deadline:
        time.sleep(10)
        st = requests.get(f"{BASE}/api/tasks/{tid}", timeout=30).json()
        status = str(st.get("status"))
        if status == "completed":
            break
        if status == "failed":
            fail(f"generation failed: {st.get('error') or st.get('message') or 'see /api/tasks/%s/diagnostics' % tid}")
    else:
        fail(f"timed out; task {tid} may still be running, resume with GET /api/video/{tid}")
    v = requests.get(f"{BASE}/api/video/{tid}", timeout=300)
    if v.status_code != 200:
        fail(f"download failed {v.status_code}")
    with open(a.out, "wb") as f:
        f.write(v.content)
    print(a.out)


def ffmpeg_bin():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        fail("ffmpeg not found")


def concat(a):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as lst:
        for p in a.clips:
            lst.write(f"file '{os.path.abspath(p)}'\n")
    # re-encode so clips with slightly different params join cleanly
    cmd = [ffmpeg_bin(), "-y", "-f", "concat", "-safe", "0", "-i", lst.name,
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", "-an", a.out]
    res = subprocess.run(cmd, capture_output=True, text=True)
    os.unlink(lst.name)
    if res.returncode:
        fail(res.stderr[-400:])
    print(a.out)


p = argparse.ArgumentParser()
sub = p.add_subparsers(dest="cmd", required=True)
c = sub.add_parser("clip")
c.add_argument("image"); c.add_argument("prompt")
c.add_argument("--out", required=True)
c.add_argument("--duration", type=int, default=5)
c.add_argument("--end-frame")
c.add_argument("--seed", type=int)
c.add_argument("--negative", default="warped face, extra fingers, flicker, text, watermark")
c.add_argument("--timeout", type=int, default=1200)
c.set_defaults(fn=clip)
j = sub.add_parser("concat")
j.add_argument("clips", nargs="+"); j.add_argument("--out", required=True)
j.set_defaults(fn=concat)
a = p.parse_args()
a.fn(a)
