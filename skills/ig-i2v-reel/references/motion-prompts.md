# Motion prompts for image-to-video

Formula: **[what the subject does] + [one camera move] + [light/mood]**, 1-2
sentences, describing what is already in the image.

Camera moves that animate reliably: slow push-in, slow pull-back, gentle pan
left/right, slight orbit, handheld sway, parallax drift.

| Image type | Example prompt |
|---|---|
| Product on surface | Slow push-in on the bottle, soft light sweeping across the label, subtle dust particles in the air. |
| Portrait | Gentle handheld sway, hair and jacket moving in a light breeze, warm golden-hour glow. Subject stays still, no talking. |
| Landscape / travel | Slow pan across the valley, clouds drifting, mist rolling over the ridge. |
| Food | Steam rising from the bowl, slow orbit, shallow depth of field. |
| Before/after | Use --end-frame with the "after" image; prompt: smooth transformation, locked camera. |

Avoid: fast action, multiple subjects interacting, text in the frame (it
warps), "make it cinematic" with no concrete motion, camera moves plus subject
action plus effects all at once.

Negative prompt that helps: "warped face, extra fingers, flicker, text, watermark, jitter".
