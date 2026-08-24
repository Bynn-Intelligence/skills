# Connecting the Bynn MCP server

```
https://mcp.bynn.com
```

Transport: **Streamable HTTP**. The endpoint is the **root path**. Appending `/mcp` gives a
404 that looks like an outage. The only other route is `GET /health`.

## Per-client configuration

### Claude Code

```bash
# OAuth
claude mcp add --transport http bynn https://mcp.bynn.com

# Bearer token
claude mcp add --transport http bynn https://mcp.bynn.com \
  --header "Authorization: Bearer $BYNN_API_TOKEN"
```

`-s user` makes it available in every project; `-s project` writes it to the repo's
`.mcp.json`. Commit only the OAuth form or an environment-variable placeholder.

After adding, run `/mcp`. It must read **Connected**. *Needs authentication* means the URL
is registered but sign-in has not happened.

### Claude Desktop and claude.ai

Settings, Connectors, **Add custom connector**, URL `https://mcp.bynn.com`. OAuth sign-in
starts automatically on first use.

### ChatGPT

Settings, Apps & Connectors, enable developer mode, **Create**, MCP server URL
`https://mcp.bynn.com`. Bynn is built as a ChatGPT app: fraud reports and AI-image checks
render as interactive cards, and attached images are forwarded to the tools natively.

### Cursor

`~/.cursor/mcp.json`, or `.cursor/mcp.json` per project:

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

`.vscode/mcp.json`:

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

### Windsurf and Zed

Both bridge through `mcp-remote`.

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

Zed uses `context_servers` with a `command` object:

```json
{
  "context_servers": {
    "bynn": {
      "command": {
        "path": "npx",
        "args": ["-y", "mcp-remote", "https://mcp.bynn.com"]
      }
    }
  }
}
```

### Generic client with a token

```json
{
  "mcpServers": {
    "bynn": {
      "url": "https://mcp.bynn.com",
      "headers": { "Authorization": "Bearer ${BYNN_API_TOKEN}" }
    }
  }
}
```

Remove `headers` entirely to use OAuth. An empty variable produces the header `Bearer `
with nothing after it, which the server reads as an **invalid** token rather than an absent
one, so it returns 401 instead of starting the OAuth flow. Either set the variable or
delete the block.

## Authentication

### OAuth 2.1

Hosted connectors authenticate with OAuth 2.1 and PKCE. The authorization server is
`dashboard.bynn.com`, and the server publishes protected-resource metadata at
`https://mcp.bynn.com/.well-known/oauth-protected-resource`:

```json
{
  "resource": "https://mcp.bynn.com/",
  "authorization_servers": ["https://dashboard.bynn.com/"],
  "bearer_methods_supported": ["header"],
  "resource_name": "Bynn MCP Server"
}
```

Clients supporting Dynamic Client Registration, including Claude and Cursor, register
themselves. If a client reports an invalid or expired token, clear its stored
authentication and reconnect rather than editing config by hand.

### Bearer tokens

Get one at `https://dashboard.bynn.com/authenticate` while logged in. Three types work,
with different reach:

| Token | Prefix | Reach |
|---|---|---|
| Dashboard token (JWT) | none | Everything. The server exchanges it for your organization's API keys as each tool needs them. |
| Private API key | `private_...` | Documents, moderation, age results. Not dashboard tools like API keys or billing. |
| Public API key | `public_...` | Client-safe session creation only. |

Prefer the dashboard token. It is the only one covering every tool group, and it is what
makes the MCP path free of manual key handling.

## Verify

Call `describe_api`. It returns the full OpenAPI 3.0 spec. Anything else means the
connection is not usable yet.

From a shell, with a bearer token:

```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"0"}}}' \
| curl -s -X POST https://mcp.bynn.com \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -H "Authorization: Bearer $BYNN_API_TOKEN" -d @-
```

Without a valid credential the server answers `401` with a `WWW-Authenticate: Bearer`
header pointing at its resource metadata. That response is the server working correctly,
not an outage.

Liveness only, no auth needed:

```bash
curl -s https://mcp.bynn.com/health
```

## Self-hosting

The server ships as a Docker image serving MCP at `/` with `GET /health` for liveness.
Stateless HTTP is enabled, so replicas behind a load balancer work without session
affinity. `BYNN_API_BASE_URL` selects the backend, defaulting to `https://api.bynn.com`.
