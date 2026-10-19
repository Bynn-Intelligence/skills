# Bynn Agent Skills

Official [Agent Skills](https://agentskills.io) for **Bynn**, **ZOREAL**, **Agemin**, and
**Detector24**. They teach any coding agent how to integrate **document fraud detection** for
manipulated, fake and AI-generated PDF and image documents, plus identity verification,
proof-of-human sign-in and meetings, age verification, and content detection, including the
parts that are easy to get subtly and dangerously wrong. The onboarding below also installs
the **DecisionNode** skill from its own repository,
[`decision-node-skills`](https://github.com/Bynn-Intelligence/decision-node-skills).

Works with Claude Code, Cursor, Codex, Copilot, Gemini CLI, OpenCode, Windsurf, Zed, and
every other agent the `skills` CLI supports.

## Onboard an agent in one shot

Paste this line into any coding agent and it installs the Bynn, ZOREAL, DecisionNode,
Agemin and Detector24 skills plus the MCP servers itself, following
[`agent-setup.md`](agent-setup.md):

```
Set up Bynn, ZOREAL, DecisionNode, Agemin and Detector24 for me: fetch https://bynn.com/agent-setup.md and follow it.
```

It covers Claude Code, Cursor, VS Code, Windsurf, Zed, Claude Desktop, ChatGPT, and
headless or CI setups, and tells the agent what to verify before it reports success.

`https://bynn.com/agent-setup.md` serves this repository's
[`agent-setup.md`](agent-setup.md) as it is; its source is
`https://github.com/Bynn-Intelligence/skills/blob/main/agent-setup.md`.

## Install

Any agent:

```bash
npx skills add Bynn-Intelligence/skills
```

The installer shows a picker grouped by product (Bynn, ZOREAL, Agemin, Detector24), so you can
toggle a whole product with one keypress on its group header. Press `a` to select
everything. Nothing is pre-selected, which is the CLI's behaviour and not configurable
per repository.

To skip the picker entirely:

```bash
# every skill, every detected agent, no prompts
npx skills add Bynn-Intelligence/skills --all

# every skill, but choose the agents yourself
npx skills add Bynn-Intelligence/skills --skill '*'

# just one product's skills
npx skills add Bynn-Intelligence/skills --skill bynn --skill bynn-mcp --skill bynn-kyc-sessions
```

Running inside a coding agent skips the picker on its own and installs everything.

Claude Code, with the bundled MCP server:

```
/plugin marketplace add Bynn-Intelligence/skills
/plugin install bynn@bynn
/plugin install zoreal@bynn
```

DecisionNode is installed from its own marketplace:

```
/plugin marketplace add Bynn-Intelligence/decision-node-skills
/plugin install decisionnode@decisionnode
```

## What is in here

### `bynn`

The identity platform. Start with the `bynn` skill: it routes to the rest.

| Skill | Covers |
|---|---|
| `bynn` | Router. Auth model, API base, errors, conventions. |
| `bynn-mcp` | Connecting an agent to `mcp.bynn.com` and driving Bynn through tools. |
| `bynn-document-fraud` | Forgery, tampering, and AI-generation analysis of documents. |
| `bynn-kyc-sessions` | Identity verification sessions: liveness, NFC chip reads, preflight. |
| `bynn-web-sdk` | Embedding verification in a website with `@bynn-intelligence/websdk`. |
| `bynn-age-verification` | Age estimation and minor detection, selfie and liveness. |
| `bynn-moderation` | Every detection model over image, video, text, and audio. |
| `bynn-face-search` | Face collections, enrollment, and 1:N search. |
| `bynn-autodoc` | Document requests sent over email or SMS. |
| `bynn-webhooks` | Payloads, the event catalogue, and signature verification. |

### `zoreal`

ZOREAL, the trust layer that proves a real human is present behind a digital interaction.

| Skill | Covers |
|---|---|
| `zoreal` | Router. What each ZOREAL product proves, and why ZOREAL Verify work goes through the Bynn skills. |
| `zoreal-identify` | Login with ZOREAL: the client libraries, scopes, requiring a live human with `acr`, the assurance block. |
| `zoreal-meet` | The ZOREAL Meet meetings API, host controls and the presence rule, and the ZOREAL Book embed. |

ZOREAL Verify, which includes PDFChecker, runs its checks through the Bynn API today, so
its integration lives in `bynn-document-fraud` and `bynn-kyc-sessions`.

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
| ZOREAL | `https://zoreal.com`: Assets for Login with ZOREAL, Settings, API keys for the Meet API |
| DecisionNode | `https://decisionnode.com/console/keys` |
| Agemin | `https://agemin.com/app` |
| Detector24 | `https://detector24.ai/app` |

### Connect the MCP server

Installing skills does not connect the Bynn MCP server: `npx skills add` copies skill files
only. Connect it separately to get the Bynn tools.

```bash
claude mcp add --transport http bynn https://mcp.bynn.com
```

Then run `/mcp` and sign in. The Claude Code plugin registers this URL for you, but it
stays inert until that sign-in completes. For headless use, pass a token instead:

```bash
claude mcp add --transport http bynn https://mcp.bynn.com \
  --header "Authorization: Bearer $BYNN_API_TOKEN"
```

The endpoint is the root path. Appending `/mcp` returns a 404.

The DecisionNode docs server needs no key or sign-in, and the `decisionnode` plugin
registers it for you:

```bash
claude mcp add --transport http decisionnode-docs https://decisionnode.com/mcp
``` Other clients, including
Claude Desktop, ChatGPT, Cursor, VS Code, Windsurf, and Zed, are covered in the
`bynn-mcp` skill.

## Two rules worth reading before you build

**Never preprocess media.** Do not resize, crop, re-encode, or strip metadata before
submitting an image, video, or document for fraud, tampering, or AI-generation analysis.
Those detectors read artifacts that live in the exact bytes of the original file, and
processing destroys them silently. The result comes back looking clean.

**The browser is never the verdict.** SDK callbacks run on the visitor's own machine.
Confirm every result server side before unlocking anything.

## Documentation

- Agent onboarding: [`agent-setup.md`](agent-setup.md)
- Bynn: `https://docs.bynn.com`, spec at `https://api.bynn.com/openapi.json`
- ZOREAL: `https://zoreal.com/documentation`, sign-in provider at `https://id.zoreal.com/.well-known/openid-configuration`
- DecisionNode: `https://decisionnode.com/docs`, docs MCP server at `https://decisionnode.com/mcp`
- Agemin: `https://agemin.com/docs`
- Detector24: `https://detector24.ai/docs`

## License

MIT. See [LICENSE](LICENSE).
