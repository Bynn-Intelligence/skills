---
name: agemin-api
description: >-
  Call the Agemin server-side API at https://api.agemin.com/v1: confirm a browser
  verification with GET /agemin/check/status/{sessionToken}, look a result up by
  your own reference with GET /agemin/check/reference/{referenceId}, or run a check
  directly with POST /agemin/check/selfie or POST /agemin/check/email. Covers the
  private key, the response shape, and the retry semantics of a reference lookup.
  Use for any Agemin call made from a backend.
metadata:
  author: bynn
  version: "0.1.0"
license: MIT
---

# Agemin server API

Everything here uses the **private key** from `https://agemin.com/app/api-keys`, format
`age_sk_live_...`, sent as `Authorization: Bearer <key>`. This code runs on your server.
A private key in a browser bundle is a breach.

Base: `https://api.agemin.com/v1`

## Confirm a browser verification

The one call every SDK integration must make. After the SDK reports a result, take
`sessionToken` from it and ask the API what actually happened:

```bash
curl https://api.agemin.com/v1/agemin/check/status/<sessionToken> \
  -H "Authorization: Bearer age_sk_live_..."
```

Grant access from this response, never from the browser callback. See `agemin-web-sdk`.

## Look up by your own reference

When a browser callback never reached you, because the visitor closed the tab or the
network dropped, reconcile with the `reference_id` you generated:

```bash
curl https://api.agemin.com/v1/agemin/check/reference/<referenceId> \
  -H "Authorization: Bearer age_sk_live_..."
```

**Know which session you get back.** A reference maps to many sessions, because a visitor
who fails and retries creates a new one each time. The response returns the latest
**passing** session, not the latest attempt. If nothing passed, it returns the most recent
attempt with `passed: false`.

That is usually what you want, and it is worth stating in your own code, because "latest
attempt" and "latest passing attempt" differ exactly in the case where someone failed and
then succeeded.

## Check directly, no SDK

Two checks you can run entirely server side.

### Selfie

```bash
curl -X POST https://api.agemin.com/v1/agemin/check/selfie \
  -H "Authorization: Bearer age_sk_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": "ast_5b08b274353b92f4",
    "image_base64_strict": "<base64>",
    "reference_id": "user_123"
  }'
```

`asset_id` is required and identifies which website or app the check belongs to. Send
`image_base64_strict` or `image_url`, strict base64 with no line breaks and no `data:`
prefix.

### Email

```bash
curl -X POST https://api.agemin.com/v1/agemin/check/email \
  -H "Authorization: Bearer age_sk_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": "ast_5b08b274353b92f4",
    "email": "user@example.com",
    "reference_id": "user_123"
  }'
```

Age from email signals and activity patterns. No camera, no visitor interaction, and no
biometrics. It is the lightest possible check and the weakest: use it to pre-screen or to
soften a gate, not as the sole control on regulated content. It returns
`face_confidence: null`, which is a useful marker that no face was involved.

## Response shape

Every one of these returns the same envelope:

```json
{
  "status": "ok",
  "reference": "user_123",
  "timestamp": "2026-08-24T18:33:57Z",
  "result": {
    "session_token": "vwGnr6onuMTrQsGGy55aUcCi",
    "age_threshold": 18,
    "verification_status": "pass",
    "confidence": "high",
    "is_adult": true,
    "is_of_age": true,
    "passed": true,
    "face_confidence": 99.9998779296875,
    "domain": "example.com",
    "asset_token": "ast_A6ctvqk5egQtCoZhr5LrWkRm"
  }
}
```

| Field | Use |
|---|---|
| `passed` | The decision. Branch on this. |
| `verification_status` | `pass` and its counterparts. Use it to tell a fail apart from an inconclusive result. |
| `is_of_age` | Met `age_threshold`. |
| `is_adult` | Met the legal adult threshold. |
| `age_threshold` | The threshold this asset is configured for. |
| `confidence` | `high`, `moderate`, `low`. |
| `face_confidence` | Face detection confidence, `null` for an email check. |
| `session_token` | The session this result belongs to. |
| `domain`, `asset_token` | Which site the verification ran on. |

Check `domain` and `asset_token` against the asset you expected. A result is scoped to one
asset, and confirming that closes the gap where a token from somewhere else is replayed at
your endpoint.

Do not branch on `confidence: low` as if it were a pass. Route it to whatever your
fallback is, the same way you would an inconclusive result.

## Webhooks

Age verification outcomes are also delivered as events: `age.verification.approved`,
`age.verification.rejected`, `age.verification.error`. Manage subscriptions in the
dashboard at `https://agemin.com/app`. Signature verification follows the same detached
JWT scheme as the rest of the platform, documented in the `bynn-webhooks` skill.

Webhooks are the right channel for anything asynchronous, for example updating a user
record after the fact. The status check remains the right call for the moment you unlock
content, because it is synchronous and you control when it happens.

## Errors

Same envelope and codes as the rest of the platform: 401 for a bad or missing key, 402
when the balance runs out, 404 for an unknown token or reference, 422 for validation, 429
for rate limiting. Do not retry 401, 402, or 422.
