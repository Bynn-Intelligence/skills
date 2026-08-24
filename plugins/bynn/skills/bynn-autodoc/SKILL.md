---
name: bynn-autodoc
description: >-
  Ask a customer to submit documents over email or SMS with Bynn AutoDoc
  invitations: create an invitation against a workflow token, track it through its
  lifecycle statuses, resend it, and link the resulting dossier back to your own
  record. Use when you need a person to upload documents without building an upload
  flow yourself, for onboarding, remediation, or document collection.
metadata:
  author: bynn
  version: "0.1.0"
license: MIT
---

# AutoDoc invitations

An invitation sends someone a link over email or SMS. When they open it, a workflow runs
and produces a dossier. You never build an upload page.

Base: `https://api.bynn.com/v1`

## Create

```bash
curl -X POST https://api.bynn.com/v1/autodoc/invitations \
  -H "Authorization: Bearer <YOUR_PRIVATE_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "workflowToken": "wf_...",
    "channel": "email",
    "recipient": "customer@example.com",
    "reference": "order-8123",
    "locale": "sv"
  }'
```

| Parameter | Required | Notes |
|---|---|---|
| `workflowToken` | yes | The workflow to start, `wf_...`. Configured in the dashboard. |
| `channel` | yes | `email` or `sms`. |
| `recipient` | yes | Email address, or a phone number in E.164 when `channel` is `sms`. |
| `reference` | no | Your own identifier, echoed back on reads and events. |
| `locale` | no | IETF language tag for the message. |

Set `reference`. It is the only thing that ties the invitation, and the dossier it
produces, back to your own record without name matching.

Supported locales come from `GET /autodoc/invitations/locales`. Read that list rather than
guessing a tag: an unsupported locale is a validation error, and a wrong one sends a
customer a message they cannot read.

The response is the invitation, with a `token` of the form `adi_...`. That is what you
poll and resend against.

## Read

```bash
curl https://api.bynn.com/v1/autodoc/invitations \
  -H "Authorization: Bearer <YOUR_PRIVATE_KEY>"

curl https://api.bynn.com/v1/autodoc/invitations/<adi_token> \
  -H "Authorization: Bearer <YOUR_PRIVATE_KEY>"
```

## Lifecycle

`status` moves through:

| Status | Meaning |
|---|---|
| `pending` | Created, not yet dispatched. |
| `sent` | Handed to the email or SMS provider. |
| `delivered` | The provider confirmed delivery. |
| `opened` | The recipient opened the link. |
| `started` | They began the workflow. A dossier now exists. |
| `completed` | The linked dossier was approved or completed. |
| `rejected` | The linked dossier was rejected. |
| `failed` | Delivery failed. `errorMessage` says why. |

Timestamps mirror the path taken: `sentAt`, `startedAt`, `completedAt`, `rejectedAt`, and
`createdAt`. `expiresAt` is when the link stops working.

Note the two halves. `pending` through `opened` describe **delivery**. `started`,
`completed`, and `rejected` describe the **dossier**. An invitation that reaches
`delivered` and stops means the message arrived and the person never acted, which is a
follow-up problem, not a technical one.

`dossierToken` appears once the recipient starts. From there, the dossier is the record
that matters, and dossier events carry the outcome. See `bynn-webhooks` for
`dossier.created`, `dossier.completed`, `dossier.approved`, and `dossier.rejected`.

## Resend

```bash
curl -X POST https://api.bynn.com/v1/autodoc/invitations/<adi_token>/resend \
  -H "Authorization: Bearer <YOUR_PRIVATE_KEY>"
```

Resending reuses the same invitation and increments `deliveryAttempts`. It does not create
a new one, so your `reference` mapping stays intact.

Resend for a real reason: a bounce, a wrong address corrected, an expiry approaching.
Chasing an `opened` invitation with repeated sends trains people to ignore them, and on
SMS it costs money per attempt.

## Choosing this over a session

AutoDoc is for **documents**, driven by a workflow, delivered asynchronously to someone
who is not in front of you. An identity verification session is for a **person**
completing a live flow with liveness and an ID check.

If you need someone to prove who they are right now, use `bynn-kyc-sessions`. If you need
a supporting document from a customer sometime this week, use an invitation.

## Over MCP

`create_invitation`, `list_invitations`, `get_invitation`, `resend_invitation`,
`delete_invitation`, `list_invitation_locales`. See `bynn-mcp`.
