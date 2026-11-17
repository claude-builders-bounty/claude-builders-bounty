---
name: refresh-modelscope-mcp-token
description: "Refresh ModelScope MCP token when bing-cn returns 401."
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [modelscope, mcp, bing-cn, token, 401, authentication]
    related_skills: [configure-mcp-servers, manage-systemd-services-wsl, configure-feishu-gateway]
---

# Refresh ModelScope MCP Token

Regenerate and update the ModelScope API token when `bing-cn` MCP server returns 401 errors (keepalive failed, session termination failed). The token expires periodically and must be refreshed at modelscope.cn.

## When to Use

- Gateway logs show: `MCP server 'bing-cn' keepalive failed, triggering reconnect (state: connected → degraded): MCPError: Server returned an error response`
- Followed by: `mcp.client.streamable_http: Session termination failed: 401`
- `hermes send --to feishu` works but web search via bing-cn fails
- Token in `HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY` is old/expired

**Don't use for:**
- Other MCP servers (poe2, poe2-sergeyklay use different auth)
- Initial ModelScope setup

## Prerequisites

- ModelScope account with API access
- `HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY` in `~/.hermes/.env` or systemd drop-in
- `hermes-gateway` systemd service running
- Browser access to modelscope.cn

## How to Run

```bash
# 1. Generate new token at ModelScope
# Open: https://modelscope.cn/my/myaccesstoken
# Click "生成新 Token" → copy the new token (starts with ms-)

# 2. Update .env
sed -i "s/^HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY=.*/HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY=ms-YOUR_NEW_TOKEN/" ~/.hermes/.env

# 3. Update systemd drop-in (used by gateway)
cat > ~/.config/systemd/user/hermes-gateway.service.d/modelscope-api.conf <<'EOF'
[Service]
Environment=HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY=ms-YOUR_NEW_TOKEN
EOF

# 4. Reload and restart gateway
systemctl --user daemon-reload
systemctl --user restart hermes-gateway

# 5. Verify bing-cn reconnects
sleep 10
journalctl --user -u hermes-gateway -n 30 --no-pager | grep -E 'bing-cn|keepalive|reconnect'
# Should show: keepalive OK or connected (not 401)
```

## Quick Reference

| Task | Command |
|------|---------|
| View current token | `grep HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY ~/.hermes/.env` |
| Generate new token | Browser: https://modelscope.cn/my/myaccesstoken |
| Update .env | `sed -i "s/^HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY=.*/HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY=ms-NEW/" ~/.hermes/.env` |
| Update systemd drop-in | See How to Run step 3 |
| Restart gateway | `systemctl --user daemon-reload && systemctl --user restart hermes-gateway` |
| Verify fix | `journalctl --user -u hermes-gateway -n 30 | grep -E 'bing-cn.*(OK|connected)'` |

## Procedure

### 1. Confirm 401 Error Pattern

**Completion criterion**: Logs show bing-cn 401 on keepalive/termination.

```bash
journalctl --user -u hermes-gateway -n 50 --no-pager | grep -E 'bing-cn.*401|keepalive failed'
# Expected pattern:
# MCP server 'bing-cn' keepalive failed, triggering reconnect... MCPError: Server returned an error response
# mcp.client.streamable_http: Session termination failed: 401
```

### 2. Generate New Token

**Completion criterion**: New `ms-...` token copied from ModelScope.

1. Open https://modelscope.cn/my/myaccesstoken in browser
2. Log in if needed
3. Click "生成新 Token" (Generate New Token)
4. Copy the new token (format: `ms-xxxxxxxxxxxxxxxx`)

### 3. Update Credentials in Both Places

**Completion criterion**: Both `.env` and systemd drop-in have new token.

```bash
NEW_TOKEN="ms-YOUR_NEW_TOKEN_HERE"

# Update .env (used by CLI, non-gateway contexts)
sed -i "s/^HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY=.*/HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY=${NEW_TOKEN}/" ~/.hermes/.env

# Update systemd drop-in (used by gateway service)
cat > ~/.config/systemd/user/hermes-gateway.service.d/modelscope-api.conf <<EOF
[Service]
Environment=HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY=${NEW_TOKEN}
EOF
```

### 4. Restart Gateway

**Completion criterion**: Gateway restarts cleanly, bing-cn reconnects without 401.

```bash
systemctl --user daemon-reload
systemctl --user restart hermes-gateway
sleep 10
systemctl --user is-active hermes-gateway
# Expected: active
```

### 5. Verify Bing-CN Reconnection

**Completion criterion**: No 401 errors in logs; keepalive succeeds.

```bash
journalctl --user -u hermes-gateway -n 50 --no-pager | grep -E 'bing-cn'
# Should show keepalive success or connected, NOT "401" or "keepalive failed"
```

## Pitfalls

| Issue | Solution |
|-------|----------|
| **Token format wrong** | Must start with `ms-` — copy exactly from ModelScope |
| **Only updated .env** | Gateway reads from systemd drop-in; update BOTH |
| **Gateway restart fails** | Check `systemctl --user status hermes-gateway` for errors |
| **Still 401 after update** | Token may have permissions issue; regenerate with full scopes |
| **Multiple gateways** | Update drop-in for each gateway service (default, empress) |
| **bing-cn URL changed** | Check MCP server config: `hermes config get mcp_servers.bing-cn.url` |

## Verification

```bash
# 1. Token updated in both places
grep HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY ~/.hermes/.env | grep -q "ms-" && echo "✅ .env updated"
grep HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY ~/.config/systemd/user/hermes-gateway.service.d/modelscope-api.conf | grep -q "ms-" && echo "✅ systemd drop-in updated"

# 2. Gateway healthy
systemctl --user is-active hermes-gateway | grep -q active && echo "✅ Gateway running"

# 3. No 401 in recent logs
journalctl --user -u hermes-gateway --since "2 minutes ago" --no-pager | grep -q "401" && echo "❌ Still 401" || echo "✅ No 401 errors"

# 4. Bing-cn keepalive OK
journalctl --user -u hermes-gateway --since "2 minutes ago" --no-pager | grep -E 'bing-cn.*(keepalive|connected|OK)' && echo "✅ Bing-cn healthy"
```

---

*Distilled from sessions: 20260926_020816_1453bcf8, 20260930_213444_3b609a, 20261001_022508_36d98b41 — bing-cn MCP server 401 errors recurring every few days (Sep 26, 30, Oct 1). Token expires and must be regenerated at modelscope.cn/my/myaccesstoken. Pattern occurs ≥3 times in last 7 days.*