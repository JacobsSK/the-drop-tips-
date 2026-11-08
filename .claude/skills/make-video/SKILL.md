---
name: make-video
description: Make short vertical videos (TikTok / Reels / Shorts ads, UGC-style promos, product explainers, animated slideshows) entirely locally by designing animated HTML frames, rendering them frame-by-frame in headless Chromium, and stitching them into an MP4 with ffmpeg. Use whenever the user asks for a video, ad, reel, short, animation, promo clip, or "make pictures and put them together".
---

# make-video

You make videos the way animators do: draw every frame, then play them fast.
Here each "picture" is a web page at a moment in time `t`. `scripts/render.js`
steps `t` from 0 to the end at 30fps, screenshots each frame, and pipes the
frames into ffmpeg → `out.mp4` (H.264, 1080×1920, plays everywhere).

What this is good at: kinetic-typography ads, karaoke captions, animated product
cards, stats/proof slides, photo slideshows with Ken Burns motion, logo stings,
before/after, listicles. It is NOT photoreal AI actors talking to camera; that needs
a hosted AI video model (see `reference/how-open-ai-ugc-works.md`).

Paths below are relative to this skill's folder (`.claude/skills/make-video/`).

## Workflow

1. **Brief.** Get (ask only for what's missing): product/offer, audience, the one
   action you want (CTA + where: "link in bio", URL, promo code), length (default 15s),
   platform (default 9:16), and any assets: logo, product photos, screenshots, clips,
   music/voiceover, brand colors/fonts. Never invent claims (ratings, prices,
   "#1", awards). Use the user's real facts or mark them `PLACEHOLDER`.
2. **Storyboard.** Use `reference/ad-structure.md`. Write a scene table:
   `time | on-screen text | visual | motion | transition`. Hook in the first 1–2s.
   For a new campaign, show the table to the user before building; for edits, just build.
3. **Build.** Create `videos/<slug>/` in the user's project, copy
   `templates/ugc-ad.html` to `videos/<slug>/index.html`, put assets in
   `videos/<slug>/assets/`. Rewrite only the SCENES block (and the style block's
   example-specific section / `:root` colors). Leave the ENGINE block alone.
4. **Render.**
   ```bash
   node .claude/skills/make-video/scripts/render.js videos/<slug>/index.html videos/<slug>/<slug>.mp4
   ```
   Always run it from the project root: the page is served over a local http server rooted at the
   current folder (so `/.claude/skills/make-video/vendor/three.module.min.js` resolves for 3D).
   Options: `--audio track.mp3` (muxed and faded out at the end), `--audio-volume 0.8`,
   `--fps 30`, `--duration 15`, `--width/--height` (e.g. 1080×1080 for feed),
   `--from 9 --duration 12` to render only part of it. A 15s video takes ~30s.
   The script exits non-zero and prints `PAGE ERRORS` if the page threw. Fix those.
5. **Review. Always look before delivering.**
   ```bash
   .claude/skills/make-video/scripts/review.sh videos/<slug>/<slug>.mp4 /tmp/sheet.png 0.75
   ```
   Read the contact sheet image and check: the hook is readable at 0.5s; no text is cut off
   or overlapping; text stays out of the bottom 380px and right 140px (platform UI covers them);
   every line stays on screen long enough to read (≈0.25s per word + 0.5s); the CTA is on
   screen ≥2s; nothing is blank or stuck. Fix and re-render.
6. **Deliver.** Send the MP4 (and the sheet) with SendUserFile. Offer 2–3 hook
   variants: duplicate `index.html`, change only scene 1, then render each.

## Authoring cheatsheet (template engine)

```html
<section class="scene" data-start="2.4" data-end="4.8" data-trans="whip"> … </section>
```
- `data-trans`: `cut fade slide up zoom whip`. Give every scene an opaque background.
- On any element: `data-anim="pop"` (combine: `"pop pulse"`). Types: `fade up down left right pop zoom spin`
  (entrances), `strike` (draws a red line through the text at `data-at`), `shake pulse float` (continuous), `words` (karaoke captions, current word gets `--hl` color;
  `data-step` = seconds per word). Timing: `data-at` (start, seconds from scene start), `data-dur`, `data-out`.
- `data-kb="in|out|left|right"`: slow Ken Burns move across the scene, for photos:
  ```html
  <div class="full" data-kb="in" style="background-image:url(assets/photo1.jpg)"></div>
  <div style="position:absolute;inset:0;background:linear-gradient(transparent 40%,rgba(0,0,0,.75))"></div>
  ```
- `data-count="0:4.9:1"`: number counts up (from:to:decimals).
- More kinds: `squash` (springy squash-and-stretch entrance), `glow` (pulsing neon glow, colour `--glow`),
  `blur` (blur-in), `draw` (on an SVG `<path>`: the line draws itself).
- `<circle r="14" data-follow="pathId" data-at="1" data-dur="2">`: a dot travels along a path. Pair it with
  `draw` on the same path for a "journey" trail (day 1 → day 30).
- `<div class="hud" data-from="3" data-to="25">…</div>` outside the scenes: a persistent banner (price, series name, CTA)
  shown between those absolute times. Style `.hud` yourself (position absolute, opacity 0).
- `<div class="fx-particles" data-count="40" data-color="#f9a825"></div>`: soft floating particles.
- `window.onFrame = (t) => {...}` in a `<script>` after the scenes: custom per-frame animation (a running figure,
  a lever, filling rings, volume bars). t is absolute seconds; keep it a pure function of t.
- `<video data-clip data-at="0.2" src="clip.mp4" muted>` plays (a negative data-at starts the clip that many seconds in) a rendered clip (e.g. a 3D shot) inside a scene,
  frame-accurate. Size it with CSS; put HTML overlays on top.
- Voiceover with exact timings: generate it phrase by phrase (Kokoro, see below) and write the
  phrase start/end times to `vo_marks.json`. Set `data-start` / `data-at` from those times.
- `<div class="fx-streaks" data-speed="1200" data-count="40"></div>`: rushing speed/wind lines.
- Classes: `.center` (centered column), `.h-xl .h-l .h-m .body .chip .btn .caption .full`.
- Draw illustrations as inline SVG (see the flyer in the template). Emoji render via Noto Color Emoji.
- Preview: open the HTML in a browser. It loops in real time (Space pause, ←/→ scrub, R restart).
  To check one moment without rendering a video, screenshot with Playwright after calling
  `window.renderFrame(t)` on the page loaded with `?render=1`.

**Hard rules** (the renderer seeks time; it doesn't play it):
- All motion must be a pure function of `t`. No `Math.random()`, `Date.now()`, `setTimeout`,
  `setInterval`, or `requestAnimationFrame` in scene code. Use the engine's attributes, CSS
  `@keyframes` (auto-seeked), or add logic inside `window.renderFrame`.
- Use local fonts: `Inter`, `Inter Display` (weights 100–900), `JetBrains Mono`, `Liberation Serif`,
  `DejaVu`. Remote font CDNs may be blocked when rendering. Load other fonts from files in `assets/`
  with `@font-face`.
- Images: reference local files (`assets/…`). Remote URLs may be blocked.

## Real 3D (three.js)

`templates/3d-product.html` is a working three.js product shot: the product cover is wrapped
on a 3D book or box, with soft shadows, a rim light, a bounce drop-in, a turn and a camera dolly.
Edit `CONFIG` (cover image, size, colours, overlay text timings). three.js is vendored at
`vendor/three.module.min.js` (import map `"three": "/.claude/skills/make-video/vendor/three.module.min.js"`).
Rules for 3D pages: set `window.VIDEO_READY = false` first and `true` after async loads (textures, models);
put all motion in `window.renderFrame(t)` and call `renderer.render()` there; set
`preserveDrawingBuffer: true`. Rendering uses software WebGL: about 3–8s of render time per second
of video at 1080×1920. Render 3D shots as separate clips and join them with ffmpeg.

## Style and long videos

Read `reference/style-playbook.md` before planning anything bigger than a simple ad. It covers
the techniques the user likes (screen-in-scene, persistent series banner, comment-keyword CTA,
one-word captions, mascots, 3D, motion trails) and how to build 60s+ videos in chapters.

## Pictures: where they come from

- **Drawn by you:** HTML/CSS gradients, shapes, SVG illustrations, icons, charts, mock phone screens.
- **User's photos / screenshots / logo:** best for real products. Ask for them.
- **AI-generated photos/clips:** only with an image/video API key and that host allowed on the network
  (e.g. MuAPI, see reference). Generate stills, save to `assets/`, then animate them with `data-kb`.

## Mixing in real video clips (ffmpeg)

Normalize a clip to 9:16 1080×1920 30fps:
```bash
ffmpeg -i in.mov -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" -c:v libx264 -pix_fmt yuv420p -an clip.mp4
```
Join rendered segments and clips (all must share size/fps; `list.txt` lines: `file 'a.mp4'`):
```bash
ffmpeg -f concat -safe 0 -i list.txt -c copy joined.mp4
```
Burn the rendered animation as the first N seconds and the clip after: render the HTML for only its
scenes (`--duration`), normalize the clip, concat. Add audio last:
`ffmpeg -i joined.mp4 -i music.mp3 -c:v copy -c:a aac -shortest final.mp4`.

## Audio

**Scripts (preferred):**
- `scripts/voice.py <script.json> <outdir> --models <kokoro dir> [--voice af_heart] [--speed 1.08]`:
  script.json is `[["id","Text.",gap_before], ...]` → `vo.mp3` + `vo_marks.json` (phrase start/end times; time the scenes to these).
- `scripts/sfx.py make videos/sfx`: synthesises `whoosh`, `whoosh_long`, `impact`, `pop`, `riser`, `tick` (numpy + soundfile).
- `scripts/sfx.py mix vo.mp3 cues.json mix.mp3 --sfxdir videos/sfx`: cues `[{"t":1.75,"sfx":"whoosh","gain":1}]`.
  Put a whoosh ~0.1–0.2s before every scene change, an impact on the big word, pops on icons, ticks on counters/bars,
  and a riser into the product reveal. Then render with `--audio mix.mp3`.
  You can't listen to it: check SFX with `ffmpeg -i x.wav -lavfi showspectrumpic=s=600x240 spec.png` and look at it.


**AI voice (free, local):** Kokoro TTS (`pip install kokoro-onnx soundfile` in a venv; model files
`kokoro-v1.0.int8.onnx` and `voices-v1.0.bin` from github.com/thewh1teagle/kokoro-onnx releases
`model-files-v1.0`). Female voices `af_heart` (default), `af_bella`, `af_sarah`, `af_nicole`; speed ~1.05–1.08.
Write numbers as words ("forty", "thirty seven dollars"). Polish the voice with:
`ffmpeg -i in.wav -af "highpass=f=80,equalizer=f=3000:t=q:w=1:g=2,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.5:LRA=7" vo.mp3`
**The user's own voice:** a phone voice memo; run the same polish chain on it. Get the phrase timings
by listening points: `ffmpeg -i vo.mp3 -af silencedetect=n=-35dB:d=0.25 -f null -` lists the pauses.
Also usable: a voiceover or music file the user provides (`--audio`).
Time scenes to the voiceover: get its length with
`ffprobe -v error -show_entries format=duration -of csv=p=0 vo.mp3`, then match the scene `data-start`
values to the line timings. Remind the user to use music they have rights to.
