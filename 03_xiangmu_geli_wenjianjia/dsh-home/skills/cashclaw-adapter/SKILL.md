---
name: cashclaw-adapter
description: Adapts CashClaw 13 skills + Guard + HYRVE Bridge to Hermes.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [cashclaw, adapter, guard, hyrve, seo, content, leads, invoicing, outreach, competitor, landing, scraper, reputation]
    related_skills: [seo-auditor, content-writer, lead-generator, payment-gateway, invoice-manager]
    requires_toolsets: [terminal, web, file, web_search, browser_exec]
---

# CashClaw Adapter — 核心适配层

## When to Use
- Need to map CashClaw (OpenClaw) skill pack capabilities to Hermes architecture
- Want to reuse Guard runtime protection, HYRVE Bridge 50+ endpoints, Mission audit patterns
- Integrating 13 CashClaw vertical skills into Hermes revenue skill ecosystem

**使命**：将 CashClaw (OpenClaw 技能包) 的核心能力 —— 13 个垂直技能、Guard 运行时防护、HYRVE Bridge 50+ API、Mission 审计追踪 —— 适配到 Hermes Agent 架构，零成本复用。

---

## 🎯 适配映射表

| CashClaw 组件 | Hermes 对应 | 状态 |
|--------------|-------------|------|
| **cashclaw-guard** (硬成本上限/递归/工具防火墙/YAML策略/多渠道告警) | `RuntimeGuard` (PlatformHandler 基类注入) | ✅ 已完成 |
| **HYRVE Bridge** (50+ 端点: Auth/Agents/Jobs/Orders/Messages/Wallet/Payments/Keys/Admin) | `HyvreHandler` (Webhook 实时 + 三层自检) | ✅ 已完成 |
| **cashclaw-core** (Mission 编排/生命周期/定价/自动接受) | `master_money_maker.py` 主循环 + 投标策略 | ✅ 已完成 |
| **cashclaw-invoicer** (Stripe/USDC 开票/催款/退款) | `PaymentGatewayManager` + `create_invoice_for_completion` | ✅ 已完成 |
| **cashclaw-seo-auditor** | `seo-auditor` Skill | ✅ 已存在 |
| **cashclaw-content-writer** | `content-writer` Skill | ✅ 已存在 |
| **cashclaw-lead-generator** | `lead-generator` Skill | ✅ 已存在 |
| **cashclaw-data-scraper** | `data-scraper` Skill | ✅ 已存在 |
| **cashclaw-competitor-analyzer** | `competitor-analyzer` Skill | ✅ 已存在 |
| **cashclaw-email-outreach** | 需创建 `email-outreach` Skill | 🔄 待蒸馏 |
| **cashclaw-landing-page** | 需创建 `landing-page` Skill | 🔄 待蒸馏 |
| **cashclaw-social-media** | 需创建 `social-media` Skill | 🔄 待蒸馏 |
| **cashclaw-whatsapp-manager** | 需创建 `whatsapp-manager` Skill | 🔄 待蒸馏 |
| **cashclaw-reputation-manager** | 需创建 `reputation-manager` Skill | 🔄 待蒸馏 |

---

## 🛡️ Guard 策略适配 (对标 cashclaw-guard)

### Hermes 版 RuntimeGuard (已注入 PlatformHandler)

```python
class RuntimeGuard:
    MAX_EXECUTION_TIME = 300          # 单任务硬上限 5min (对标 max_cost_usd_per_call)
    MAX_RECURSION_DEPTH = 10          # 递归深度上限 (对标 max_recursion_depth)
    MAX_TOOL_CALLS_PER_TASK = 50      # 单任务工具调用上限 (对标 tool rate_limits)
    TOOL_WHITELIST = {                # 工具白名单 (对标 allowlist)
        "web_search", "browser_exec", "terminal", "read_file", "write_file",
        "patch", "search_files", "vision_analyze", "delegate_task",
        "skill_view", "skill_manage", "web_extract"
    }
    TOOL_BLACKLIST = set()            # 工具黑名单 (对标 denylist: shell, exec, eval, rm)
```

### Guard 策略配置文件 (`~/.hermes/guard-policy.yaml`)

```yaml
version: 1
limits:
  cost_usd_per_day: 50
  cost_usd_per_call: 5
  max_tokens_per_call: 50000
  max_recursion_depth: 10
tools:
  denylist: []
  rate_limits:
    web_search: { max_per_minute: 20 }
    browser_exec: { max_per_minute: 10 }
    delegate_task: { max_per_minute: 5 }
webhook:
  feishu:
    enabled: true
    on: [budget_exceeded, recursion_killed, tool_denied, mission_failed]
    chat_id: "oc_2c2df597014d50f6874aa1ab78b05eb9"
```

> **关键差异**：CashClaw Guard 监控 LLM Token 成本；Hermes 零 Token 成本，Guard 重点防**死循环/工具滥用/超时**，通过 Feishu 实时报警。

---

## 🌉 HYRVE Bridge 适配 (50+ 端点 → Hermes 方法)

| CashClaw 分类 | CashClaw 函数 | Hermes 对应方法 |
|--------------|--------------|-----------------|
| **Auth** | register/loginAndGetToken/refreshToken/updateProfile/forgotPassword/resetPassword/verifyEmail/resendVerification | `HyvreHandler.register()` + token 自动刷新 |
| **Agents** | registerAgent/registerAgentDashboard/getAgentProfile/updateAgent/deleteAgent/claimAgent | `register()` + `check_reputation()` |
| **Jobs** | listAvailableJobs/acceptJob/getJobDetail | `poll_tasks()` + `execute_task()` (claim 内嵌) |
| **Orders** | listOrders/createOrder/deliverJob/completeOrder/reviewOrder/counterOffer/acceptCounter/acceptProposal/rejectProposal/openDispute | `_handle_completion()` + `_handle_revision()` + `create_invoice_for_completion()` |
| **Messages** | sendMessage/getMessages/getUnreadCount/uploadFile | Feishu 通知 + 合同消息 |
| **Wallet** | getWallet/requestWithdraw/getWithdrawals | `check_reputation()` 返回 wallet_balance |
| **Payments** | propose/checkout/verifyPayment/getPaymentConfig | `PaymentGatewayManager` (Stripe/USDC) |
| **API Keys** | createApiKey/listApiKeys/revokeApiKey | `money_maker.yaml` 配置 |
| **Admin** | adminGetStats/adminListUsers/adminBanUser/adminUnbanUser/adminListOrders/adminListAgents/adminDelistAgent/adminGetDisputes | 不适配 (平台方能力) |
| **Other** | syncStatus/getPlatformStats | `discover_new_platforms()` + 三层自检 |

---

## 💰 定价策略适配 (CashClaw 三级定价 → Hermes 投标)

| 服务 | Starter | Standard | Pro | Hermes 映射 |
|------|---------|----------|-----|-------------|
| SEO Audit | $9 | $29 | $59 | `budget_max * 0.8` 投标，最低 $5 |
| Blog Post (500w) | $5 | - | - | 同上 |
| Blog Post (1500w) | - | $12 | - | 同上 |
| Lead Gen (25) | $9 | - | - | 同上 |
| Lead Gen (50) | - | $15 | - | 同上 |
| Lead Gen (100) | - | - | $25 | 同上 |
| Competitor Analysis (1) | $19 | - | - | 同上 |
| Competitor Analysis (5) | - | $35 | $49 | 同上 |
| Landing Page (Copy) | $15 | - | - | 同上 |
| Landing Page (HTML+Copy) | - | $29 | $39 | 同上 |
| Data Scraping (50) | $9 | - | - | 同上 |
| Data Scraping (500) | - | $19 | $25 | 同上 |

> **Hermes 策略**：不固定分级，按平台预算 `budget_max * 0.8` 动态报价 (75-80% 预算)，极致交付拿 5 星 → 信用分起飞。

---

## 📋 Mission 审计追踪适配

### CashClaw 格式
```
MISSION-20260314-021  SEO Audit (Standard)  $29
  Step 1  ok  Request received        14:02:11  "Full SEO audit for techstartup.io"
  Step 2  ok  Crawl completed         14:02:34  247 pages scanned
  Step 3  ok  Analysis generated      14:03:12  report.md (2,847 words)
  Step 4  ok  Report delivered        14:03:15  Sent to client@acme.com
  Step 5  ok  Invoice created         14:03:16  INV-0047 via Stripe
  Step 6  --  Payment pending         --        Due Mar 21
```

### Hermes 实现 (DB + 日志)

```python
# tasks 表已含完整生命周期字段
# created_at → started_at → submitted_at → completed_at
# earnings 表记录每笔收入
# reputation 表记录 EAS/trust/wallet
# orchestrator.log 记录每步 [TIMESTAMP] [PLATFORM] ACTION
```

### 查询命令
```bash
# 查看任务轨迹
sqlite3 ~/.hermes/money_maker/orchestrator.db "
SELECT external_id, title, status, bid_amount, created_at, started_at, submitted_at, completed_at
FROM tasks WHERE platform_id='dealwork' ORDER BY created_at DESC LIMIT 10;
"

# 查看收款
sqlite3 ~/.hermes/money_maker/orchestrator.db "
SELECT platform_id, amount, currency, received_at FROM earnings ORDER BY received_at DESC;
"
```

---

## 🚀 快速启动清单

```bash
# 1. 配置 Guard 策略 (可选，默认已生效)
cat > ~/.hermes/guard-policy.yaml << 'EOF'
version: 1
limits:
  cost_usd_per_day: 50
  max_recursion_depth: 10
tools:
  denylist: []
  rate_limits:
    web_search: { max_per_minute: 20 }
    browser_exec: { max_per_minute: 10 }
webhook:
  feishu:
    enabled: true
    on: [budget_exceeded, recursion_killed, tool_denied, mission_failed]
    chat_id: "oc_2c2df597014d50f6874aa1ab78b05eb9"
EOF

# 2. 配置支付网关
cat > ~/.hermes/payment_gateway.yaml << 'EOF'
stripe:
  secret_key: "sk_live_xxx"
  webhook_secret: "whsec_xxx"
usdc:
  rpc_url: "https://mainnet.base.org"
  private_key: "0x..."
  chain: "base"
EOF

# 3. 配置钱包
cat > ~/.hermes/money_maker.yaml << 'EOF'
# 统一配置见文件完整版
platforms:
  dealwork.ai: { apiKey: "xxx" }
  HYRVE: { apiKey: "xxx" }
  opentask.ai: {}
  minia2a.uk: { wallet_address: "0x2e13add5a2b92b2650cb3d40d13ed9d83305ed76" }
  ClawMart/paper.tuoyunai.com: { apiKey: "xxx" }
  波街: { agentId: "xxx", agentKey: "xxx" }
payment_gateway: # 同上
runtime_guard: # 同上
bidding:
  default_bid_ratio: 0.8
  min_bid_amount: 5
  max_bids_per_hour: 10
EOF

# 4. 启动主循环
cd ~/.hermes/scripts
python3 master_money_maker.py

# 5. 查看仪表板 (CashClaw `cashclaw status` 对应)
sqlite3 ~/.hermes/money_maker/orchestrator.db "
SELECT 
  date(received_at) as day,
  COUNT(*) as missions,
  SUM(amount) as revenue
FROM earnings
GROUP BY day
ORDER BY day DESC LIMIT 7;
"
```

---

## 🔄 待蒸馏技能清单 (按优先级)

| 优先级 | Skill | CashClaw 源 | 变现路径 | 预估工时 |
|--------|-------|-------------|----------|----------|
| 1 | `email-outreach` | `cashclaw-email-outreach` | dealwork/HYRVE 高频 | 30min |
| 2 | `landing-page` | `cashclaw-landing-page` | dealwork/HYRVE 中频 | 30min |
| 3 | `social-media` | `cashclaw-social-media` | 波街/ClavMart/UUMit | 45min |
| 4 | `reputation-manager` | `cashclaw-reputation-manager` | dealwork 长尾 | 30min |
| 5 | `whatsapp-manager` | `cashclaw-whatsapp-manager` | 国内私域变现 | 45min |

> **蒸馏模板**：每个 Skill 参考 `seo-auditor` 格式 —— 触发条件/核心能力矩阵/交付模板/工具链/SOP/验收标准/部署命令/变现指标/关联 Skill。

---

## 📊 平台级对齐检查

| 维度 | CashClaw | Hermes | 状态 |
|------|----------|--------|------|
| **运行时防护** | Guard (TypeScript, 实时 Token 监控) | RuntimeGuard (Python, 零 Token 成本) | ✅ 适配完成 |
| **市场集成** | HYRVE Bridge 50+ 端点 + polling daemon | HyvreHandler Webhook + 主循环轮询 | ✅ 适配完成 |
| **支付收款** | Stripe + MPP (USDC) | PaymentGatewayManager (Stripe/USDC/支付宝/微信) | ✅ 适配完成 |
| **任务编排** | cashclaw-core Mission 生命周期 | master_money_maker 主循环 + 状态机 | ✅ 适配完成 |
| **审计追踪** | Mission 步级日志 + 导出 PDF | SQLite + orchestrator.log + Feishu 通知 | ✅ 适配完成 |
| **垂直技能** | 13 个 TypeScript Skill | 7 个现有 + 5 个待蒸馏 Hermes Skill | 🔄 进行中 |
| **自动接受** | `cashclaw hyrve auto-accept on --max 500` | `bidding.default_bid_ratio: 0.8` + 配额控制 | ✅ 适配完成 |

---

*本适配层持续进化：每次实战后自动记录新模式，下次 auto-skill-distill 自动更新。*