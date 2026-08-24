---
name: bynn-mcp
description: >-
  Connect an agent to the Bynn MCP server at https://mcp.bynn.com and drive Bynn
  through its 143 tools instead of hand-written HTTP. Covers connecting with OAuth
  or a bearer token, per-client config for Claude Code, Claude Desktop, ChatGPT,
  Cursor, VS Code, Windsurf and Zed, which credential each tool group needs,
  verifying the connection, self-discovery, and when to drop to REST. Use when
  setting up the connection, when a tool returns an authentication error, or when
  choosing between MCP and REST.
allowed-tools: Bash(claude:*), Bash(npx:*), Bash(curl:*)
compatibility: Linux, macOS, Windows
metadata:
  author: bynn
  version: "0.1.0"
license: MIT
---

# Bynn over MCP

The MCP server exposes the whole Bynn platform as 143 structured tools: identity
verification, document fraud detection, age verification, content moderation, face
search, AutoDoc, fraud reasoning agents, and account management. Prefer it over
hand-written HTTP for anything interactive, because it removes key handling and
`describe_api` hands you the full spec on demand.

```
https://mcp.bynn.com
```

**The endpoint is the root path.** Do not append `/mcp`. `https://mcp.bynn.com/mcp` does
not work, and it fails as an immediate 404 that looks like the server being down. The only
other route is `GET /health`.

## Connect

If the server is not connected yet, set it up before starting the task rather than
discovering halfway through that nothing works.

### Claude Code

```bash
claude mcp add --transport http bynn https://mcp.bynn.com
```

Then run `/mcp` and sign in. Adding the server registers the URL; it stays inert until the
sign-in completes.

Add `-s user` to make it available in every project, or `-s project` to commit it to one
repo's `.mcp.json`. Only ever commit the OAuth form or an environment-variable
placeholder, never a literal token.

### Other clients

| Client | How |
|---|---|
| Claude Desktop, claude.ai | Settings, Connectors, Add custom connector, URL `https://mcp.bynn.com`. OAuth starts on first use. |
| ChatGPT | Settings, Apps & Connectors, developer mode, Create, MCP server URL `https://mcp.bynn.com`. |
| Cursor | `~/.cursor/mcp.json` (or `.cursor/mcp.json` per project): `{"mcpServers":{"bynn":{"url":"https://mcp.bynn.com"}}}` |
| VS Code (Copilot) | `.vscode/mcp.json`: `{"servers":{"bynn":{"type":"http","url":"https://mcp.bynn.com"}}}` |
| Windsurf, Zed | Bridge with `npx -y mcp-remote https://mcp.bynn.com` |

Full per-client blocks and the OAuth metadata: [reference/connect.md](reference/connect.md).

### Authentication

Two paths, same tools.

**OAuth 2.1 with PKCE** is the default for connectors. The authorization server is
`dashboard.bynn.com`. Your client opens a browser sign-in, you approve, and it connects as
your dashboard user. Clients supporting Dynamic Client Registration, including Claude and
Cursor, register themselves.

**Bearer token** for server-side, scripted, or self-hosted use. Get one at
`https://dashboard.bynn.com/authenticate` and send it on the connection:

```bash
claude mcp add --transport http bynn https://mcp.bynn.com \
  --header "Authorization: Bearer $BYNN_API_TOKEN"
```

Keep it in an environment variable, never in a committed file.

### Verify before relying on it

Do this first, not after a failed tool call.

- In Claude Code, `/mcp` shows `bynn` as **Connected**, not *Needs authentication*. If it
  shows the latter, sign in there.
- Call `describe_api`. If it returns the OpenAPI spec, the connection is real.
- No `bynn` tools present at all means the server was never added.

If MCP cannot be connected, fall back to the REST API with a private key rather than
limping along on a half-setup. See the `bynn` skill.

## Which credential reaches which tools

Three token types work, and they do not have the same reach. This is the source of most
"connected but the tool still 401s" confusion.

| Token | Prefix | Reach |
|---|---|---|
| Dashboard token (JWT) | none | **Everything.** When a tool needs an API key, the server exchanges the JWT for your organization's keys automatically. |
| Private API key | `private_...` | Product and verification tools: documents, moderation, age results. Not dashboard tools. |
| Public API key | `public_...` | Client-safe session creation only. |

Per tool group:

| Tool group | Minimum credential |
|---|---|
| API keys, billing, users, AutoDoc, reasoning, websites | Dashboard token (JWT) |
| Documents, moderation, face, NFC | Private key or JWT |
| `create_session`, `create_age_verification_session` | Public key or JWT |
| `verify_age_from_selfie`, `get_age_verification_result` | Private key or JWT |
| Session steps: consent, preflight, liveness, uploads | None. The session token in the URL is the credential. |

**Use the dashboard token unless you have a reason not to.** It is the only one that
reaches every group, and it is why the MCP path avoids key handling entirely. Private keys
belong in trusted server-side environments only: never in frontend code, public
repositories, or shared chats.

## Tool surface

143 tools. Start with `describe_api`; it is authoritative and always current. The ones you
will reach for most:

| Goal | Tools |
|---|---|
| Document fraud analysis | `submit_document`, then poll `get_document` |
| Is this image AI-generated | `detect_ai_generated_image` |
| Age or minor detection | `check_age`, `verify_age_from_selfie` |
| Hosted identity verification | `create_session`, `get_session`, `get_session_preflight` |
| Any moderation or detection model | `list_all_moderation_models`, `create_moderation_inference` |
| Face gallery | `create_face_collection`, `enroll_face`, `search_faces` |
| Document requests over email or SMS | `create_invitation`, `get_invitation` |

Groups: Documents (4), Age Verification (5), Content Moderation (12), Face Search (6),
AutoDoc (37), Reasoning and Fraud Agents (25), Billing (14), Users and Account (7),
Websites (8), Agemin Checks (3), Verification Sessions (16), API Keys (3), NFC (1),
Server and Self-Discovery (2).

Image inputs accept `file_path`, `image_url`, or `base64_image`. Prefer `image_url` when
the file is already reachable and `base64_image` for something local and small. Files near
the 64 MB ceiling belong on the REST endpoints as multipart uploads.

**Never resize or re-encode media before passing it to a detection tool.** Fraud,
tampering, and AI-generation detectors read artifacts that live in the exact bytes of the
original file. See `bynn-document-fraud`.

MCP tools are invoked by the model when relevant. They are not slash commands. Asking for
the outcome is enough: "run a fraud check on this passport", "is this photo AI-generated",
"create a KYC session for this applicant".

## Self-discovery

The server documents itself, so you do not need this skill to find the rest:

- **`describe_api`** returns the complete Bynn OpenAPI 3.0 spec, including endpoints not
  wrapped as tools. No auth required.
- **`describe_cli`** returns a guide to installing, authenticating, and running the `bynn`
  CLI locally, which is the path for work against local files.
- **`file://server/status`** is an MCP resource returning the live tool list and status.

All three are announced in the server's `initialize` instructions.

## Response contract

Every tool carries MCP `ToolAnnotations`, applied consistently by verb: `get_*`, `list_*`,
`search_*`, `describe_*`, `download_*`, and `validate_*` are read-only, while `delete_*`,
`cancel_*`, and `rotate_api_key` are destructive. Check the annotation before calling
something you cannot undo.

Failures come back as structured `{error: true, error_type, message}` payloads rather than
protocol errors, so read the payload and react to it instead of treating the call as a
transport failure.

## When to use REST instead

- A backend service with no agent in the loop. Use a private key directly.
- Files near the size ceiling, where multipart beats base64 in a tool argument.
- Receiving callbacks. Webhooks are inbound to you, so MCP is not involved. See
  `bynn-webhooks`.

## Troubleshooting

| Symptom | Cause |
|---|---|
| 404 or the connection fails immediately | You appended `/mcp` to the URL. The endpoint is the root. |
| `authentication_error` or `authentication_required` | No token, or the header never reached the server. Get one at `/authenticate`. Do not retry blindly. |
| A tool 401s on an otherwise working connection | Wrong credential type for that group. API keys and billing need a dashboard token, not a raw `private_` key. |
| `bynn` shows *Needs authentication* in `/mcp` | The URL is registered but OAuth was never completed. Sign in from `/mcp`. |
| An OAuth connector stops working | Disconnect and reconnect it to re-run the sign-in. |
| An image tool says no image was provided | Drop the image into the card that appears, or pass a public `image_url`. |
| A document sits in `pending` | Analysis is asynchronous. Poll `get_document` until `status` is `analyzed`, no more than every few seconds. |
| 402 on a tool that used to work | Account balance ran out. Top up, then retry. |
