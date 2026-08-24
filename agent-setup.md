> ## Documentation index
> Bynn API reference: https://docs.bynn.com
> Full OpenAPI 3.0 spec: https://api.bynn.com/openapi.json
> Fetch the spec to discover every endpoint before exploring further.

# Onboard your agent to Bynn

> Official Bynn instructions that install the Bynn, Agemin, and Detector24 skills and the
> Bynn MCP server into your coding agent in one shot.

These are official instructions from Bynn Intelligence for setting up an AI development
environment that integrates document fraud detection for manipulated, fake and
AI-generated PDF and image documents, plus identity verification, age verification, and
content detection. They are published at
`https://github.com/Bynn-Intelligence/skills/blob/main/agent-setup.md`, so you can verify
their origin before following them.

Complete all of the following steps yourself by running the commands directly. The only
exceptions are the steps explicitly marked **User step**: in-session commands and OAuth
sign-in happen inside the agent UI, so you cannot perform them. Never run a command that
blocks on an interactive prompt.

Every command below is safe to re-run on a machine where setup already happened.

***

## What gets installed

Three plugins, fourteen skills, and the hosted Bynn MCP server.

| Plugin | Skills | Covers |
|---|---|---|
| `bynn` | `bynn`, `bynn-mcp`, `bynn-document-fraud`, `bynn-kyc-sessions`, `bynn-web-sdk`, `bynn-age-verification`, `bynn-moderation`, `bynn-face-search`, `bynn-autodoc`, `bynn-webhooks` | Document fraud detection, identity verification, moderation, face search, webhooks |
| `agemin` | `agemin`, `agemin-web-sdk`, `agemin-api` | Biometric age verification and age gating |
| `detector24` | `detector24` | Detection models for image, video, audio, and text |

Each router skill (`bynn`, `agemin`, `detector24`) points at the others, so an agent only
loads the lane a task needs. No API keys are installed or stored by any of this.

Use the correct section for your agent below.

***

## Claude Code

Run these two commands to install the skills and register the MCP server in one step. Do
not use `npx skills` or `claude mcp add` here; the plugin commands handle both.

```
claude plugin marketplace add Bynn-Intelligence/skills
claude plugin install bynn@bynn
```

Add the other two plugins if the user works with those products:

```
claude plugin install agemin@bynn
claude plugin install detector24@bynn
```

Verify:

```
claude plugin list | grep -A2 'bynn@bynn'
```

Expect `Status: ✔ enabled`. If the plugin is listed but disabled, run
`claude plugin enable bynn@bynn`.

> **User step.** Ask the user to run `/reload-plugins` inside Claude Code to activate the
> plugins, then connect the MCP server with `/mcp` and sign in to **bynn**. This uses
> OAuth 2.1 against `dashboard.bynn.com`, so no API key is created or stored. Wait for the
> user to confirm before reporting the MCP server as connected.

***

## Other agents

First, install the skills:

```
npx -y skills add Bynn-Intelligence/skills --skill '*' --yes --global
```

Then register the hosted MCP server for the agent in question. The endpoint is
`https://mcp.bynn.com` and it is the **root path**: appending `/mcp` returns a 404 that
looks like the server being down.

### Cursor

Add to `~/.cursor/mcp.json`, or `.cursor/mcp.json` for one project:

```json
{
  "mcpServers": {
    "bynn": {
      "url": "https://mcp.bynn.com"
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
    }
  }
}
```

Zed uses `context_servers` with a `command` object rather than `mcpServers`.

### Claude Desktop, claude.ai, and ChatGPT

> **User step.** These connect through the app, not the command line. Ask the user to open
> Settings, add a custom connector with the URL `https://mcp.bynn.com`, and complete the
> sign-in when the browser opens. In ChatGPT, this lives under Apps and Connectors with
> developer mode enabled.

### Headless and CI

Where no browser is available, authenticate with a bearer token instead of OAuth.

> **User step.** Ask the user to generate a token at
> `https://dashboard.bynn.com/authenticate` and export it. Do not ask them to paste the
> token into the chat.

```
claude mcp add --transport http bynn https://mcp.bynn.com \
  --header "Authorization: Bearer $BYNN_API_TOKEN"
```

***

## Verify end to end

Once the user has signed in, confirm the connection with two read-only calls that cost
nothing and change nothing:

1. Call `describe_api`. It returns the full OpenAPI 3.0 spec and needs no authentication,
   so it proves the transport works.
2. Call `get_current_user`. It returns the signed-in account, which is what proves the
   authentication actually completed.

If `describe_api` succeeds but `get_current_user` returns an authentication error, the
server is reachable but the sign-in has not finished. Send the user back to `/mcp`.

***

## Report the result

Report what you actually verified. Do not print a checkmark for anything you could not
confirm: the MCP server stays unauthenticated until the user completes sign-in.

```
┌─ Bynn Agent Setup ───────────────────────────────────┐
│  ✓ Bynn skills     3 plugins, 14 skills              │
│  ⚠ bynn MCP        needs sign-in: /mcp → bynn        │
│                                                      │
│  ⚡ Reload or restart your agent to load the skills  │
└──────────────────────────────────────────────────────┘
```

Use `✓` verified, `⚠` needs a user action, `✗` failed. Follow the banner with the specific
next action for every non-`✓` line.

***

## Two rules the skills enforce

Worth knowing before the first task, because both fail quietly rather than loudly.

**Never preprocess media.** Do not resize, crop, re-encode, or strip metadata before
submitting an image or document for fraud, tampering, or AI-generation analysis. Those
detectors read artifacts that live in the exact bytes of the original file. Processing
destroys them and the result comes back looking clean, which is worse than no result.

**The browser is never the verdict.** SDK callbacks run on the visitor's own machine, so
anyone can call them. Confirm every result server side, or take the webhook, before
unlocking anything.

***

## Resources

| Resource | URL |
|---|---|
| Skills repository | `https://github.com/Bynn-Intelligence/skills` |
| Bynn docs | `https://docs.bynn.com` |
| OpenAPI spec | `https://api.bynn.com/openapi.json` |
| Bynn dashboard and API keys | `https://dashboard.bynn.com` |
| Agent access token | `https://dashboard.bynn.com/authenticate` |
| MCP server | `https://mcp.bynn.com` |
| Agemin docs | `https://agemin.com/docs` |
| Detector24 docs | `https://detector24.ai/docs` |
| Agent Skills specification | `https://agentskills.io` |
