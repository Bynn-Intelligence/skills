---
name: bynn-kyc-sessions
description: >-
  Run a full identity verification (KYC) on a real person with Bynn hosted sessions:
  create a session with a KYC level, hand the applicant a URL or QR code, track
  progress over websocket or webhooks, and collect the outcome. Covers session
  creation and update, consent, liveness, ID document capture, NFC chip reads,
  email/phone/address/proof-of-funds sub-verifications, preflight, and cancellation.
  Use for onboarding an end user, an age-gated signup with identity, or any flow
  where a person proves who they are.
metadata:
  author: bynn
  version: "1.0.0"
license: MIT
---

# Identity verification sessions

A session is one applicant going through one verification flow. You create it, the
applicant completes it in a hosted page, and the outcome reaches you by webhook.

Base: `https://api.bynn.com/v1`

## Before you start

A session needs a **KYC level**, which defines what the applicant must provide (ID
document, liveness, proof of address, and so on). Levels are configured once in the
dashboard at `https://dashboard.bynn.com/setting/product/kyc` and referenced by token.
There is no API to invent a level inline. If `kyc_level` is wrong you get a 404, not a
validation error.

## Create a session

Public key. This is the one endpoint safe to call from a client you do not control.

```bash
curl -X POST https://api.bynn.com/v1/sessions \
  -H "Authorization: Bearer <YOUR_PUBLIC_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "kyc_level": "<level token>",
    "unique_id": "user_8123",
    "first_name": "Ada",
    "last_name": "Lovelace",
    "email_address": "ada@example.com",
    "phone_number": "+441234567890",
    "i18n": "en",
    "generate_qr": true
  }'
```

Only `kyc_level` is required. Everything else is optional and worth sending: prefilled
applicant details cut drop-off, and `unique_id` is how you match the result back to your
own user row later. Set it now, because you cannot add it retroactively.

Response:

| Field | Use |
|---|---|
| `session_id` | The session token. Store it against your user. |
| `url` | Where the applicant completes the flow. Redirect or link to it. |
| `qr_base64_png` | Base64 PNG, present when `generate_qr` was true. For desktop to mobile handoff. |
| `websocket_url` | Live status stream for this session, for a progress UI. |
| `branding` | Your configured colors and logo, if you are rendering your own shell. |

## Hand it to the applicant

Three normal patterns:

- **Redirect.** Send the browser to `url`. Simplest, and the default.
- **QR.** Render `qr_base64_png` on desktop so the applicant continues on a phone, which
  is where the camera is. Use this whenever the flow needs liveness or document capture.
- **SMS.** `POST /sessions/{session_id}/send_sms` delivers the link to the phone number
  on the session.

## Track progress

Two channels, and they answer different questions.

- **Websocket** at `websocket_url`, for a live progress UI while the applicant is in the
  flow. Presentation only.
- **Webhooks**, for the outcome. This is the channel your backend must trust. The
  applicant's browser can close at any moment; the webhook still arrives.

Events on a session: `session.created`, `session.consent.accept`,
`session.consent.reject`, `session.liveness.started`, `session.liveness.accepted`,
`session.liveness.rejected`, `session.completed`, `session.canceled`, `session.expired`.
Document outcomes arrive separately as `identity_document.*`, `proof_of_address.*`, and
`proof_of_funds.*`. See `bynn-webhooks` for delivery and signature verification.

Never treat a redirect back to your site as proof of success. It means the applicant
reached the end of the flow, not that they passed.

## Read a session

```bash
curl https://api.bynn.com/v1/sessions/<session_id>
```

Returns the session record. A `410` means the session was canceled or consent was
refused, and is a normal terminal state rather than an error to retry.

## Update or cancel

```bash
# update applicant details on an in-flight session
curl -X POST https://api.bynn.com/v1/sessions/<session_id> \
  -H "Content-Type: application/json" \
  -d '{ "email_address": "new@example.com", "i18n": "sv" }'

# cancel
curl -X DELETE https://api.bynn.com/v1/sessions/<session_id>
```

Update accepts the same applicant fields as create, plus `country_code`. It cannot change
`kyc_level`: to change what is being asked for, cancel and create a new session.

## Sub-verifications

When your KYC level includes them, these run inside the session. Each is scoped to the
session token, so nothing here is addressable without it.

| Step | Endpoint |
|---|---|
| Consent | `PATCH /sessions/{session_id}/consent` |
| Email | `POST` to send a code, `PATCH` to check it, on `/sessions/{session_id}/email_verification` |
| Phone | Same pair on `/sessions/{session_id}/phone_verification` |
| Address | `POST /sessions/{session_id}/address_verification` |
| Proof of funds | `POST /sessions/{session_id}/funds_verification` |
| Liveness | `POST /sessions/{session_id}/liveness/start`, then `/liveness/complete` |
| Media upload | `POST /sessions/{session_id}/media` |
| Preflight | `GET /sessions/{session_id}/preflight` |

Consent is a gate, not a formality. Until it is accepted the session refuses to progress
and reads return `410`.

## Building your own capture UI

Most integrations use the hosted flow and never touch this section. If you are rendering
capture yourself:

- `GET /sessions/{session_id}/preflight` tells you what screen to show next. It returns
  `screen`, `requirement`, `entity_id_document_type`, and `entity_id_state`, which is how
  you know whether a document was accepted or needs resubmission (for example
  `front_received_but_needs_resubmission`).
- `POST /sessions/{session_id}/media` uploads a capture. It requires
  `media_base64_strict` and `app_screen`, where `app_screen` names the screen the media
  came from. Accepts jpg, jpeg, png, mov, mp4, pdf, and webm.
- Drive the loop as preflight, capture, upload, preflight again. Do not assume the order
  of screens: the level configuration decides it, and it can change without a code change
  on your side.

## NFC chip reads

`POST /v1/nfc` submits a passport or ID chip read against a session. It expects the raw
data groups (`rawDG1`, `rawDG2`, `rawDG14`, `rawDG15`, `rawSOD`), the parsed identity
fields, `authenticationStatus`, and `hashVerification`.

Send the raw data groups even though you are also sending parsed fields. The parsed
values are convenience; the chip's own signed data is what gets verified server side. A
submission with only parsed fields proves nothing about the document.

## Common mistakes

- Using the private key to create a session. The endpoint takes the public key.
- Treating `session_id` as secret. It is not a credential, it is an identifier. The public
  key plus the session token is what a client legitimately holds.
- Polling `GET /sessions/{session_id}` in a loop for the verdict. Use webhooks.
- Skipping `unique_id`, then trying to match a webhook back to a user by name or email.
