---
name: bynn-age-verification
description: >-
  Estimate age and detect minors from a face image with Bynn: POST
  /age_verification/selfie for a one-shot check, or the liveness flow when the
  selfie must come from a live person rather than an uploaded file. Covers the
  age threshold models, legal_age_21, verification_status and confidence, age
  ranges, and how to pick a fallback when the estimate is uncertain. Use for age
  gates, minor detection, and any "is this person old enough" question.
metadata:
  author: bynn
  version: "1.0.0"
license: MIT
---

# Age verification

Two shapes. Pick by threat model.

- **Selfie check.** One image in, an age estimate out. Fast, no session. Right for a
  soft age gate where the cost of a wrong answer is low.
- **Liveness flow.** The image is captured from a live camera under challenge, so an
  uploaded photo of someone older does not pass. Right for anything regulated.

Base: `https://api.bynn.com/v1`. Private key.

## Selfie check

```bash
curl -X POST https://api.bynn.com/v1/age_verification/selfie \
  -H "Authorization: Bearer <YOUR_PRIVATE_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/face.jpg",
    "age_verification_model": "age_verification_18_years"
  }'
```

Send `image_url` or `image_base64_strict`, not both. Base64 must be strict, with no line
breaks and no `data:` prefix.

### Picking a model

`age_verification_model` selects the threshold the model was trained on, from
`age_verification_12_years` through `age_verification_21_years` in one-year steps
(12, 13, 14, 15, 16, 17, 18, 19, 20, 21).

Choose the threshold you actually need to enforce. A model trained at the boundary you
care about beats reading a raw age estimate and comparing it yourself, because the
decision boundary is where the model is calibrated.

`legal_age_21` is a separate flag. It sets the legal adult threshold for your
jurisdiction, defaulting to 18, and it is what drives `is_adult`. It is not the same as
the model threshold, and setting one does not set the other.

### Reading the result

| Field | Meaning |
|---|---|
| `verification_status` | `pass`, `underage`, `unknown`, `pending`, or `error`. Branch on this. |
| `is_adult` | Boolean against the legal age threshold. |
| `confidence` | `high`, `moderate`, or `low`. |
| `age_estimated` | Single best estimate. A prediction, not a fact. |
| `age_range` | `low` and `high` bounds around the estimate. |
| `face` | Detected face attributes. |
| `liveness` | `status` and `confidence` for whether a real human was in frame. |
| `image_saved`, `biometrics_saved` | Whether anything was retained. |
| `data_destroyed_at` | When the data is or will be destroyed. |

**`unknown` is not a failure and not a pass.** It means the model would not commit, which
happens near the threshold, with poor lighting, occlusion, or no clear face. Treat it as
its own branch and fall back to a stronger check rather than guessing. The same goes for
`pass` with `confidence: low`.

Use `age_range` rather than `age_estimated` when you need to explain a decision. A range
of 17 to 21 around an estimate of 19 is a different situation from 18 to 20, and only the
range shows it.

## Liveness flow

Four calls. The first creates a session, your client runs the capture against it, and you
read the outcome.

```
POST  /age_verification/liveness                                   -> { session_id }
PATCH /age_verification/liveness/{session_id}                      -> credentials + server_time
GET   /age_verification/liveness/{age_verification_id}/complete    -> completion state
GET   /age_verification/liveness/{age_verification_id}             -> the age result
```

`POST /age_verification/liveness` requires `unique_id`, your own identifier for the user.
Set it: it is how the result maps back to your row.

Liveness `status` moves through `created`, then `successful`, `failed`, or `expired`.
Expired is normal when a user abandons the flow, so handle it as its own case rather than
as an error.

## Fallback ladder

Age estimation is probabilistic. Design for the uncertain answer before you ship:

1. Selfie check. `pass` with `confidence: high` clears.
2. `unknown`, `low` confidence, or a range straddling your threshold: escalate to the
   liveness flow.
3. Still uncertain, or the jurisdiction demands documentary proof: run a full identity
   verification with an ID document. See `bynn-kyc-sessions`.

Do not silently deny on `unknown`. That is where false negatives concentrate, and the
users it hits hardest are the ones near the boundary who are legitimately old enough.

## Related

`bynn-moderation` exposes the raw `age-detection` model, which returns per-face `age`,
`from_age`, `to_age`, `is_minor`, and `challenge_25` without the verification wrapper.
Use it for bulk screening of a library of images. Use this skill's endpoints when a
decision is being made about a specific person.

## Over MCP

`verify_age_from_selfie` and `check_age`. See `bynn-mcp`.
