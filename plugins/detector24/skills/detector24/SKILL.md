---
name: detector24
description: >-
  Integrate Detector24 detection models: discover a model in the catalogue, read
  its input_schema and output_schema to build the request and parse the response,
  submit content asynchronously, and read results. Covers image, video, audio, and
  text models including AI-generated media, deepfakes, nudity, violence, weapons,
  drugs, OCR, and duplicate detection, plus the rule that media must never be
  resized or re-encoded before submission. Use for any Detector24 or content
  detection integration.
metadata:
  author: bynn
  version: "0.1.0"
license: MIT
---

# Detector24

Detection and moderation models for image, video, audio, and text. One API, one key, many
models.

| Thing | Value |
|---|---|
| Dashboard and API keys | `https://detector24.ai/app` |
| Model catalogue | `https://detector24.ai/model-catalogue` |
| Docs | `https://detector24.ai/docs` |
| API base | `https://api.bynn.com/v1` |
| Auth | `Authorization: Bearer <your key>` |

## The integration pattern

Do not hardcode a request shape from an example you saw once. **Every model publishes its
own contract**, and the catalogue is how you read it.

1. Find the model, and read its `input_schema` and `output_schema`.
2. Build your request from `input_schema.parameters`.
3. Submit, preferring the async endpoint.
4. Parse the response against `output_schema.fields`.

This is what makes an integration survive a new model version. Code written against a
single hardcoded example breaks the first time a field is added.

## 1. Read the catalogue

```bash
# every model available to your account
curl https://api.bynn.com/v1/moderation/models/all \
  -H "Authorization: Bearer <YOUR_KEY>"

# one model, with its full contract
curl https://api.bynn.com/v1/moderation/models/ai-generated-image \
  -H "Authorization: Bearer <YOUR_KEY>"
```

A model entry carries everything you need to integrate it:

| Field | Why it matters |
|---|---|
| `api_name` | The identifier you pass as `model`. |
| `moderation_type` | `image`, `video`, `audio`, or `text`. Decides which input field to use. |
| `input_schema.parameters` | Name, type, required, description, and an example per parameter. |
| `output_schema.fields` | The exact response shape, including nested properties. Write your parsing against this. |
| `example_request`, `example_response` | Working request and response for this model. |
| `supported_formats` | Accepted file types. Check before you send. |
| `max_file_size_mb` | Hard ceiling for this model. |
| `require_plan` | The plan tier this model needs. A 403 usually traces here. |
| `accuracy`, `avg_response_time_ms` | For choosing between models and setting timeouts. |
| `is_active`, `version` | Whether it is live, and which version you are integrating. |
| `documentation` | Longer per-model notes when they exist. |

Filter `/models/all` by `moderation_type` to list one modality. Cache the catalogue,
refresh it on a schedule, and log the `version` you integrated against.

## 2. Submit, asynchronously by default

Two endpoints:

| Endpoint | Returns | Use it for |
|---|---|---|
| `POST /moderation/infer_async` | `202` with an inference token | Default. Nearly everything. |
| `POST /moderation/infer` | The result inline | Small interactive checks where a person is waiting. |

**Use `infer_async` whenever you can.** Same parameters, a far looser rate limit because
the work is paced by the inference queue, and no held connection. The synchronous endpoint
ties up a connection on both sides for the entire inference, which is how a video model or
a batch turns into timeouts the moment you have load.

```bash
curl -X POST https://api.bynn.com/v1/moderation/infer_async \
  -H "Authorization: Bearer <YOUR_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ai-generated-image",
    "image_url": "https://example.com/file.jpg",
    "idempotency_key": "scan-8123"
  }'
# -> 202 { "token": "...", "status": "pending"... }
```

Then read `GET /moderation/inference/{token}`. Collect tokens, do other work, come back.
Back off between reads instead of hammering one token, and never long-poll.

Async gives you real backpressure: a `429` with `type: "queue_full"` means too much
outstanding work, and the response carries `Retry-After`. Honour it. The synchronous
endpoint has no equivalent, so overload there just looks like timeouts.

Set `idempotency_key` on every submit. A retry of an already-accepted request returns the
existing record instead of queueing a duplicate, and that holds even while you are being
throttled, which is precisely when clients retry.

## 3. Inputs by modality

| Modality | Fields |
|---|---|
| Image | `image_url`, `base64_image`, or `image_urls` / `base64_images` to batch |
| Video | `video_url` or `base64_video`, plus optional `fps` (1 to 10) |
| Text | `content` |
| Audio | `audio_url` or `base64_audio` |
| PDF | `base64_pdf`, for the OCR model, processed per page |

Send one input, matched to the model's `moderation_type`. Batch image arrays in one
request rather than looping: same work, far less overhead.

`fps` costs you real compute. Every extracted frame is an inference. Start at 1 for long
recordings and raise it only when hunting something brief. A 10-minute clip at `fps: 10`
is six thousand frames.

## Never preprocess the media

This is the single biggest cause of missed detections, and it fails silently.

**Do not resize, crop, re-encode, re-compress, strip metadata, or run media through an
editor before submitting it.** Send the original bytes.

These models read the traces a generator or an editor leaves behind: compression and
quantization artifacts, resampling patterns, sensor noise, and local inconsistencies no
human eye can see. All of it lives in the exact bytes of the file. Resizing resamples it
away. Re-encoding overwrites it with your own encoder's artifacts. A thumbnail pipeline,
an "optimize images" build step, a screenshot, or a messaging app that recompresses on
send will each turn a confident detection into a clean-looking pass.

- Submit the original file exactly as received, byte for byte.
- Prefer `image_url` pointing at the original asset over anything your pipeline produced.
- Encoding to base64 is fine. Decoding and re-saving is not.
- Never submit a CDN-resized derivative, a cropped avatar, or a screenshot.
- Over `max_file_size_mb`? Reject or escalate. Do not shrink it and submit anyway: a
  downscaled submission can come back clean, which is worse than no answer at all.

This applies to every detector that reasons about manipulation: `ai-generated-image`,
`ai-edited-image-forgery`, `effort-deepfake-image`, `effort-deepfake-video`,
`document-tampering`, and the voice and music detectors.

## What the models cover

Confirm names against the catalogue before depending on one.

**Image.** `ai-generated-image`, `ai-edited-image-forgery`, `effort-deepfake-image`,
`nudity-detection`, `weapons-detection`, `drugs-detection`, `alcohol-detection`,
`smoking-detection`, `gambling-detection`, `military-detection`, `money-detection`,
`vehicle-detection`, `people-counting`, `destruction-fire-detection`,
`graphic-language-detection`, `content-rating`, `document-tampering`,
`document-liveness`, `document-classifier`, `vlm-ocr`, `vlm-violence-detection`,
`age-detection`, `minor-detection`, `face-occlusion-detection`,
`face-redaction`, `face-redaction-minors`,
`wanted-person-detection-image`.

**Video.** `effort-deepfake-video`, `face-liveness`, `video-content-rating`,
`vlm-video-violence-detection`, `wanted-person-detection`,
`bynn-cctv-abnormality-crime`.

**Text.** `ai-generated-text`, `fake-news-detection`, `fraud-text-detection`,
`advanced-sentiment-analysis`, `mental-health-detection`,
`pii-solicitation-detection`, `bynn-csam-text`.

**Audio.** `voice-deepfake-detection`, `voice-safety-detection`, `ai-generated-music`.

### Picking between the AI-image detectors

Three models, three different questions:

- `ai-generated-image`: was the whole image synthesized?
- `ai-edited-image-forgery`: was a real photo locally altered?
- `effort-deepfake-image`: is this a face swap?

An image can pass one and fail another. Run the one matching your threat, or all three
when the stakes justify it.

## 4. Read results against the schema

Every model has its own output fields, which is exactly why `output_schema` exists. Parse
against it rather than pattern-matching keys from a sample.

Scores are probabilities, not verdicts. Set thresholds per model and per surface: the bar
for auto-removing an upload is not the bar for flagging it for review. Store the raw
scores so you can move a threshold later without reprocessing everything.

## Errors

| Status | Cause |
|---|---|
| 401 | Missing or invalid key. |
| 402 | Balance exhausted. Top up, then retry. |
| 403 | Model needs a higher plan. Check `require_plan`. |
| 413 / 415 | Over `max_file_size_mb`, or a type not in `supported_formats`. |
| 422 | Parameters do not match `input_schema`. |
| 429 | Rate limited, or `queue_full` with `Retry-After`. |

Do not retry 401, 402, 403, or 422.

## Related

Detector24 runs on the Bynn platform, so the same models are reachable through the Bynn
API and MCP server. For document forgery as a single pipeline with one risk score rather
than one model at a time, see the `bynn-document-fraud` skill.
