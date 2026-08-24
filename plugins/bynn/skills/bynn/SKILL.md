---
name: bynn
description: >-
  Start here for any Bynn task: identity verification (KYC) sessions, document fraud
  detection, age verification, content moderation and AI-generated media detection,
  face search, AutoDoc invitations, or webhook verification. Routes to the right
  Bynn skill and covers the authentication model, the API base, and error handling
  shared by all of them. Use it whenever the lane is unclear, and for any multi-step
  integration even when it is not.
metadata:
  author: bynn
  version: "1.0.0"
license: MIT
---

# Bynn (router)

The entry point for the Bynn skills. This skill picks the lane and hands off. Read the
routing table, open the one skill you need, and do not load the rest.

## Quick reference

| Thing | Value |
|---|---|
| REST base | `https://api.bynn.com/v1` |
| OpenAPI 3.0 spec | `https://api.bynn.com/openapi.json` |
| MCP server | `https://mcp.bynn.com/` (Streamable HTTP) |
| Dashboard | `https://dashboard.bynn.com` |
| Get a token | `https://dashboard.bynn.com/authenticate` |
| Docs | `https://docs.bynn.com` |
| Auth header | `Authorization: Bearer <token>` |

## First run: connect before the first call

Do not start a Bynn task and discover mid-way that nothing is set up. Check first.

- **Using MCP?** In Claude Code, `/mcp` must show `bynn` as **Connected**. If it is absent,
  run `claude mcp add --transport http bynn https://mcp.bynn.com` and sign in from `/mcp`.
  Confirm with a `describe_api` call. Full setup, including other clients and bearer
  tokens: `bynn-mcp`.
- **Using REST?** Confirm you hold the right key family for the endpoints you need, per
  the table below.

If neither is available, help set one up rather than guessing at a partial fallback.

## Routing

| Task | Skill |
|---|---|
| Connect an agent to Bynn, pick tools, no hand-written HTTP | `bynn-mcp` |
| Verify a real person's identity end to end, hosted flow, NFC chip read | `bynn-kyc-sessions` |
| Is this ID, passport, invoice, or contract forged or tampered with | `bynn-document-fraud` |
| Is this person old enough, minor detection, age gate | `bynn-age-verification` |
| Is this image, video, audio, or text safe, AI-generated, or a deepfake | `bynn-moderation` |
| Find or match a face across a gallery you control | `bynn-face-search` |
| Ask a customer to upload documents over email or SMS | `bynn-autodoc` |
| Receive and verify Bynn callbacks in your backend | `bynn-webhooks` |

If the task spans several lanes (for example "verify this applicant and screen their ID"),
start with `bynn-kyc-sessions`: a session already runs document forensics, liveness, and
the checks the other lanes expose individually.

## Authentication

Bynn has two credential families. Pick by caller, not by convenience.

**API keys**, from `https://dashboard.bynn.com`. The prefix tells you exactly what a key
is, so you never have to guess from a variable name:

| Key | Use |
|---|---|
| `private_...` | Live, server to server. Reads results, submits media. |
| `public_...` | Live, client-facing. Creates a verification session, little else. |
| `private_sandbox_...` | Test mode, server side. |
| `public_sandbox_...` | Test mode, client side. |

- The **private** key must never reach a browser, a mobile app, or any client you do not
  control. Anyone holding it can read every verification result you own.
- The **public** key is designed to be visible. That is what makes it safe to ship in a web
  or mobile client, and why `POST /sessions` accepts it.

Send either as a Bearer token:

```
Authorization: Bearer private_...
```

HTTP Basic also works, with the key as the username and an empty password, which suits
tooling that only speaks Basic:

```bash
curl -u "private_...:" https://api.bynn.com/v1/documents/<id>
```

Endpoints declare which family they accept. `POST /sessions` takes the public key.
`POST /documents` and the result endpoints take the private key. A public key on a
private-key endpoint returns 401.

### Test mode and live mode

There is **no mode switch and no separate base URL**. You select the environment by using
the matching key, and the two are strictly isolated: a sandbox key cannot read a live
record, and a live key cannot read a sandbox one. Requests made with a sandbox key never
touch live networks and cost nothing.

Keep both pairs in configuration and choose by environment, exactly as you would with any
other payment-style API. Do not hardcode one and swap it at deploy time.

**Dashboard access token**, from `https://dashboard.bynn.com/authenticate`. This is the
token for agents and the MCP server. It acts with your own account's permissions, is
long lived, and the MCP server resolves the right underlying key per tool so you never
handle API keys by hand. Treat it like a password.

## Errors

Every error is `{ "error": { "type": "...", "message": "..." } }`.

| Status | Meaning | Do this |
|---|---|---|
| 401 | Missing or invalid credential | Check the key family. A public key on a private-key endpoint returns 401. |
| 402 | Insufficient balance | Top up in the dashboard, then retry. |
| 403 | Not permitted for this role or plan | Use an account that has the capability. |
| 404 | Not found | Records are addressed by token, never by a numeric id. Check the token. |
| 413 / 415 | Too large or unsupported type | Documents up to 64 MB, and jpg, jpeg, png, or pdf only. |
| 422 | Validation error | Fix the parameters named in the message. |
| 429 | Rate limited | Back off and retry with jitter. |

Do not retry 401, 402, 403, or 422. They will not succeed on a second attempt.

## Conventions that apply everywhere

- **Tokens, not ids.** Every record is addressed by an opaque token (`document_...`,
  `wf_...`, a session token). Do not construct them, store them as integers, or assume
  they are sequential.
- **Async where the work is heavy.** Document analysis and some moderation models return
  a receipt first and a result later. Poll the result endpoint or take a webhook. Never
  block a request thread waiting for one.
- **Base64 must be strict.** Fields named `*_base64_strict` reject line breaks. Use
  strict encoding with no wrapping, and no `data:` URI prefix.
- **Never preprocess media before submitting it.** Do not resize, crop, re-encode, or
  strip metadata. Fraud, tampering, and AI-generation detection read artifacts that live
  in the exact bytes of the original file, and processing destroys them silently: the
  result comes back looking clean. Send the original, or reject the file.
- **Give every call a reference.** `reference_id`, `unique_id`, or `reference` ties a
  Bynn record back to your own row. Set it on creation; you cannot add it later.

## Discovering the rest

The spec is the source of truth and covers every parameter these skills leave out:

```bash
curl -s https://api.bynn.com/openapi.json | jq '.paths | keys'
```

Over MCP, call `describe_api` for the same thing.
