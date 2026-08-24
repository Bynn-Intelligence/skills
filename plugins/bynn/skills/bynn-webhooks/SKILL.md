---
name: bynn-webhooks
description: >-
  Receive and verify Bynn webhooks: the payload shape, the event catalogue,
  verifying the X-Bynn-Signature detached RS256 JWT against the raw request body,
  deduplicating with Idempotency-Key, and handling retries. Use when building the
  endpoint that receives Bynn callbacks, when signature verification fails, or when
  events arrive twice or out of order.
metadata:
  author: bynn
  version: "1.0.0"
license: MIT
---

# Webhooks

Webhooks are how outcomes reach you. Sessions, documents, and age verifications all
finish asynchronously, and the browser that started them may be long gone. Take the
webhook. Do not poll for a verdict you could have been told about.

## Payload

```json
{
  "event_id": "8f1c...",
  "created_at": "2026-08-24T10:12:33Z",
  "event_type": "document.analyzed",
  "resource": { "...": "the record this event is about" },
  "organization": { "id": "org_...", "name": "Acme" },
  "jwt": "<full-payload token>"
}
```

Headers on every delivery:

| Header | Meaning |
|---|---|
| `X-Bynn-Signature` | Detached RS256 JWT over a digest of the body. Verify this. |
| `Idempotency-Key` | Stable per logical event, identical across retries. Deduplicate on it. |
| `X-Webhook-Token` | Same value, for correlation in logs. |

## Verify the signature

`X-Bynn-Signature` is a JWT signed RS256 with Bynn's private key. Its claims:

| Claim | Value |
|---|---|
| `iss` | `bynn.com` |
| `sub` | the `event_id` |
| `jti` | the webhook token, matching `Idempotency-Key` |
| `iat`, `exp` | issued at, and 24 hours later |
| `v` | `2` |
| `sha256` | hex SHA-256 digest of the exact raw request body |

Verification, in order:

1. Capture the **raw** request body before any JSON parsing. This is the step that breaks
   most integrations: a framework that parses and re-serializes changes the bytes, and the
   digest will not match.
2. Verify the JWT against Bynn's published RS256 public key. Reject on a bad signature or
   an expired token.
3. Compute `sha256` of the raw body and compare it, constant time, against the `sha256`
   claim.
4. Only then parse the body.

```python
import hmac, hashlib, jwt   # PyJWT

def verify(raw_body: bytes, header: str, public_key: str) -> dict:
    claims = jwt.decode(header, public_key, algorithms=["RS256"], issuer="bynn.com")
    digest = hashlib.sha256(raw_body).hexdigest()
    if not hmac.compare_digest(digest, claims["sha256"]):
        raise ValueError("body digest mismatch")
    return claims
```

```javascript
import crypto from 'node:crypto';
import jwt from 'jsonwebtoken';

// express: app.post('/hooks/bynn', express.raw({ type: 'application/json' }), handler)
function verify(rawBody, header, publicKey) {
  const claims = jwt.verify(header, publicKey, { algorithms: ['RS256'], issuer: 'bynn.com' });
  const digest = crypto.createHash('sha256').update(rawBody).digest('hex');
  const a = Buffer.from(digest), b = Buffer.from(claims.sha256);
  if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) throw new Error('body digest mismatch');
  return claims;
}
```

The signature is **detached**, meaning the header carries only the digest, not the
payload. That keeps it around 800 bytes no matter how large the event is. A header that
embedded the whole payload would exceed the 8 KB per-header limit that nginx and Apache
default to, and the proxy would reject the delivery with a 400 your application never
sees.

The body also carries a `jwt` field, a full-payload token kept for older integrations. To
verify from it instead: parse the body, remove the `jwt` key, and compare the remainder
against the token's `data` claim. Prefer the header. It lets you verify before parsing,
which is the safer order.

## Deduplicate

`Idempotency-Key` is stable across retries of the same logical event, so a retry is not a
new event. Store processed keys and return 200 on a repeat without doing the work again.
Do not deduplicate on `event_id` alone and do not assume ordering: events can arrive out
of order, and a retry of an earlier event can land after a later one.

## Respond fast

Return 2xx as soon as you have verified and persisted the event. Do the real work in a
background job. A handler that runs a slow query inline eventually times out, gets
retried, and multiplies the load that caused the timeout.

Any non-2xx triggers the retry schedule, which escalates to multi-hour intervals over
roughly a day. Because signing happens per delivery attempt, a retry always carries a
fresh, unexpired token.

## Event catalogue

**Sessions.** `session.created`, `session.completed`, `session.canceled`,
`session.expired`, `session.consent.accept`, `session.consent.reject`,
`session.liveness.started`, `session.liveness.accepted`, `session.liveness.rejected`,
`session.id_document_front.received` / `.accepted` / `.rejected`,
`session.id_document_back.received` / `.accepted` / `.rejected`, `session.poa.received` /
`.accepted` / `.rejected`.

**Documents.** `document.analyzed`, `document.rejected`, `document.monitoring_event`,
`identity_document.received`, `identity_document.analyzed`, `identity_document.approved`,
`identity_document.rejected`, `identity_document.expired`,
`identity_document.needs_attention`, `identity_document.in_bynn_review_queue`,
`proof_of_address.*`, `proof_of_funds.*`.

**Dossiers and decisions.** `dossier.created`, `dossier.open`, `dossier.completed`,
`dossier.approved`, `dossier.rejected`, `dossier.needs_attention`, `dossier.canceled`,
`dossier.archived`, `dossier.expired`, `decision.approved`, `decision.rejected`,
`decision.challenge`.

**Screening and agents.** `aml.screening.match`, `aml.screening.match_confirmed`,
`aml.screening.match_rejected`, `agent.started`, `agent.analyzed`, `agent.approved`,
`agent.rejected`, `agent.needs_attention`, `agent.error`.

**Age verification.** `age.verification.approved`, `age.verification.rejected`,
`age.verification.error`.

Subscribe to what you act on. Switch on `event_type` and ignore anything unrecognized
rather than failing: new event types get added, and a handler that throws on an unknown
type turns a new feature into an outage.

## Checklist

- [ ] Raw body captured before parsing
- [ ] JWT verified against the published public key, `iss` checked
- [ ] `sha256` compared constant time against the raw body digest
- [ ] `Idempotency-Key` stored and checked before processing
- [ ] 2xx returned quickly, real work queued
- [ ] Unknown `event_type` ignored, not an error
- [ ] Endpoint reachable over HTTPS from the public internet
