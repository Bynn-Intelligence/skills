---
name: bynn-moderation
description: >-
  Run any Bynn detection or moderation model over image, video, text, or audio
  through POST /moderation/infer: nudity, violence, weapons, drugs, CSAM, PII
  solicitation, AI-generated image/video/text/music, deepfakes, OCR, age and minor
  detection, and more. Covers model discovery, per-modality inputs, batching,
  idempotency, and reading results. Use for content safety, trust and safety
  pipelines, and "is this AI-generated or a deepfake" questions.
metadata:
  author: bynn
  version: "0.1.0"
license: MIT
---

# Content moderation and detection

One endpoint, many models. You pick the model by API name and hand it content in
whichever form you already have.

Base: `https://api.bynn.com/v1`

## Discover models first

Model availability depends on your account, so read the catalog rather than hardcoding a
name from this file:

```bash
curl https://api.bynn.com/v1/moderation/models/all \
  -H "Authorization: Bearer <YOUR_TOKEN>"

curl https://api.bynn.com/v1/moderation/models/ai-generated-image \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

The single-model call returns the categories that model outputs, which is what your
result parsing should be written against.

## Prefer async

There are two submit endpoints:

| Endpoint | Returns | Use it for |
|---|---|---|
| `POST /moderation/infer_async` | `202` immediately with an inference token | Default. Everything that is not a user waiting on screen. |
| `POST /moderation/infer` | The result inline, once processing finishes | Small, interactive, one-off checks only. |

**Use the async endpoint whenever you can.** It accepts the same parameters, its rate
limit is far looser than the synchronous one because the real work is paced by the
inference queue, and it never holds a request thread open. The synchronous endpoint ties
up a connection on both sides for the whole inference, which is how a video model or a
batch turns into timeouts under load.

```bash
curl -X POST https://api.bynn.com/v1/moderation/infer_async \
  -H "Authorization: Bearer <YOUR_PRIVATE_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ai-generated-image",
    "image_url": "https://example.com/file.jpg",
    "idempotency_key": "scan-8123"
  }'
# -> 202 { "token": "...", "status": "pending", ... }
```

Then read the result at `GET /moderation/inference/{token}`. Collect the token, get on
with other work, and check back. Do not sit in a tight polling loop against a single
token: back off, and batch your reads if you have many outstanding.

Async also gives you real backpressure. A `429` with `type: "queue_full"` means your
organization has too much outstanding work, and the response carries `Retry-After`.
Honour it. The synchronous endpoint has no equivalent, so overload shows up there as
timeouts instead.

Set `idempotency_key` on every async submit. A retry of an already-accepted submission
returns the existing record instead of queueing a second one, and that holds even when
you are being throttled, which is exactly when clients retry.

## Run an inference

The synchronous form, for the interactive cases where waiting inline is genuinely
simpler:

```bash
curl -X POST https://api.bynn.com/v1/moderation/infer \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ai-generated-image",
    "image_url": "https://example.com/file.jpg"
  }'
```

`model` is the only required field. Supply exactly one content input, matched to the
model's modality:

| Modality | Fields |
|---|---|
| Image | `image_url`, `base64_image`, or `image_urls` / `base64_images` for a batch |
| Video | `video_url` or `base64_video`, plus optional `fps` (1 to 10) |
| Text | `content` |
| Audio | `audio_url` or `base64_audio` |
| PDF | `base64_pdf`, for the OCR model, processed per page |

Other parameters:

- `idempotency_key`: deduplicates retries. Set it on anything you might resend.
- `metadata`: arbitrary object stored with the inference, for your own correlation.
- `distance_threshold` (0.3 to 0.7): face matching strictness where a model does matching.
  Lower is stricter.
- `extract_faces`: return a cropped PNG of the best face match.

Read a stored result later with:

```bash
curl https://api.bynn.com/v1/moderation/inference/<token> \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

## The catalog

Names as of writing. Confirm against `/moderation/models/all` before you depend on one.

**Image.** `nudity-detection`, `weapons-detection`, `drugs-detection`,
`alcohol-detection`, `smoking-detection`, `gambling-detection`, `military-detection`,
`money-detection`, `vehicle-detection`, `people-counting`,
`destruction-fire-detection`, `graphic-language-detection`, `content-rating`,
`ai-generated-image`, `ai-edited-image-forgery`, `effort-deepfake-image`,
`document-tampering`, `document-liveness`, `document-classifier`, `vlm-ocr`,
`vlm-violence-detection`, `age-detection`, `minor-detection`, `beauty-scoring`,
`face-occlusion-detection`, `selfie-liveness`, `face-redaction`,
`face-redaction-minors`, `wanted-person-detection-image`.

**Video.** `effort-deepfake-video`, `face-liveness`, `video-content-rating`,
`vlm-video-violence-detection`, `wanted-person-detection`,
`bynn-cctv-abnormality-crime`.

**Text.** `ai-generated-text`, `fake-news-detection`, `fraud-text-detection`,
`advanced-sentiment-analysis`, `mental-health-detection`,
`pii-solicitation-detection`, `bynn-csam-text`.

**Audio.** `voice-deepfake-detection`, `voice-safety-detection`, `ai-generated-music`.

## AI-generated media

`ai-generated-image` returns a probability and, when it can, the likely generator:

```json
{
  "result": {
    "is_ai_generated": true,
    "ai_probability": 0.9998,
    "top_generator": { "name": "openai_gpt_image", "probability": 0.96 }
  }
}
```

### Send the original file, unmodified

This is the single biggest cause of missed detections. **Do not resize, crop, re-encode,
re-compress, strip metadata, or run the image through any editor before submitting it.**

These models work on the traces a generator or an editor leaves behind: compression and
quantization artifacts, resampling patterns, sensor noise, and local inconsistencies that
are invisible to a human eye. Every one of those traces lives in the exact bytes of the
file. Resizing resamples them away. Re-encoding to JPEG overwrites them with the artifacts
of your own encoder. A thumbnail pipeline, an "optimize images" step, a screenshot of the
image, or a messaging app that recompresses on send can all turn a confident detection
into a clean-looking pass.

Practical rules:

- Submit the original file exactly as you received it, byte for byte.
- Prefer `image_url` pointing at the original asset over anything your pipeline produced.
- If you must send base64, encode the original bytes. Do not decode and re-save.
- Never feed these models a CDN-resized derivative, a cropped avatar, or a screenshot.
- If an image is over the size limit, that is a reason to reject or escalate it, not to
  shrink it and submit anyway. A downscaled submission can return a false clean result,
  which is worse than no result.

The same applies to `ai-edited-image-forgery`, `effort-deepfake-image`,
`effort-deepfake-video`, `document-tampering`, and the document forensics pipeline in
`bynn-document-fraud`. Anything that reasons about manipulation needs the original.

Three related models answer three different questions. `ai-generated-image` asks whether
the whole image was synthesized. `ai-edited-image-forgery` asks whether a real photo was
locally altered. `effort-deepfake-image` targets face swaps specifically. A photo that
passes one can fail another, so run the one that matches your threat, or run all three
when the stakes justify it.

## Video costs frames

`fps` controls how many frames per second are extracted, from 1 to 10. Every frame is
work. Start at 1 for a long recording and raise it only when you are hunting something
brief. A 10-minute clip at `fps: 10` is six thousand frames.

## Batching

`image_urls` and `base64_images` accept arrays for image models. One request, one result
set, far less overhead than a loop. Use it for backfills and library scans.

## Reading results

Every model has its own category set, which is why `/moderation/models/{api_name}` exists.
Write your parsing against that response instead of pattern-matching keys you saw once.

Scores are probabilities. Pick thresholds per model and per surface: the bar for
auto-removing an upload is not the bar for flagging it to a human. Log the raw scores so
you can move a threshold later without reprocessing.

## Choosing this over the dedicated endpoints

`age-detection` and `minor-detection` here give you raw per-face output, which suits bulk
screening. When a decision is being made about a specific person, use
`bynn-age-verification`. When the question is whether a document is forged rather than
whether an image is unsafe, use `bynn-document-fraud`: its pipeline runs many detectors
and returns one risk score, instead of one model at a time.

## Over MCP

`list_all_moderation_models`, `create_moderation_inference`, `get_moderation_inference`,
and the shortcut `detect_ai_generated_image`. See `bynn-mcp`.
