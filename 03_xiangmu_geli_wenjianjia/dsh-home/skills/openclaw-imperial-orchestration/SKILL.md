---
name: openclaw-imperial-orchestration
description: "Deploy OpenClaw with Edict (三省六部) agents, integrate with Hermes Empress, Feishu binding. [DISABLED]"
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, windows]
metadata:
  hermes:
    tags: [openclaw, edict, multi-agent, orchestration, imperial, feishu]
    related_skills: [manage-systemd-services-wsl, configure-feishu-gateway, verify-hermes-setup, hermes-agent]
---

# OpenClaw Imperial Orchestration

Deploy OpenClaw gateway with Edict (三省六部制) 12-agent orchestration system, integrate with Hermes Empress for `下旨:` routing, and configure Feishu binding for chat-driven task dispatch.

## When to Use

- Need multi-agent orchestration with structured hierarchy (Empress → 三省六部)
- Want Feishu-driven task dispatch via `下旨:` prefix
- Require 12 specialized agents: 太子、中书省、门下省、尚书省、六部(礼/户/兵/刑/工/吏)、早朝、皇城司
- Need dashboard at `http://127.0.0.1:18789/` for monitoring
- Hermes Empress routes `下旨:` commands to OpenClaw三省六部 chain

## Prerequisites

- WSL2 with `systemd=true` in `/etc/wsl.conf` + `wsl --shutdown` restart
- `loginctl enable-linger $USER` for user service persistence
- Node.js 18+ (install via nvm for stable path: `nvm install 20.18.0`)
- Hermes Agent with Feishu gateway configured (`configure-feishu-gateway`)
- Feishu App ID/Secret with Bot capability + WebSocket mode
- OpenClaw npm package: `npm i -g openclaw@latest`

## How to Run

```bash
# 1. Install OpenClaw globally
npm i -g openclaw@latest

# 2. Verify WSL systemd is running
systemctl --user status
# Should show "State: running"

# 3. Enable and start OpenClaw gateway
systemctl --user daemon-reload
systemctl --user enable --now openclaw-gateway

# 4. Verify gateway running
openclaw gateway status
# Should show: Runtime: running, Connectivity probe: ok, Listening: 127.0.0.1:18789

# 5. Interactive onboarding (configures model provider, Feishu, skills)
openclaw onboard

# 6. Verify Edict agents loaded (12 agents)
openclaw agent list
# Should show: taizi, zhongshu, menxia, shangshu, libu, hubu, bingbu, xingbu, gongbu, libu_hr, zaochao, huangchengsi

# 7. Test dashboard
# Open http://127.0.0.1:18789/ in browser
```

## Quick Reference

| Task | Command |
|------|---------|
| Install OpenClaw | `npm i -g openclaw@latest` |
| Check systemd | `systemctl --user status` |
| Enable OpenClaw service | `systemctl --user enable --now openclaw-gateway` |
| Gateway status | `openclaw gateway status` |
| Interactive config | `openclaw onboard` |
| List agents | `openclaw agent list` |
| Dashboard | `http://127.0.0.1:18789/` |
| View logs | `journalctl --user -u openclaw-gateway -f` |

## Procedure

### 1. Prepare WSL Environment

```bash
# Ensure systemd is enabled in WSL
# /etc/wsl.conf must contain:
# [boot]
# systemd=true
# [user]
# default = user01

# Then in Windows PowerShell (Admin):
wsl --shutdown
# Reopen WSL terminal

# Verify
systemctl --user status
# State: running
```

### 2. Install OpenClaw and Node.js

```bash
# Install Node.js via nvm (persistent path)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install 20.18.0
nvm alias default 20.18.0

# Install OpenClaw
npm i -g openclaw@latest

# Verify
openclaw --version
# Should show version like 2026.8.1
```

### 3. Create OpenClaw Gateway systemd Service

```bash
# Create service unit
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/openclaw-gateway.service << 'EOF'
[Unit]
Description=OpenClaw Gateway
After=network.target

[Service]
Type=exec
ExecStart=/home/user01/.nvm/versions/node/v20.18.0/bin/node --max-old-space-size=8192 /home/user01/.nvm/versions/node/v20.18.0/lib/node_modules/openclaw/dist/index.js gateway --port 18789
WorkingDirectory=/home/user01
Restart=on-failure
RestartSec=5
Environment=PATH=/home/user01/.nvm/versions/node/v20.18.0/bin:/usr/local/bin:/usr/bin:/bin
Environment=OPENCLAW_GATEWAY_PORT=18789

[Install]
WantedBy=default.target
EOF

# Enable linger for persistence
loginctl enable-linger $USER

# Reload and start
systemctl --user daemon-reload
systemctl --user enable --now openclaw-gateway
```

### 4. Verify Gateway and Configure via Onboarding

```bash
# Check status
openclaw gateway status
# Runtime: running, Connectivity probe: ok, Listening: 127.0.0.1:18789

# Interactive configuration
openclaw onboard
# Prompts for:
# 1. Model provider (OpenAI / Anthropic / Ollama / etc.)
# 2. Default model
# 3. Messaging platforms (Feishu/Slack/Discord/Telegram)
# 4. Skills/plugins to enable
```

### 5. Verify Edict (三省六部) Agents Loaded

```bash
openclaw agent list
# Expected 12 agents:
# taizi          - 太子 (Message routing/sorting)
# zhongshu       - 中书省 (Planning/strategy)
# menxia         - 门下省 (Review/approval)
# shangshu       - 尚书省 (Dispatch/execution)
# libu           - 礼部 (Documentation/UI)
# hubu           - 户部 (Data/analytics)
# bingbu         - 兵部 (Code/engineering)
# xingbu         - 刑部 (Testing/compliance)
# gongbu         - 工部 (Infrastructure/DevOps)
# libu_hr        - 吏部 (HR/agent management)
# zaochao        - 早朝 (Intelligence/briefing)
# huangchengsi   - 皇城司 (Security audit/logging)
```

### 6. Integrate with Hermes Empress

Hermes Empress (profile `empress`) routes messages starting with `下旨:` to OpenClaw三省六部 chain:

```
User (Feishu) → "下旨: 帮我写个用户登录 API"
    ↓
Hermes Empress (Nemotron 3 Ultra) — detects "下旨:" prefix
    ↓
OpenClaw Gateway (port 18789) — receives via Feishu WebSocket
    ↓
太子 (taizi) — sorts, creates JJC task, forwards to 中书省
    ↓
中书省 (zhongshu) — plans, drafts execution plan
    ↓
门下省 (menxia) — reviews, 准奏/封驳 (approve/reject)
    ↓
尚书省 (shangshu) — dispatches to 六部 (parallel)
    ↓
六部执行 → 尚书省汇总 → 中书省回奏 → 太子回复用户
```

**Configuration in Hermes Empress profile:**
- Feishu gateway already configured (shared)
- Empress detects `下旨:` prefix in incoming messages
- Routes to OpenClaw via local WebSocket `ws://127.0.0.1:18789`

### 7. Feishu Binding for Empress

```bash
# Empress uses same Feishu App ID/Secret as Hermes gateway
# Ensure bot is added to group chat (required for 230002 error)
# In Feishu: Group settings → Add bot → Select your app

# Verify Empress receives messages
journalctl --user -u hermes-gateway -f
# Look for: [Feishu] Inbound dm message received
```

### 8. Dashboard and Monitoring

```bash
# Open dashboard
# http://127.0.0.1:18789/

# Dashboard shows:
# - 10 panel views (all/by status/by department/by priority)
# - Real-time activity stream (59+ events per task)
# - Agent online status + heartbeat
# - One-click stop/cancel/resume/advance
```

## Pitfalls

- **systemd not enabled** — WSL default has no systemd. Must edit `/etc/wsl.conf` + `wsl --shutdown` + restart WSL.
- **Node.js path in `/tmp/` not persistent** — Use nvm/apt stable path (`~/.nvm/versions/node/v20.18.0/bin/node`).
- **Feishu bot not in chat** — Error `[230002] Bot/User can NOT be out of the chat`. Fix: invite bot to group or send DM first.
- **Gateway restart from inside gateway blocked** — SIGTERM propagates. Use separate shell: `systemctl --user restart openclaw-gateway`.
- **OpenClaw gateway port conflict** — Default 18789. Check `ss -tlnp | grep 18789`.
- **Model provider auth** — `openclaw onboard` requires valid API keys. For Ollama: ensure `OLLAMA_HOST=0.0.0.0` and firewall allows WSL subnet.
- **12-agent limit** — Edict defines exactly 12 agents. Don't add more without architecture changes.
- **RPM limit** — OpenClaw enforces 40 RPM per agent. Batch heavy workloads.

## Verification

```bash
# 1. systemd running
systemctl --user is-active openclaw-gateway
# → active

# 2. Gateway healthy
openclaw gateway status | grep -E "Runtime: running|Connectivity probe: ok"
# → both present

# 3. All 12 agents loaded
openclaw agent list | wc -l
# → 12

# 4. Dashboard accessible
curl -s http://127.0.0.1:18789/ | grep -q "OpenClaw"
# → exit 0

# 5. Feishu WebSocket connected
journalctl --user -u hermes-gateway -n 20 | grep "Connected in websocket mode"
# → [Feishu] Connected in websocket mode (feishu)

# 6. Empress → OpenClaw routing test
# In Feishu: send "下旨: 测试任务"
# Should see task created in OpenClaw dashboard
```

---

*Skill distilled from 3 sessions (2026-08-31, 2026-08-30) analyzing OpenClaw + Edict deployment, systemd troubleshooting, and Hermes Empress integration pattern.*