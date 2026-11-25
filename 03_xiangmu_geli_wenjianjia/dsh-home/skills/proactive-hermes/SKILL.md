---
name: proactive-hermes
version: 1.0.0
description: 'Use when you want to transform Hermes from reactive to proactive: daily briefings, weekly skill distillation, repo health checks, price monitoring. Provides cron templates, heartbeat hooks, Working Buffer persistence. Do NOT use for one-off task automation.'
author: Hermes Agent
tags:
- proactive
- automation
- cron
- heartbeat
- WAL
- self-improving
requires:
- python: '>=3.10'
- pip:
  - pyyaml
metadata:
  hermes:
    requires_toolsets:
    - terminal
    - cronjob
---





# Proactive Hermes 🦞

**将 Hermes 从「等任务」变成「主动伙伴」** — 移植自 Hal Labs 的 Proactive Agent 架构，适配 Hermes Gateway + Cron + Skills 体系。

---

## 核心三支柱

| 支柱 | 含义 | Hermes 实现 |
|------|------|-------------|
| **主动** | 不等指令、预判需求、反向提示 | `cronjob` 定时任务 + `delegate_task` 子代理 + 心跳检查 |
| **持久** | 熬过上下文丢失、关键细节不丢 | `memory-local` 向量记忆 + WAL 协议（钩子自动落盘）+ Working Buffer |
| **自我改进** | 越用越顺手、错误不重犯 | `learning-capture` 技能 + `auto-skill-distill` 每日技能提炼 |

---

## 已就绪的 Hermes 原生能力（直接用，别重复造）

| 能力 | 对应 proactive 概念 | 状态 |
|------|---------------------|------|
| `memory-local` + hooks | WAL Protocol / Working Buffer | ✅ 运行中（session:start/end, agent:end 自动存取） |
| `cronjob` (systemd timer) | Autonomous Crons | ✅ 2 个已跑：`memory-local-compression` (03:00), `auto-skill-distill` (04:00) |
| `delegate_task` + subagents | Proactive research / parallel work | ✅ 可用 |
| `verify-hermes-setup` | Security hardening / health check | ✅ 8 项检查 |
| `hermes-agent-skill-authoring` | Skill installation vetting | ✅ 规范文档 |
| `requesting-code-review` | Security scan before commit | ✅ 质量门禁 |

---

## 新增：主动式 Cron 模板

把「想做但一直没空做」的事变成 Cron，睡醒就有结果。

### 1. 每日早报（早 8:00 推送到 Feishu）
```bash
hermes cron create \
  --name "daily-briefing" \
  --schedule "0 8 * * *" \
  --prompt "生成每日简报：1) 昨天完成了什么（查 memory-local），2) 今天日历/待办，3) 值得关注的技术/行业动态（web_search），4) 主动建议：有什么能帮用户省力的自动化？" \
  --deliver "feishu" \
  --skills "memory-local,web-content-fetcher"
```

### 2. 周末技能蒸馏（周日 10:00）
```bash
hermes cron create \
  --name "weekly-skill-distill" \
  --schedule "0 10 * * 0" \
  --prompt "分析本周所有会话，提炼可复用的操作模式 → 生成/更新 Hermes skill（参考 auto-skill-distill 逻辑）" \
  --deliver "local" \
  --skills "memory-local,hermes-agent-skill-authoring"
```

### 3. 代码库健康巡检（每 2 小时）
```bash
hermes cron create \
  --name "repo-health" \
  --schedule "0 */2 * * *" \
  --prompt "检查 ~/projects 下所有 git 仓库：未提交变更、CI 失败、依赖过期、安全漏洞 → 汇总报告" \
  --deliver "local" \
  --skills "github"
```

### 4. 价格/库存监控（按需）
```bash
hermes cron create \
  --name "price-watch-<product>" \
  --schedule "0 */6 * * *" \
  --prompt "查 <product> 价格/库存，低于阈值推送 Feishu" \
  --deliver "feishu" \
  --skills "product-price-monitor"
```

---

## Heartbeat 机制（移植自 Proactive Agent）

**不再是「收到心跳回 OK」，而是每次心跳都做点有用的事。**

在 Hermes 里：**Gateway 接收到平台消息 = 心跳触发点**。

### 可在 `hooks/memory-local/handler.py` 的 `on_message_received()` 里加入：
```python
def on_message_received(context):
    # 1. 检查邮件/日历（如果配了 google-workspace）
    # 2. 扫描关键日志错误
    # 3. 查 memory-local 有没遗漏的待办
    # 4. 如果发现「重要邮件/即将到会/新错误/>8h没说话」 → 主动推送 Feishu
    pass
```

### 触发主动推送的条件（参考 AGENTS.md）：
- ✅ 重要未读邮件
- ✅ <2h 即将开始的日程
- ✅ 关键服务报错（systemd failed、cron 失败、GPU 显存溢出）
- ✅ 发现高价值自动化机会（如：重复手动操作 >3 次）
- ❌ 深夜非紧急不打扰
- ❌ 用户明显在忙（高频消息中）

---

## Working Buffer：熬过「危险区」

**危险区** = 对话进行中、尚未触发 `session:end`、记忆还在内存缓冲、上下文可能被压缩截断的窗口。

Hermes `memory-local` 的 `save_every_n_turns=5` 已缓解。再加一层：

```python
# 在 hooks/memory-local/handler.py 的 on_turn_end() 里
def on_turn_end(context):
    # 现有逻辑：提取事实 → pending_memories
    # 新增：关键决策/修正/阻塞点 → 即时写入 Working Buffer 文件
    working_buffer = Path("~/.hermes/working-buffer.md").expanduser()
    if "决定" in context.response or "修正" in context.response or "报错" in context.response:
        with open(working_buffer, "a") as f:
            f.write(f"\n## {datetime.now():%H:%M} - {context.session_id}\n")
            f.write(f"User: {context.message[:200]}\n")
            f.write(f"Assistant: {context.response[:200]}\n")
            f.write("---\n")
```

**恢复**：新会话 `session:start` 时，自动读取 `working-buffer.md` 最近 50 行注入上下文。

---

## 验证清单（移植自 security-audit.sh）

```bash
# 一键跑通 proactive-hermes 健康检查
hermes skill run proactive-hermes audit
```

检查项：
- [ ] `memory-local` hooks 已加载（gateway 日志有 `1 hook(s) loaded`）
- [ ] Cron 任务 `memory-local-compression` / `auto-skill-distill` 状态 `enabled`
- [ ] `.credentials/` 权限 600，`.gitignore` 包含 `.env` `.credentials/`
- [ ] `AGENTS.md` / `USER.md` / `SOUL.md` 存在且更新 < 7 天
- [ ] 无硬编码密钥在 skill/脚本里
- [ ] `verify-hermes-setup` 全绿

---

## 快速开始

```bash
# 1. 启用每日早报（需配置 Feishu webhook）
hermes cron create --name daily-briefing --schedule "0 8 * * *" \
  --prompt "生成每日简报..." --deliver feishu --skills "memory-local,web-content-fetcher"

# 2. 加入 Working Buffer 到 memory-local hook（一次性）
# 编辑 ~/.hermes/hooks/memory-local/handler.py，在 on_turn_end 追加工作缓冲写入

# 3. 运行审计
hermes skill run proactive-hermes audit
```

---

## 文件结构

```
~/.hermes/skills/proactive-hermes/
├── SKILL.md
├── scripts/
│   ├── audit.py           # 健康检查入口
│   ├── heartbeat.py       # 心跳处理逻辑（可集成到 memory-local hook）
│   └── working_buffer.py  # Working Buffer 读写
├── references/
│   └── AGENTS.md          # 操作规范（从 proactive-agent 移植精简版）
└── templates/
    └── cron-templates.yaml # 常用 Cron 模板
```