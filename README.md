# Bynn Agent Skills

Official [Agent Skills](https://agentskills.io) for **Bynn**, **Agemin**, and
**Detector24**. They teach any coding agent how to integrate identity verification,
document fraud detection, age verification, and content detection correctly, including the
parts that are easy to get subtly and dangerously wrong.

Works with Claude Code, Cursor, Codex, Copilot, Gemini CLI, OpenCode, Windsurf, Zed, and
every other agent the `skills` CLI supports.

## Install

Any agent:

```bash
npx skills add Bynn-Intelligence/skills
```

Pick a single product:

```bash
npx skills add Bynn-Intelligence/skills --skill bynn
npx skills add Bynn-Intelligence/skills --skill agemin
npx skills add Bynn-Intelligence/skills --skill detector24
```

Claude Code, with the bundled MCP server:

```
/plugin marketplace add Bynn-Intelligence/skills
/plugin install bynn@bynn
```

## What is in here

### `bynn`

The identity platform. Start with the `bynn` skill: it routes to the rest.

| Skill | Covers |
|---|---|
| `bynn` | Router. Auth model, API base, errors, conventions. |
| `bynn-mcp` | Connecting an agent to `mcp.bynn.com` and driving Bynn through tools. |
| `bynn-kyc-sessions` | Hosted identity verification, liveness, NFC chip reads, preflight. |
| `bynn-web-sdk` | Embedding verification in a website with `@bynn-intelligence/websdk`. |
| `bynn-document-fraud` | Forgery, tampering, and AI-generation analysis of documents. |
| `bynn-age-verification` | Age estimation and minor detection, selfie and liveness. |
| `bynn-moderation` | Every detection model over image, video, text, and audio. |
| `bynn-face-search` | Face collections, enrollment, and 1:N search. |
| `bynn-autodoc` | Document requests sent over email or SMS. |
| `bynn-webhooks` | Payloads, the event catalogue, and signature verification. |

### `agemin`

Biometric age verification for websites and apps.

| Skill | Covers |
|---|---|
| `agemin` | Router. Asset ID versus private key, and why the browser result is not proof. |
| `agemin-web-sdk` | `@bynn-intelligence/agemin-sdk`, age gating, SEO bypass, React and Vue. |
| `agemin-api` | Server-side confirmation, email and selfie checks, reference lookups. |

### `detector24`

Detection models for image, video, audio, and text.

| Skill | Covers |
|---|---|
| `detector24` | Reading a model's `input_schema` and `output_schema`, async submission, and the rule that media must never be preprocessed. |

## Credentials

Nothing here ships a credential. Each skill says which key it needs and where to get it.

| Product | Get keys at |
|---|---|
| Bynn | `https://dashboard.bynn.com` (agent token at `/authenticate`) |
| Agemin | `https://agemin.com/app` |
| Detector24 | `https://detector24.ai/app` |

For the bundled MCP server in Claude Code, export your token before starting the session:

```bash
export BYNN_API_TOKEN="<token from https://dashboard.bynn.com/authenticate>"
```

## Two rules worth reading before you build

**Never preprocess media.** Do not resize, crop, re-encode, or strip metadata before
submitting an image, video, or document for fraud, tampering, or AI-generation analysis.
Those detectors read artifacts that live in the exact bytes of the original file, and
processing destroys them silently. The result comes back looking clean.

**The browser is never the verdict.** SDK callbacks run on the visitor's own machine.
Confirm every result server side before unlocking anything.

## Documentation

- Bynn: `https://docs.bynn.com`, spec at `https://api.bynn.com/openapi.json`
- Agemin: `https://agemin.com/docs`
- Detector24: `https://detector24.ai/docs`

## License

MIT. See [LICENSE](LICENSE).
