---
name: mcp-server-authoring
description: "Author, debug, and deploy custom MCP servers for Hermes Agent. [DISABLED]"
version: 0.1.0
author: User (Hermes Agent)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mcp, server, authoring, debugging, typescript, python, stdio, sse]
    related_skills: [configure-mcp-servers, hermes-agent, configure-messaging-gateway]
---

# MCP Server Authoring

Build custom Model Context Protocol (MCP) servers from scratch for Hermes Agent. Covers both stdio (local) and SSE/HTTP (remote) transports, TypeScript and Python implementations, debugging workflows, and deployment patterns.

## When to Use

- Need a custom MCP server wrapping an API, SDK, or data source (e.g., Albion Online market data, game APIs)
- Existing MCP servers don't cover your use case
- Want to expose local tools/scripts as MCP resources/tools/prompts
- Debugging MCP connection issues (401, transport failures, capability negotiation)

Don't use for:
- Configuring existing MCP servers (use `configure-mcp-servers`)
- Simple function calling without MCP protocol needs

## Prerequisites

- Node.js 18+ (for TypeScript servers) or Python 3.10+ (for Python servers)
- `mcp` package: `npm i @modelcontextprotocol/sdk` or `pip install mcp`
- Hermes Agent with MCP client support (built-in)
- For SSE/HTTP: public URL or ngrok/cloudflare tunnel for remote access

## How to Run

```bash
# TypeScript server (recommended for Hermes integration)
mkdir my-mcp-server && cd my-mcp-server
npm init -y
npm i @modelcontextprotocol/sdk zod
npm i -D typescript @types/node tsx
# Write src/index.ts → see Procedure
npx tsx src/index.ts  # stdio test

# Python server
mkdir my-mcp-py && cd my-mcp-py
pip install mcp pydantic
# Write server.py → see Procedure
python server.py  # stdio test

# Register with Hermes (in config.yaml or via CLI)
hermes mcp add my-server --command "npx tsx /path/to/src/index.ts"
# or for Python
hermes mcp add my-server --command "python /path/to/server.py"
```

## Quick Reference

| Task | Command |
|------|---------|
| Init TypeScript MCP | `npm init -y && npm i @modelcontextprotocol/sdk zod && npm i -D typescript @types/node tsx` |
| Init Python MCP | `pip install mcp pydantic` |
| Test stdio locally | `npx tsx src/index.ts` / `python server.py` |
| Add to Hermes | `hermes mcp add <name> --command "<cmd>"` |
| List registered | `hermes mcp list` |
| Test via Hermes | `hermes chat -q "Use my-server tool X"` |
| Debug transport | `HERMES_LOG=debug hermes mcp test <name>` |

## Procedure

### 1. Choose Transport & Language

**Completion criterion**: Decision documented with rationale.

| Transport | Use Case | Complexity |
|-----------|----------|------------|
| stdio | Local tools, Hermes-internal, no network | Low |
| SSE | Remote access, multiple clients, web deployment | Medium |
| Streamable HTTP | Modern replacement for SSE, better proxy support | Medium |

**Language choice**: TypeScript (first-class SDK, Hermes uses Node for some MCP) or Python (if wrapping Python SDKs like `albion-online-sdk`).

### 2. Scaffold Server Structure

**Completion criterion**: Minimal server runs and responds to `initialize`.

**TypeScript (stdio):**
```typescript
// src/index.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { ListToolsRequestSchema, CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  { name: "my-mcp", version: "0.1.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{ name: "my_tool", description: "Does something", inputSchema: { type: "object", properties: {} } }]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "my_tool") {
    return { content: [{ type: "text", text: "Tool result" }] };
  }
  throw new Error(`Unknown tool: ${request.params.name}`);
});

const transport = new StdioServerTransport();
await server.connect(transport);
console.error("MCP server running on stdio");
```

**Python (stdio):**
```python
# server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("my-mcp")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(name="my_tool", description="Does something", inputSchema={"type": "object", "properties": {}})]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "my_tool":
        return [TextContent(type="text", text="Tool result")]
    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### 3. Implement Domain Tools/Resources

**Completion criterion**: Each tool/resource tested independently with sample inputs.

**Pattern for wrapping external APIs (e.g., Albion AODP/AFM):**
```typescript
// src/services/albion.ts
export async function fetchMarketPrices(itemIds: string[]) {
  const res = await fetch(`https://api.albionfreemarket.com/v1/prices?items=${itemIds.join(",")}`);
  return res.json();
}

// In tool handler:
server.setRequestHandler(CallToolRequestSchema, async (req) => {
  if (req.params.name === "get_market_prices") {
    const { items } = req.params.arguments as { items: string[] };
    const data = await fetchMarketPrices(items);
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
});
```

**Key patterns:**
- Separate API clients into `src/services/` or `services/`
- Use Zod (TS) or Pydantic (Py) for input validation
- Return structured JSON via `TextContent` for complex data
- Handle rate limits, auth, retries in service layer

### 4. Test Stdio Transport Locally

**Completion criterion**: `initialize` → `tools/list` → `tools/call` round-trip works.

```bash
# TypeScript
npx tsx src/index.ts
# In another terminal, send JSON-RPC:
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}' | npx tsx src/index.ts
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | npx tsx src/index.ts
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"my_tool","arguments":{}}}' | npx tsx src/index.ts
```

### 5. Register with Hermes

**Completion criterion**: `hermes mcp list` shows server, tools visible in chat.

```yaml
# In ~/.hermes/config.yaml (or via CLI)
mcp_servers:
  my-mcp:
    command: "npx"
    args: ["tsx", "/home/user01/.hermes/python/my-mcp-server/src/index.ts"]
    enabled: true
    env:
      ALBION_API_KEY: "${ALBION_API_KEY}"  # From .env
```

Or via CLI:
```bash
hermes mcp add my-mcp --command "npx" --args "tsx" --args "/home/user01/.hermes/python/my-mcp-server/src/index.ts"
```

### 6. Debug Common Issues

**Completion criterion**: Issue identified, fix applied, re-verified.

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `401 Unauthorized` | Missing/invalid API key in env | Check `.env`, restart gateway, verify `env` in config |
| `tools/list` empty | Capability not declared | Ensure `capabilities: { tools: {} }` in Server init |
| `Connection refused` | Stdio transport not connected | Verify command/path, check Hermes logs |
| `MCPError: Server returned error` | Tool threw unhandled error | Wrap handlers in try/catch, return error content |
| `keepalive failed` (SSE) | Server timeout / no heartbeat | Implement ping/pong, increase timeout |
| `session termination failed: 401` | Auth header not forwarded | Check proxy/gateway auth passthrough |

### 7. Deploy for Production (SSE/HTTP)

**Completion criterion**: Remote clients can connect and call tools.

```typescript
// SSE transport (for remote access)
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import express from "express";

const app = express();
const transport = new SSEServerTransport("/mcp", app);
await server.connect(transport);

app.listen(3000, () => console.error("MCP SSE on :3000/mcp"));
```

Register with Hermes:
```yaml
mcp_servers:
  my-mcp-remote:
    url: "https://mcp.example.com/mcp"  # or http://localhost:3000/mcp
    enabled: true
    headers:
      Authorization: "Bearer ${MCP_API_TOKEN}"
```

## Pitfalls

| Issue | Solution |
|-------|----------|
| **Stdio vs SSE confusion** | Stdio = local subprocess (Hermes spawns). SSE/HTTP = remote (Hermes connects). Don't mix. |
| **Env vars not reaching server** | For stdio: define `env:` in mcp_servers config. For SSE: server reads its own env. |
| **TypeScript `import` errors** | Use `.js` extension in imports: `import x from "./services/albion.js"` |
| **Zod schema not matching MCP types** | MCP uses JSON Schema; convert with `z.toJSONSchema()` or write JSON Schema directly. |
| **Hermes caches MCP server** | Restart gateway after config change: `systemctl --user restart hermes-gateway` |
| **Multiple servers same stdio** | Each stdio server needs separate process; can't share one stdio connection. |
| **Large responses truncated** | MCP has no hard limit but Hermes may truncate; paginate or summarize in tool. |
| **Windows path in args** | Use WSL paths in config (`/home/user/...`) even on Windows; Hermes runs in WSL. |

## Verification

```bash
# 1. Server runs standalone
npx tsx src/index.ts &
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}' | npx tsx src/index.ts
# → Should return server info + capabilities

# 2. Registered in Hermes
hermes mcp list | grep my-mcp
# → my-mcp: enabled

# 3. Tools visible in chat
hermes chat -q "List tools from my-mcp"
# → Should show your tool names

# 4. Tool executes
hermes chat -q "Call my-mcp my_tool with args {}"
# → Should return tool result

# 5. End-to-end with real API
hermes chat -q "Use my-mcp to fetch Albion T7_LEATHER prices"
# → Should return market data
```

## Pattern Source

Distilled from 3+ sessions (Sep 2026):
- **20260925_030355_db2731eb** (762 msgs): Full Albion MCP server wrapping AODP/AFM + albion-online-sdk (TypeScript, stdio)
- **20260925/26/30 cron runs**: poe2-mcp (Python, stdio) and poe2-sergeyklay (Node, HTTP) registered in config.yaml
- **Recurring**: MCP 401 errors (ModelScope token expiry), stdio vs SSE transport confusion, env var passthrough

Key learnings:
- TypeScript SDK is more mature for Hermes integration
- stdio transport simplest for local-only tools
- Always validate input with Zod/Pydantic before calling external APIs
- Keep service layer separate from MCP protocol handlers
- Test stdio round-trip before registering with Hermes

---

*Distilled from session 20260925_030355_db2731eb (762 messages: Albion MCP authoring), plus recurring MCP server management patterns across cron sessions (poe2-mcp, poe2-sergeyklay, bing-cn). Pattern: scaffold → implement services → test stdio → register → debug transport/auth.*