> ## Documentation index
> Bynn API reference: https://docs.bynn.com
> Full OpenAPI 3.0 spec: https://api.bynn.com/openapi.json
> ZOREAL documentation: https://zoreal.com/documentation (site index: https://zoreal.com/llms.txt)
> DecisionNode documentation: https://decisionnode.com/docs (for agents: https://decisionnode.com/llms.txt)
> Fetch the Bynn spec to discover every Bynn endpoint before exploring further.

# Onboard your agent to Bynn

> Official Bynn instructions that install the Bynn, ZOREAL, DecisionNode, Agemin, and
> Detector24 skills and the Bynn and DecisionNode MCP servers into your coding agent in
> one shot.

These are official instructions from Bynn Intelligence for setting up an AI development
environment that integrates document fraud detection for manipulated, fake and
AI-generated PDF and image documents, plus identity verification, proof-of-human sign-in
and meetings, calibrated decisions, age verification, and content detection. They are
published at `https://github.com/Bynn-Intelligence/skills/blob/main/agent-setup.md`, so
you can verify their origin before following them.

The one line a developer pastes into their agent to start this:

```
Set up Bynn, ZOREAL, DecisionNode, Agemin and Detector24 for me: fetch https://raw.githubusercontent.com/Bynn-Intelligence/skills/refs/heads/main/agent-setup.md and follow it.
```

That line asks for all five products, so install all five. When the user asked for only
some of them, install `bynn` plus the ones they named.

Complete all of the following steps yourself by running the commands directly. The only
exceptions are the steps explicitly marked **User step**: in-session commands, OAuth
sign-in and API keys happen on the user's side, so you cannot perform them. Never run a
command that blocks on an interactive prompt, and never ask the user to paste a key or
token into the chat.

Every command below is safe to re-run on a machine where setup already happened.

***

## What gets installed

Five plugins from two marketplaces, eighteen skills, and two hosted MCP servers.

| Plugin | From | Skills | Covers |
|---|---|---|---|
| `bynn` | `Bynn-Intelligence/skills` | `bynn`, `bynn-mcp`, `bynn-document-fraud`, `bynn-kyc-sessions`, `bynn-web-sdk`, `bynn-age-verification`, `bynn-moderation`, `bynn-face-search`, `bynn-autodoc`, `bynn-webhooks` | Document fraud detection, identity verification, moderation, face search, webhooks. Also the API that runs ZOREAL Verify's checks today. |
| `zoreal` | `Bynn-Intelligence/skills` | `zoreal`, `zoreal-identify`, `zoreal-meet` | Login with ZOREAL (proof-of-human sign-in), the ZOREAL Meet meetings API, the ZOREAL Book embed |
| `agemin` | `Bynn-Intelligence/skills` | `agemin`, `agemin-web-sdk`, `agemin-api` | Biometric age verification and age gating |
| `detector24` | `Bynn-Intelligence/skills` | `detector24` | Detection models for image, video, audio, and text |
| `decisionnode` | `Bynn-Intelligence/decision-node-skills` | `decisionnode` | DecisionNode, the decision engine: calibrated yes-or-no, choice, score, number, point and box decisions |

| MCP server | Address | Auth | Gives the agent |
|---|---|---|---|
| `bynn` | `https://mcp.bynn.com` | OAuth sign-in, or a bearer token | The Bynn platform as tools, including the checks behind ZOREAL Verify |
| `decisionnode-docs` | `https://decisionnode.com/mcp` | None | The DecisionNode documentation: `search_docs` and `read_doc` |

DecisionNode's skills and docs server are maintained in their own repository and installed
from there, not copied here. ZOREAL has no MCP server of its own: its Verify checks are
reached through the `bynn` server, and Login with ZOREAL and the Meet API are written as
code from the `zoreal` skills.

Each router skill (`bynn`, `zoreal`, `agemin`, `detector24`, `decisionnode`) points at the
others, so an agent only loads the lane a task needs. No API keys are installed or stored
by any of this.

***

## Agemin is not Bynn: two products, two web SDKs

The single most common integration mistake. Bynn and Agemin each ship a browser SDK, the
package names are one word apart, and searching the Bynn docs for "the Agemin SDK" lands you
on the wrong one. Pick by what the task needs, not by the name closest to hand.

| | Bynn Web SDK | Agemin Web SDK |
|---|---|---|
| Package | `@bynn-intelligence/websdk` | `@bynn-intelligence/agemin-sdk` |
| Import | `import { Bynn } from ...` | `import Agemin from ...` |
| Answers | "Who is this person?" (identity, KYC, document) | "Is this person old enough?" (age only) |
| Credentials | public key + KYC level | Asset ID (`ast_...`) + reference ID |
| Entry call | `Bynn({...}).mount()` | `new Agemin({...}).verify()` / `.validateSession()` |
| Docs | `https://docs.bynn.com` | `https://agemin.com/docs` |
| Skill | `bynn-web-sdk` | `agemin-web-sdk` |

If the request mentions age, an age gate, age verification, or "how old", it is Agemin, so
work from the `agemin` skills and `@bynn-intelligence/agemin-sdk`. If it mentions KYC,
identity, onboarding, or a document check, it is Bynn. When a request just says "the SDK"
and the product is ambiguous, ask which one rather than guessing: the two are not
interchangeable, and the wrong one cannot be made to do the other's job.

### DecisionNode's packages, and a name that is not ours

DecisionNode's official code lives under `github.com/Bynn-Intelligence` (`decision-node-*`)
and its API at `api.decisionnode.com`. The `decisionnode` package on npm and the
`decisionnode` organization on GitHub belong to an unrelated project. Install the SDK the
`decisionnode` skill names for the language, never a package found by searching the name.

***

## Same capability, different products: route by the job

Age, AI-generation, moderation, identity, document forensics and decisions each exist in
more than one product. The wrong lane still returns a plausible answer, so this is the kind
of mistake that fails quietly. Route by the job, not by the first skill whose description
happens to match.

### "Is this document genuine?" is ZOREAL Verify, run through Bynn

ZOREAL Verify is where Bynn's document forensics now live within ZOREAL, and PDFChecker is
a product inside ZOREAL Verify. Its checks run through the Bynn API today, with its
integrated dashboard coming soon. So there is one lane in code, not two:

| Use | When | Skill |
|---|---|---|
| ZOREAL Verify document forensics, PDFChecker, Bynn document fraud detection | A PDF, invoice, statement, contract or ID document: genuine, altered, or machine-generated | `bynn-document-fraud` |
| Detector24 | General media (photos, video, audio, text) rather than a document | `detector24` |

Do not look for a separate ZOREAL Verify or PDFChecker API or SDK, and do not invent one.

### "Who is this person?" lives in two places

| Use | When | Skill |
|---|---|---|
| Bynn KYC sessions (the identity verification in ZOREAL Verify) | You need to verify someone you do not know yet: their government ID, a liveness check and a face match, inside an onboarding flow, with a result your compliance process relies on. | `bynn-kyc-sessions`, `bynn-web-sdk` |
| Login with ZOREAL (ZOREAL Identify) | You want people to sign in as a verified, unique, live human who already holds a ZOREAL ID, and to read age, nationality, name or document fields only with their consent. | `zoreal-identify` |

Login with ZOREAL is a sign-in, not a KYC decision: it hands you verified attributes and how
strongly the login was proven, and the regulatory determination stays yours. For onboarding
a stranger, it is a KYC session. The two compose: verify once with a session, then let
returning users sign in with ZOREAL.

### "Decide what happens next" lives in DecisionNode and inside Bynn

| Use | When | Skill |
|---|---|---|
| DecisionNode | Your own code needs a narrow, calibrated answer to branch on: is this a refund request, which team owns this ticket, how urgent is it, how many items are on the receipt, where in the photo is the package. | `decisionnode` |
| Bynn fraud reasoning agents | AI reasoning over evidence inside a Bynn document fraud or claims review, configured and run on the Bynn platform. | `bynn-mcp` (Reasoning and Fraud Agents tools) |
| Agemin, Detector24, Bynn moderation | The check itself is the product: an age gate, a moderation or AI-generation verdict. | `agemin`, `detector24`, `bynn-moderation` |

DecisionNode's boosters add Agemin's age estimate and Detector24's AI-generated image model
as evidence inside a wider decision. Reach for a booster when age or AI-generation is one
input to a decision your code makes; reach for Agemin or Detector24 when it is the answer
the user asked for.

### "Is this person old enough?" lives in three places

| Use | When | Skill |
|---|---|---|
| Agemin | A self-serve age gate on a site or app: the visitor scans their own face in the browser, the SDK runs the flow, your server confirms. | `agemin`, `agemin-web-sdk`, `agemin-api` |
| Bynn age verification | You already hold a selfie, or want age as one step inside a Bynn identity flow, called server side. | `bynn-age-verification` |
| Bynn moderation age model | Age or minor detection as one signal in a content pipeline that is already scoring other things. | `bynn-moderation` |

Default to Agemin for an actual age gate. Reach for `bynn-age-verification` when the image
is already in hand or age rides along with identity, and for the moderation model only when
age is one of several signals in a trust-and-safety pass. If your users already sign in
with ZOREAL, the `zoreal.age` scope returns `age_over_N` booleans from their verified
document instead (`zoreal-identify`).

### "Is this AI-generated or a deepfake?" lives in three places

| Use | When | Skill |
|---|---|---|
| Detector24 | A general detection pipeline over image, video, audio, or text, picking models from a catalogue. | `detector24` |
| Bynn moderation | The same detection as one call inside a Bynn trust-and-safety flow, sharing Bynn auth and webhooks. | `bynn-moderation` |
| Bynn document fraud (ZOREAL Verify) | The thing under test is a document (ID, passport, invoice, statement), not general media. | `bynn-document-fraud` |

If it is a document, it is `bynn-document-fraud`. For general media, Detector24 and
`bynn-moderation` run the same class of models: choose Detector24 for a standalone detection
product with its own dashboard and catalogue, and `bynn-moderation` when the work already
sits inside Bynn.

### Detector24 vs Bynn moderation

They overlap on purpose. Detector24 is the standalone detection product (`detector24.ai`,
own dashboard and model catalogue). `bynn-moderation` is the same model family reached
through the Bynn API, alongside identity and fraud. The detection is the same either way.
Pick by which platform the rest of the integration lives on, not by the capability, and do
not wire up both for one job.

### KYC vs document fraud, inside Bynn

Two lanes of one product, not competing products. `bynn-document-fraud` answers "is this one
document genuine, altered, or machine-generated". `bynn-kyc-sessions` onboards and verifies
a person end to end, and can run a document check as part of that. Use fraud detection for a
document in isolation, KYC sessions for verifying a human. They compose.

***

Use the correct section for your agent below.

***

## Claude Code

Add the two marketplaces and install the plugins. The plugin commands also register the
`bynn` and `decisionnode-docs` MCP servers, so do not use `npx skills` or `claude mcp add`
here.

```
claude plugin marketplace add Bynn-Intelligence/skills
claude plugin install bynn@bynn
claude plugin install zoreal@bynn
claude plugin install agemin@bynn
claude plugin install detector24@bynn
claude plugin marketplace add Bynn-Intelligence/decision-node-skills
claude plugin install decisionnode@decisionnode
```

Install every plugin the user's request names, in the same setup pass, and do not defer
one. The standard onboarding line names all five. If the user asked for one product only,
install `bynn@bynn` and that product's plugin: "Set up Agemin" is a request to install
`agemin@bynn`, "set up ZOREAL" is `zoreal@bynn`, and "set up DecisionNode" is
`decisionnode@decisionnode`. A plugin the user's task needs but you did not install is a
skill you will not have loaded when you start the work, which is exactly when it is too late
to notice.

Verify:

```
claude plugin list | grep -E -A3 '(bynn|zoreal|agemin|detector24)@bynn|decisionnode@decisionnode'
```

Expect `Status: ✔ enabled` for each. If one is listed but disabled, run
`claude plugin enable <plugin>@<marketplace>`, for example
`claude plugin enable zoreal@bynn`.

> **User step.** Ask the user to run `/reload-plugins` inside Claude Code to activate the
> plugins, then connect the MCP servers with `/mcp`: sign in to **bynn** (OAuth 2.1
> against `dashboard.bynn.com`, so no API key is created or stored), and confirm
> **decisionnode-docs** shows as connected (it needs no sign-in). Wait for the user to
> confirm before reporting the MCP servers as connected.

***

## Other agents

First, install the skills from both repositories:

```
npx -y skills add Bynn-Intelligence/skills --skill '*' --yes --global
npx -y skills add Bynn-Intelligence/decision-node-skills --skill '*' --yes --global
```

Then register the hosted MCP servers for the agent in question. The Bynn endpoint is
`https://mcp.bynn.com` and it is the **root path**: appending `/mcp` returns a 404 that
looks like the server being down. The DecisionNode docs endpoint is
`https://decisionnode.com/mcp`, which needs no key and no sign-in.

### Cursor

Add to `~/.cursor/mcp.json`, or `.cursor/mcp.json` for one project:

```json
{
  "mcpServers": {
    "bynn": {
      "url": "https://mcp.bynn.com"
    },
    "decisionnode-docs": {
      "url": "https://decisionnode.com/mcp"
    }
  }
}
```

### VS Code (GitHub Copilot)

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "bynn": {
      "type": "http",
      "url": "https://mcp.bynn.com"
    },
    "decisionnode-docs": {
      "type": "http",
      "url": "https://decisionnode.com/mcp"
    }
  }
}
```

### Windsurf, Zed, and clients without Streamable HTTP

Bridge through `mcp-remote`:

```json
{
  "mcpServers": {
    "bynn": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.bynn.com"]
    },
    "decisionnode-docs": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://decisionnode.com/mcp"]
    }
  }
}
```

Zed uses `context_servers` with a `command` object rather than `mcpServers`.

### Claude Desktop, claude.ai, and ChatGPT

> **User step.** These connect through the app, not the command line. Ask the user to open
> Settings and add two custom connectors: `https://mcp.bynn.com`, completing the sign-in
> when the browser opens, and `https://decisionnode.com/mcp`, with no sign-in. In ChatGPT,
> this lives under Apps and Connectors with developer mode enabled.

### Headless and CI

Where no browser is available, authenticate the Bynn server with a bearer token instead of
OAuth. The DecisionNode docs server needs nothing.

> **User step.** Ask the user to generate a token at
> `https://dashboard.bynn.com/authenticate` and export it. Do not ask them to paste the
> token into the chat.

```
claude mcp add --transport http bynn https://mcp.bynn.com \
  --header "Authorization: Bearer $BYNN_API_TOKEN"
claude mcp add --transport http decisionnode-docs https://decisionnode.com/mcp
```

If a server of that name already exists, leave it in place.

***

## Keys for the code you will write

None of these are needed to install anything. They are what the application under
development will read from its environment.

> **User step.** Ask the user to set the keys for the products they will build with, in
> the shell profile or secret store that runs their application and tests, and never to
> paste them into the chat. Check one is set with `test -n "$NAME" && echo set`; never
> print a key.

| Product | Variable, by convention | Created at |
|---|---|---|
| Bynn (and ZOREAL Verify's checks) | `BYNN_API_KEY` | `https://dashboard.bynn.com` |
| ZOREAL Meet API | `ZOREAL_API_KEY` | `https://zoreal.com`, Settings, API keys |
| Login with ZOREAL | `ZOREAL_CLIENT_ID` (public) and `ZOREAL_CLIENT_SECRET` | `https://zoreal.com`, Assets, the asset's OAuth2 tab |
| DecisionNode | `DECISIONNODE_API_KEY` (starts with `dn_live_`) | `https://decisionnode.com/console/keys` |
| Agemin | the Asset ID (public) and a private key | `https://agemin.com/app` |
| Detector24 | an API key | `https://detector24.ai/app` |

Optional: to let the agent itself ask DecisionNode questions as tool calls, rather than
writing code that does, the DecisionNode tools server runs locally with
[uv](https://docs.astral.sh/uv/) and the user's key:
`claude mcp add decisionnode -e DECISIONNODE_API_KEY="$DECISIONNODE_API_KEY" -- uvx bynn-decisionnode-mcp`.
Each tool call is a billed DecisionNode request, so set this up only when the user asks.

***

## Verify end to end

Once the user has signed in, confirm the connections with read-only calls that cost
nothing and change nothing:

1. **bynn**: call `describe_api`. It returns the full OpenAPI 3.0 spec and needs no
   authentication, so it proves the transport works.
2. **bynn**: call `get_current_user`. It returns the signed-in account, which is what
   proves the authentication actually completed.
3. **decisionnode-docs**: call `search_docs` with the query `boosters`. Expect hits, each
   with a `path`.

If `describe_api` succeeds but `get_current_user` returns an authentication error, the
server is reachable but the sign-in has not finished. Send the user back to `/mcp`.

These calls check the MCP servers only. A reachable, authenticated MCP is **not** proof
the skills installed: the MCP can already be connected from an earlier session, or bundled
by another client, while the plugins are absent. Do not let a green `get_current_user` stand
in for setup being complete. Confirm the skills separately:

```
claude plugin list | grep -E -A3 '(bynn|zoreal|agemin|detector24)@bynn|decisionnode@decisionnode'
```

Outside Claude Code, check that `npx -y skills list --global` lists `bynn`, `zoreal`,
`agemin`, `detector24` and `decisionnode`.

If the plugins are missing, the verification calls still pass, and you nonetheless begin
the first task with no skills loaded and guess from general knowledge, which is the exact
failure this document exists to prevent.

***

## Report the result

Report what you actually verified. Do not print a checkmark for anything you could not
confirm: the Bynn MCP server stays unauthenticated until the user completes sign-in.

```
┌─ Bynn Agent Setup ───────────────────────────────────────┐
│  ✓ Skills             5 plugins, 18 skills               │
│  ⚠ bynn MCP           needs sign-in: /mcp → bynn         │
│  ✓ decisionnode-docs  search_docs answered               │
│                                                          │
│  → Reload or restart your agent to load the skills       │
└──────────────────────────────────────────────────────────┘
```

Use `✓` verified, `⚠` needs a user action, `✗` failed. Follow the banner with the specific
next action for every non-`✓` line.

***

## Rules the skills enforce

Worth knowing before the first task, because each fails quietly rather than loudly.

**Never preprocess media.** Do not resize, crop, re-encode, or strip metadata before
submitting an image or document for fraud, tampering, or AI-generation analysis. Those
detectors read artifacts that live in the exact bytes of the original file. Processing
destroys them and the result comes back looking clean, which is worse than no result.

**The browser is never the verdict.** SDK callbacks run on the visitor's own machine, so
anyone can call them. Confirm every result server side, or take the webhook, before
unlocking anything. For Login with ZOREAL, that means verifying the signed token on your
backend, including the `acr` level you asked for.

**Keys stay on the server.** Bynn private keys, ZOREAL client secrets and API keys, and
DecisionNode keys never go into a browser, a mobile app or a repository.

***

## Resources

| Resource | URL |
|---|---|
| Skills repository | `https://github.com/Bynn-Intelligence/skills` |
| DecisionNode skills repository | `https://github.com/Bynn-Intelligence/decision-node-skills` |
| Bynn docs | `https://docs.bynn.com` |
| OpenAPI spec | `https://api.bynn.com/openapi.json` |
| Bynn dashboard and API keys | `https://dashboard.bynn.com` |
| Agent access token | `https://dashboard.bynn.com/authenticate` |
| Bynn MCP server | `https://mcp.bynn.com` |
| ZOREAL documentation | `https://zoreal.com/documentation` |
| ZOREAL site index for agents | `https://zoreal.com/llms.txt` |
| Login with ZOREAL provider | `https://id.zoreal.com/.well-known/openid-configuration` |
| DecisionNode docs | `https://decisionnode.com/docs` |
| DecisionNode docs for agents | `https://decisionnode.com/llms.txt` |
| DecisionNode docs MCP server | `https://decisionnode.com/mcp` |
| Agemin docs | `https://agemin.com/docs` |
| Detector24 docs | `https://detector24.ai/docs` |
| Agent Skills specification | `https://agentskills.io` |
