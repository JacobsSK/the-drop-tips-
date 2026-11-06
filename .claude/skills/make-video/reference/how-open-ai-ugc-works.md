# How "Open AI UGC" makes videos (reverse-engineered)

Source studied: the open-source Next.js app `Open-AI-UGC` (Anil-matcha/Open-AI-UGC).

**It doesn't render or stitch anything itself.** It's a thin front end and billing
layer around hosted AI video models sold through MuAPI (muapi.ai). The pipeline:

1. **Upload reference images** (`src/app/api/upload/route.js`)
   `POST https://api.muapi.ai/api/v1/upload_file` (multipart `file`, header `x-api-key`)
   → returns a hosted URL for the face / product / scene image.
2. **Start a generation** (`src/app/api/generate/route.js`)
   `POST` to a model endpoint with header `x-api-key` and JSON:
   ```json
   { "prompt": "@image1 a woman holds the bottle and says ...",
     "images_list": ["https://…/img1.jpg"], "image_url": "https://…/img1.jpg",
     "webhook_url": "https://your-app/api/webhook/muapi",
     "aspect_ratio": "9:16", "resolution": "720p", "duration": 6, "mode": "normal" }
   ```
   Endpoints:
   - `/api/v1/grok-imagine-image-to-video`
   - `/api/v1/veo3.1-image-to-video`
   - `/api/v1/seedance-2-image-to-video`
   - `/api/v1/happy-horse-1-image-to-video-720p`

   Response contains `request_id`. The app stores it with status `processing`.
3. **Receive the result** (`src/app/api/webhook/muapi/route.js`)
   MuAPI POSTs `{ id|request_id, status, outputs: ["https://…/video.mp4"], error }`
   to the webhook. `outputs[0]` is the finished MP4 URL.
4. **Business layer:** NextAuth (Google, or "sign in with your MuAPI key"), Prisma/Postgres
   `Creation` table for the gallery, Stripe credit packs. Credit cost per render in the app:
   Grok 5–10 credits/s, Veo 3.1 500–740/s, Seedance 50/s, Happy Horse 36/s.

The "magic" (a realistic person moving and talking) is the diffusion video model
(Veo, Seedance, etc.), which generates all frames at once from the prompt + image.
The app adds prompt UI, an image picker (`@image1` tokens) and billing.

## Using that path from Claude Code

Possible, but it needs: (a) a MuAPI API key, (b) `api.muapi.ai` allowed by the
environment's network policy, (c) real money per render. Without a webhook server,
poll instead. Check MuAPI's docs for the current result endpoint; it is not in this
app's code. Download `outputs[0]` and treat it like any other clip: normalize it with
ffmpeg, then concat or overlay captions rendered by this skill.

## How this skill differs

This skill is the "draw every picture, then stitch" approach: deterministic,
free, offline, brand-exact text and layout, instant re-edits. Combine both for
best results: AI clips for the realistic shots, this renderer for hooks,
captions, product cards, proof and CTA end-cards.
