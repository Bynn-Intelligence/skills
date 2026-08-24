# Bynn

Skills for integrating the [Bynn](https://www.bynn.com) identity platform: KYC sessions,
document fraud detection, age verification, content moderation, face search, AutoDoc
invitations, and webhook verification. Bundles the Bynn MCP server.

## Install

```
/plugin marketplace add Bynn-Intelligence/skills
/plugin install bynn@bynn
```

Any agent, via the skills CLI:

```bash
npx skills add Bynn-Intelligence/skills --skill bynn
```

## Connect the MCP server

Installing skills does not connect the MCP server. Connect it separately to get Bynn's
143 tools:

```bash
claude mcp add --transport http bynn https://mcp.bynn.com
```

Then run `/mcp` and sign in. The endpoint is the root path; appending `/mcp` returns a 404.
For headless use, pass a token from `https://dashboard.bynn.com/authenticate` as an
`Authorization: Bearer` header instead. Full details are in the `bynn-mcp` skill.

## Skills

| Skill | Covers |
|---|---|
| `bynn` | Router. Auth model, key families, test versus live mode, errors. Start here. |
| `bynn-mcp` | Connecting an agent to the MCP server and driving Bynn through tools. |
| `bynn-kyc-sessions` | Hosted identity verification, liveness, NFC chip reads, preflight. |
| `bynn-web-sdk` | Embedding verification in a website with `@bynn-intelligence/websdk`. |
| `bynn-document-fraud` | Forgery, tampering, and AI-generation analysis of documents. |
| `bynn-age-verification` | Age estimation and minor detection, selfie and liveness. |
| `bynn-moderation` | Detection models across image, video, text, and audio. |
| `bynn-face-search` | Face collections, enrollment, and 1:N search. |
| `bynn-autodoc` | Document requests sent over email or SMS. |
| `bynn-webhooks` | Payloads, the event catalogue, and signature verification. |

## Credentials

No credential ships with this plugin. Each skill states which key it needs and where to
get it. API keys come from `https://dashboard.bynn.com`; the agent token for MCP comes
from `https://dashboard.bynn.com/authenticate`.

Keys are prefixed so you always know what you hold: `private_`, `public_`, and their
`private_sandbox_` and `public_sandbox_` test-mode counterparts. There is no mode switch
and no separate base URL; the key selects the environment.

## Two rules worth knowing before you build

**Never preprocess media.** Do not resize, crop, re-encode, or strip metadata before
submitting an image or document for fraud, tampering, or AI-generation analysis. Those
detectors read artifacts that live in the exact bytes of the original file, and processing
destroys them silently, so the result comes back looking clean.

**The browser is never the verdict.** SDK callbacks run on the visitor's own machine.
Confirm every result server side, or take the webhook, before unlocking anything.

## Documentation

`https://docs.bynn.com`, with the full spec at `https://api.bynn.com/openapi.json`.
