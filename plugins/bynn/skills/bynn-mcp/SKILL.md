---
name: bynn-mcp
description: >-
  Connect an agent to the Bynn MCP server at https://mcp.bynn.com/ and drive Bynn
  through tools instead of hand-written HTTP. Covers getting a token, client config
  for Claude Code and other MCP clients, how one token resolves to the right API key
  per tool, the tool map, and when to drop to REST instead. Use when setting up the
  connection, when a tool returns an authentication error, or when choosing between
  MCP and REST.
metadata:
  author: bynn
  version: "0.1.0"
license: MIT
---

# Bynn over MCP

The MCP server exposes the Bynn platform as tools. Prefer it over hand-written HTTP for
anything interactive: it removes key handling, and `describe_api` gives you the full
OpenAPI spec on demand.

## Get a token

1. Log in to `https://dashboard.bynn.com`.
2. Open `/authenticate`.
3. Generate an access token and copy it.

The token acts with your own account's permissions and is long lived. Store it in an
environment variable, never in a committed file.

```bash
export BYNN_API_TOKEN="<your token>"
```

## Connect

Streamable HTTP, one header:

```json
{
  "mcpServers": {
    "bynn": {
      "type": "http",
      "url": "https://mcp.bynn.com/",
      "headers": { "Authorization": "Bearer ${BYNN_API_TOKEN}" }
    }
  }
}
```

In Claude Code this ships with the plugin, so exporting `BYNN_API_TOKEN` before starting
the session is the whole setup. For a client that does not expand environment variables
in its config, paste the token literally and keep the file out of version control.

Verify the connection by calling `describe_api`. If it returns the spec, you are done.

## One token, every capability

You never pick an API key. The server resolves the right credential per tool:

| Tool group | Resolved credential |
|---|---|
| billing, users, websites, reasoning, autodoc, moderation, face | your dashboard token |
| documents, age verification | your organization's private key |
| creating verification sessions | your organization's public key |

This is why the MCP path is safe for an agent and why a raw REST integration has to be
deliberate about which key it holds. See the `bynn` skill for the key families.

## Tool map

Start with `describe_api`. It returns the full OpenAPI 3.0 spec, which is authoritative
and always current. The tools you will reach for most:

| Goal | Tools |
|---|---|
| Document fraud analysis | `submit_document`, then poll `get_document` |
| Is this image AI-generated | `detect_ai_generated_image` |
| Age or minor detection | `check_age`, `verify_age_from_selfie` |
| Hosted identity verification | `create_session`, `get_session`, `get_session_preflight` |
| Any moderation or detection model | `list_all_moderation_models`, `create_moderation_inference` |
| Face gallery | `create_face_collection`, `enroll_face`, `search_faces` |
| Document requests over email or SMS | `create_invitation`, `get_invitation` |

Image inputs accept `file_path`, `image_url`, or `base64_image`. Prefer `image_url` when
the file is already reachable, and `base64_image` for anything local and small. Very large
files belong on the REST endpoints as multipart uploads.

MCP tools are invoked by the model when they are relevant. They are not slash commands.
Asking for the outcome is enough: "run a fraud check on this passport", "is this photo
AI-generated", "create a KYC session for this applicant".

## When to use REST instead

- A backend service with no agent in the loop. Use a private key directly.
- Files near the 64 MB ceiling, where multipart beats base64 in a tool argument.
- Receiving callbacks. Webhooks are inbound to you, so MCP is not involved. See
  `bynn-webhooks`.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `authentication_error` or `authentication_required` on every tool | No token, or the header never reached the server. Re-read the token from `/authenticate` and check the config, do not retry blindly. |
| One tool 403s while others work | Your account role or plan lacks that capability. |
| 402 on a tool that used to work | Account balance ran out. Top up, then retry. |
| Tool list is empty | The client connected but did not complete the MCP handshake. Restart the client. |
