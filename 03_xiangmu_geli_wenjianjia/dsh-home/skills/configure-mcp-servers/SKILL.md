---
name: configure-mcp-servers
description: Add and verify MCP servers in Hermes Agent via CLI.
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mcp, model-context-protocol, server, tool, verification]
    related_skills: [configure-modelscope-vision, verify-hermes-setup]
---

# configure-mcp-servers Skill

Add MCP (Model Context Protocol) servers to Hermes Agent using the `hermes mcp` CLI, enabling standardised tool access (Tools/Resources/Prompts) from any compliant server.

## When to Use

- Need to connect Hermes to an MCP server (filesystem, github, postgres, custom, etc.)
- Want to expose external tools to the agent without custom adapters
- Using ModelScope or other providers hosting MCP endpoints
- Need to verify server connectivity and tool discovery

## Prerequisites

- Hermes Agent with `mcp` package >= 1.0 (for stdio/SSE) or >= 2.1 (for streamable_http)
- Server URL and optional auth (API key / Bearer token)
- Network access to the MCP endpoint

## How to Run

```bash
# 1. Ensure mcp package supports your transport
# stdio/SSE: mcp >= 1.0 (built-in)
# streamable_http: mcp >= 2.1 (pip install --upgrade mcp)

# 2. Add server (interactive prompts for auth if needed)
hermes mcp add <name> --url <url> [--transport <stdio|sse|streamable_http>]

# 3. List configured servers
hermes mcp list

# 4. Test connectivity
hermes mcp test <name>

# 5. Use in chat (auto-discovered tools prefixed with mcp__<server>__)
hermes chat -q "用 mcp__bing__bing_search 搜索 'MCP 协议'"
```

## Quick Reference

| Action | Command |
|--------|---------|
| Add stdio server | `hermes mcp add myserver --command "python server.py"` |
| Add SSE server | `hermes mcp add myserver --url http://localhost:8080/sse --transport sse` |
| Add HTTP server | `hermes mcp add myserver --url https://example.com/mcp --transport streamable_http` |
| List all | `hermes mcp list` |
| Test one | `hermes mcp test <name>` |
| Remove | `hermes mcp remove <name>` |
| View config | `grep -A 10 "mcp_servers:" ~/.hermes/config.yaml` |

## Procedure

1. **Check mcp package version** — `pip show mcp` or `python -c "import mcp; print(mcp.__version__)"`. For `streamable_http`, need >= 2.1.
2. **Add server** — Run `hermes mcp add <name> --url <url>`. Answer prompts:
   - "Does this server require authentication?" → `n` (no auth) or `y` + enter token
   - "Enable all N tools?" → `y` (enable all) or `select` (pick specific)
3. **Verify** — `hermes mcp list` shows server with tools; `hermes mcp test <name>` returns `Connected` + tool list.
4. **Use** — Tools auto-available as `mcp__<server>__<tool>` in chat.

## Pitfalls

- **streamable_http needs mcp >= 2.1** — older versions only support stdio/SSE. Upgrade: `pip install --upgrade mcp`.
- **Auth token not persisted in config.yaml** — stored in keyring/credential store; re-add server if keyring unavailable.
- **Server requires auth** — answer `y` to auth prompt, paste token. Some servers use header `Authorization: Bearer <token>`.
- **Tools not showing in chat** — ensure gateway is running (`systemctl --user status hermes-gateway`); MCP tools load on gateway startup.
- **Firewall/proxy** — MCP over HTTP/SSE needs outbound access to server URL.

## Verification

```bash
# Config check
grep -A 5 "mcp_servers:" ~/.hermes/config.yaml
# Should show your server with url, enabled: true

# Live test
hermes mcp test <name>
# Expected: "Connected (XXXms)" + tool list

# In-chat test
hermes chat -q "列出可用的 MCP 工具"
# Should mention mcp__<server>__<tool> tools
```

Success = server listed, test passes, tools callable in chat.

## References

- `references/session-2026-08-25-setup.md` — ModelScope bing-cn server setup transcript
- MCP Spec: https://modelcontextprotocol.io/specification/
- Official servers: https://github.com/modelcontextprotocol/servers