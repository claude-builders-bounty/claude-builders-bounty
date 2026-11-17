---
name: master-money-maker
description: "Run master money maker orchestration across 7 platforms. [DISABLED]"
version: 1.0.0
author: User (Hermes Agent)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - autonomous
    - money-making
    - orchestration
    - dealwork
    - hyrve
    - clawmart
    - botstreet
    - uumit
    - agenthansa
    - minia2a
    related_skills:
    - autonomous-money-making-workflow
    - agent-marketplace-integration
    - uumit-market-autobid-deployment
    - configure-messaging-gateway
---

# Master Money Maker Orchestration

Run the master money-making orchestration loop (`master_money_maker.py`) across 7 platforms with 3-layer self-check, unified config, and Feishu notifications. Continuous autonomous earning loop.

## When to Use

- Start the main autonomous earning loop (5-min polling cycle)
- Debug why bids/contracts not progressing on any platform
- Verify all 7 platform handlers are functional
- Check unified config (`money_maker.yaml`, `payment_gateway.yaml`, `guard-policy.yaml`)

**Don't use for:**
- Single-platform debugging (use platform-specific skills)
- Initial platform setup (use `agent-marketplace-integration`)

## Prerequisites

- `~/.hermes/scripts/master_money_maker.py` (main orchestrator)
- `~/.hermes/scripts/bid_status_monitor.py` (5-min bid monitoring)
- `~/.hermes/scripts/cred_self_check.py` (10-min credential self-check)
- `~/.hermes/scripts/full_platform_self_check.py` (2-hr full platform check)
- `~/.hermes/money_maker.yaml` (platform credentials + runtime config)
- `~/.hermes/payment_gateway.yaml` (Stripe/USDC gateway config)
- `~/.hermes/guard-policy.yaml` (CashClaw Guard policy)
- `~/.hermes/money_maker/orchestrator.db` (SQLite state DB)
- Feishu gateway running (`hermes-gateway` systemd service)
- All 7 platform API keys/credentials configured

## How to Run

```bash
# 1. Fill in real credentials (one-time)
vim ~/.hermes/money_maker.yaml       # Platform API keys
vim ~/.hermes/payment_gateway.yaml   # Stripe/USDC keys

# 2. Start master loop (foreground for testing)
cd ~/.hermes/scripts
python3 master_money_maker.py

# 3. Or run as systemd service (production)
# See Procedure step 5 for systemd setup
```

## Quick Reference

| Task | Command |
|------|---------|
| Start master loop | `cd ~/.hermes/scripts && python3 master_money_maker.py` |
| Check bid status | `python3 bid_status_monitor.py` |
| Credential self-check | `python3 cred_self_check.py` |
| Full platform check | `python3 full_platform_self_check.py` |
| View earnings DB | `sqlite3 ~/.hermes/money_maker/orchestrator.db "SELECT date(received_at) as day, COUNT(*) as missions, SUM(amount) as revenue FROM earnings GROUP BY day ORDER BY day DESC LIMIT 7;"` |
| View contracts | `sqlite3 ~/.hermes/money_maker/orchestrator.db "SELECT * FROM contracts ORDER BY created_at DESC LIMIT 10;"` |

## Procedure

### 1. Configure Unified Credentials

**Completion criterion**: All 7 platforms have valid API keys in `money_maker.yaml`.

```yaml
# ~/.hermes/money_maker.yaml (edit with real values)
platforms:
  dealwork:
    api_key: "dw_..."           # From dealwork.ai dashboard
    base_url: "https://dealwork.ai"
    enabled: true
    bid_strategy: "normal"      # 75-80% budget
  hyrve:
    api_key: "hyrve_..."
    webhook_secret: "..."
    enabled: true
  agenthansa:
    api_key: "ah_..."
    wallet: "0x2e13ADd5A2b92B2650CB3D40d13eD9D83305ED76"
    enabled: true
  clawmart:
    api_key: "cm_..."
    enabled: true
  botstreet:
    api_key: "bs_..."
    enabled: true
  uumit:
    username: "xxx"
    password: "xxx"
    enabled: true
  minia2a:
    api_key: "ma_..."
    wallet: "0x2e13ADd5A2b92B2650CB3D40d13eD9D83305ED76"
    enabled: true

payment_gateway:
  stripe_secret_key: "sk_..."
  usdc_wallet: "0x2e13ADd5A2b92B2650CB3D40d13eD9D83305ED76"
  usdc_rpc: "https://mainnet.infura.io/v3/..."

guard:
  max_cost_usd_per_hour: 10.0
  max_recursion_depth: 3
  tool_firewall: ["terminal", "web_search", "browser_exec", "delegate_task"]
```

### 2. Configure Payment Gateway

**Completion criterion**: `payment_gateway.yaml` has valid Stripe/USDC keys.

```yaml
# ~/.hermes/payment_gateway.yaml
stripe:
  secret_key: "sk_live_..."     # Or test key
  webhook_secret: "whsec_..."
usdc:
  wallet: "0x2e13ADd5A2b92B2650CB3D40d13eD9D83305ED76"
  private_key_path: "~/.hermes/wallet/wallet.json"
  p256_key_path: "~/.hermes/wallet/p256_key.json"
  rpc_url: "https://mainnet.infura.io/v3/..."
  chain_id: 1
```

### 3. Configure Guard Policy

**Completion criterion**: `guard-policy.yaml` matches CashClaw Guard defaults.

```yaml
# ~/.hermes/guard-policy.yaml
cost_cap_usd_per_hour: 10.0
recursion_kill_depth: 3
tool_firewall:
  allow: ["terminal", "web_search", "browser_exec", "delegate_task", "skill_view", "skill_manage"]
  deny: ["computer_use", "vision_analyze"]
```

### 4. Verify All Platform Handlers Import

**Completion criterion**: No import errors for any platform handler.

```bash
cd ~/.hermes/scripts
python3 -c "
import dealwork_handler, hyrve_handler, agenthansa_handler
import clawmart_handler, botstreet_handler, uumit_handler, minia2a_handler
print('✅ All 7 platform handlers import OK')
"
```

### 5. Run Master Loop (Test Foreground)

**Completion criterion**: Loop starts, shows "Cycle N" logs, polls all enabled platforms.

```bash
cd ~/.hermes/scripts
python3 master_money_maker.py
# Expected output:
# [Cycle 1] Polling 7 platforms...
# [dealwork] Polling tasks... 0 new
# [hyrve] Polling jobs... 0 new
# ...
# [Cycle 2] (5 min later)
# Press Ctrl+C to stop
```

### 6. Deploy as Systemd Service (Production)

**Completion criterion**: Service runs in background, survives logout, restarts on failure.

```bash
# Create service unit
cat > ~/.config/systemd/user/master-money-maker.service <<'EOF'
[Unit]
Description=Master Money Maker - Autonomous Earning Orchestrator
After=network.target hermes-gateway.service
Requires=hermes-gateway.service

[Service]
Type=exec
ExecStart=/home/user01/.hermes/hermes-agent/venv/bin/python /home/user01/.hermes/scripts/master_money_maker.py
WorkingDirectory=/home/user01/.hermes/scripts
Restart=on-failure
RestartSec=30
Environment=PATH=/home/user01/.hermes/hermes-agent/venv/bin:/usr/local/bin:/usr/bin:/bin
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

# Enable and start
systemctl --user daemon-reload
systemctl --user enable --now master-money-maker

# Verify
systemctl --user status master-money-maker
journalctl --user -u master-money-maker -f
```

### 7. Monitor via Feishu & DB

**Completion criterion**: Feishu alerts on bid accepted/contract started/payment received; DB records earnings.

```bash
# Check recent earnings
sqlite3 ~/.hermes/money_maker/orchestrator.db "
SELECT date(received_at) as day, COUNT(*) as missions, SUM(amount) as revenue
FROM earnings GROUP BY day ORDER BY day DESC LIMIT 7;
"

# Check bid history
sqlite3 ~/.hermes/money_maker/orchestrator.db "
SELECT platform, job_title, proposed_amount, status, created_at
FROM bid_history ORDER BY created_at DESC LIMIT 20;
"

# Check contracts
sqlite3 ~/.hermes/money_maker/orchestrator.db "
SELECT platform, job_id, state, amount, started_at, completed_at
FROM contracts ORDER BY created_at DESC LIMIT 10;
"
```

## Pitfalls

| Issue | Solution |
|-------|----------|
| **dealwork 投标全被拒** | 检查 `bid_strategy: normal` (75-80% budget)；单价太高/太低；信誉分不够 |
| **HYRVE webhook 不通** | `ngrok` 隧道需稳定；`HyvreHandler.start_webhook_server()` 自检 ngrok URL |
| **AgentHansa 需加盟** | 先 `checkin` → 选加盟 → 再 `poll_quests`；加盟选项影响可接任务类型 |
| **ClawMart 任务全灰产** | Handler 内置 `gate_filtered` 拦截；只接白名单类型（代码/文档/数据） |
| **波街 服务帖审核慢** | 发帖后需人工审核；可发多帖覆盖不同技能标签 |
| **UUMit timer 后台跑** | `uumit-market-autobid-deployment` skill 管理 4 个 systemd timer |
| **minia2a 需上架技能** | 先在 minia2a.uk 注册服务 → 配置 x402 定价 → 再轮询 |
| **DB 锁死** | SQLite 并发写入；`cred_self_check` 和主循环错峰，或用 WAL 模式 |

## Verification

```bash
# 1. Master loop starts without import errors
cd ~/.hermes/scripts && timeout 10 python3 master_money_maker.py 2>&1 | grep -q "Cycle 1" && echo "✅ Master loop starts"

# 2. Bid monitor works
python3 bid_status_monitor.py 2>&1 | grep -q "dealwork\|hyrve" && echo "✅ Bid monitor runs"

# 3. Credential check passes
python3 cred_self_check.py 2>&1 | grep -q "OK\|healthy" && echo "✅ Credentials healthy"

# 4. Full platform check runs
timeout 30 python3 full_platform_self_check.py 2>&1 | grep -q "dealwork\|hyrve" && echo "✅ Full check runs"

# 5. Systemd service active (if deployed)
systemctl --user is-active master-money-maker | grep -q active && echo "✅ Service running"

# 6. Earnings DB accessible
sqlite3 ~/.hermes/money_maker/orchestrator.db ".tables" | grep -q earnings && echo "✅ DB schema OK"
```

---

*Distilled from session 20261004_100635_3c5af9a0 (Oct 4, 2026) — Master money maker orchestration with 7 platforms (dealwork/HYRVE/AgentHansa/ClawMart/Botstreet/UUMit/minia2a), 3-layer self-check (5min/10min/2hr), unified YAML config, SQLite state DB, Feishu notifications. CashClaw Guard integrated. Core earning loop pattern occurs continuously.*