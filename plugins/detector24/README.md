# Detector24

Skills for integrating [Detector24](https://detector24.ai) detection models across image,
video, audio, and text: AI-generated media, deepfakes, nudity, violence, weapons, drugs,
OCR, and more.

## Install

```
/plugin marketplace add Bynn-Intelligence/skills
/plugin install detector24@bynn
```

Any agent, via the skills CLI:

```bash
npx skills add Bynn-Intelligence/skills --skill detector24
```

## Skills

| Skill | Covers |
|---|---|
| `detector24` | Reading a model's `input_schema` and `output_schema` from the catalogue, async submission, batching, and result parsing. |

## How the integration works

Every model publishes its own contract. Read the catalogue rather than hardcoding a request
shape from an example:

```bash
curl https://api.bynn.com/v1/moderation/models/ai-generated-image \
  -H "Authorization: Bearer <YOUR_KEY>"
```

The response carries `input_schema.parameters`, `output_schema.fields`, `example_request`,
`example_response`, `supported_formats`, `max_file_size_mb`, and `require_plan`. Build
requests and parse responses against those, and the integration survives a new model
version.

Keys come from `https://detector24.ai/app`. API base is `https://api.bynn.com/v1`.

## Two rules worth knowing before you build

**Never preprocess media.** Do not resize, crop, re-encode, re-compress, or strip metadata
before submitting. These models read the traces a generator or editor leaves behind:
compression artifacts, resampling patterns, sensor noise. All of it lives in the exact
bytes. A thumbnail pipeline or an "optimize images" step turns a confident detection into a
clean-looking pass, silently. If a file is over the size limit, reject or escalate it
rather than shrinking it.

**Prefer async.** `POST /moderation/infer_async` returns a token immediately and has a far
looser rate limit, because the work is paced by the inference queue. The synchronous
endpoint holds a connection open for the whole inference, which is how a video model turns
into timeouts under load.

## Documentation

`https://detector24.ai/docs`, model catalogue at `https://detector24.ai/model-catalogue`.
