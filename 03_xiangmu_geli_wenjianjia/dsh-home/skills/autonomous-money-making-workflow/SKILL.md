---
name: autonomous-money-making-workflow
description: "持续自主赚钱闭环：全网找合法渠道→验证跑通→上架/投标→交付收款→技能蒸馏→扩大复制 [DISABLED]"
version: 1.0.0
author: User, Hermes Agent
license: MIT
platforms: [linux, windows, macos]
metadata:
  hermes:
    tags: [autonomous, money-making, workflow, skill-distillation, continuous-learning]
    related_skills: [auto-skill-distill, hermes-agent-skill-authoring, session-librarian]
    requires_toolsets: [terminal, web, skills, file]
---

# 自主赚钱闭环工作流

**核心使命**：在合法合规前提下，持续发现、验证、执行、扩大赚钱渠道，形成"干中学、学中干"的自我进化闭环。

---

## 🎯 核心循环（每轮执行）

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 发现渠道 (Discover)                                           │
│    - 全网搜索合法赚钱渠道(A2A/自由职业/技能变现/数据标注/API等)   │
│    - 筛选：有API/可自动化、真实出金案例、非灰产、门槛可跨越       │
│    - 产出：候选渠道清单 + 优先级评分                              │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. 验证跑通 (Validate)                                           │
│    - 注册账号、配置凭据、跑通最小闭环(注册→发布/投标→接单→收款)   │
│    - 实测：能否真实出金、到账时间、手续费、单价区间              │
│    - 产出：验证报告 + 可用性评级(S/A/B/C) + 标准化操作SOP         │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. 批量执行 (Execute)                                            │
│    - 将验证通过的渠道接入 master 编排器自动化                    │
│    - 持续：轮询任务/投标/上架服务/监控收款                       │
│    - 异常自检、自动修复、飞书实时通知                            │
│    - 产出：真实收益 + 执行日志 + 性能指标                         │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. 蒸馏进化 (Distill & Evolve)                                   │
│    - 复盘：哪些渠道赚到了钱、哪些卡住、哪些技能缺失             │
│    - 缺技能→找权威书/官方文档/最佳实践→蒸馏成 skill              │
│    - 优化 SOP、调整优先级、扩大规模、开拓新渠道                  │
│    - 产出：新 skill + 更新编排器 + 更新优先级策略                │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
                    回到第 1 步 (持续循环)
```

---

## 📋 执行标准（每步必做）

### 1. 发现渠道 - 来源与筛选标准
| 来源 | 搜索关键词 | 筛选硬指标 |
|------|-----------|-----------|
| 搜索引擎 | "AI agent marketplace earn money 2024 real withdrawal" | 有真实出金截图/案例 |
| GitHub/Awesome列表 | "awesome-ai-agents", "agent-marketplace" | Star>100、近6月活跃 |
| Reddit/HackerNews | "I made $X with AI agents", "freelance AI agent" | 具体金额、时间、平台名 |
| 官方文档 | 平台 skill.md / API docs | 有完整 API、自动化支持 |
| 竞品观察 | 同类 agent 在哪接单、发什么服务 | 可复制的服务类型 |

**红线（直接排除）**：
- 灰产/刷单/模拟器/广告欺诈/APK复刻
- 无API、需人工实名/人脸/手机号、仅App端
- 承诺"躺赚/日入过万/零门槛"的营销号
- 单价极低(<$1)、需大量人工、ROI算不过来

### 2. 验证跑通 - 最小闭环清单
| 步骤 | 验收标准 |
|------|----------|
| 注册/认证 | 能拿到 API Key / 凭据文件 |
| 发布/投标 | 能成功创建服务帖/投标/上架技能 |
| 接单/匹配 | 能收到任务/订单/私信 |
| 交付/执行 | 能按要求产出交付物(代码/文档/数据/结果) |
| 验收/结算 | 平台确认完成、释放托管/打款 |
| 提现到账 | 钱到微信/支付宝/USDC/银行卡，记录到账时间/手续费 |

**输出**：`验证报告.md` (渠道名、评级、单价区间、出金周期、SOP链接、风险点)

### 3. 批量执行 - 编排器接入标准
| 要求 | 实现 |
|------|------|
| 统一入口 | 所有平台在 master_money_maker.py 注册 Handler |
| 统一调度 | 主循环 5 分钟轮询：poll_tasks → execute_task → check_contracts |
| 统一凭据 | ~/.hermes/money_maker/orchestrator.db + 平台专用 cred 文件 |
| 统一监控 | bid_status_monitor(5min) + cred_self_check(10min) + full_check(2h) |
| 统一通知 | 飞书实时：投标接受/拒绝、合同开始、收款到账、异常报警 |
| 统一日志 | DB 记录：tasks, bid_history, contracts, reputation, earnings |

### 4. 蒸馏进化 - 技能缺口 → Skill 流程
```
发现缺技能 (如: 不会写Claude Code插件、不懂某平台API、不会做数据标注)
    ↓
找权威源 (官方文档 > 权威书籍 > 高赞实战博客 > 官方示例代码)
    ↓
用 auto-skill-distill 流程蒸馏
    ↓
生成 skill (放入 ~/.hermes/skills/xxx/)
    ↓
编排器自动加载，下轮循环即可用
```

**蒸馏触发条件**：
- 连续 3 次同类任务失败/卡住
- 新渠道需要新技能栈(如: 某平台要写 Rust、要用特定框架)
- 单价可提升但缺核心能力(如: 从写脚本→写完整 SaaS、从数据清洗→建模训练)

---

## 🛠️ 技能蒸馏子流程（复用 auto-skill-distill）

当需要新技能时，**直接调用**：

```bash
# 1. 明确需求
NEED="需要学会: 编写 Anthropic Claude Code 插件，包含: 工具定义、上下文注入、流式响应处理、MCP 集成"

# 2. 找权威源
SOURCES=(
  "https://docs.anthropic.com/claude-code/plugins"  # 官方文档
  "https://github.com/anthropics/claude-code-plugin-examples"  # 官方示例
  "Plugin Development Guide"  # 官方 PDF/文档
)

# 3. 蒸馏成 skill
skill_manage action="create" name="claude-code-plugin-dev" content="$(cat << 'EOF'
---
name: claude-code-plugin-dev
description: 开发 Anthropic Claude Code 插件：工具定义、上下文注入、流式响应、MCP 集成。
version: 0.1.0
author: User, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [plugin, claude-code, anthropic, mcp]
    related_skills: [hermes-agent-skill-authoring]
---
# 权威源: 官方文档 + 官方示例仓库
## When to Use
- 需要为 Claude Code 开发自定义工具/插件
- 需要集成 MCP Server 到 Claude Code
## Procedure
1. 读取官方 Plugin API 文档
2. 克隆官方示例仓库分析结构
3. 按标准模板创建插件项目
4. 实现工具定义 schema + 处理器
5. 测试: npm run dev / claude-code --plugin ./dist
## Verification
- 插件在 Claude Code 中可见且可调用
- 工具调用返回正确结果
- 流式响应正常渲染
EOF
)"
```

---

## 📊 当前渠道优先级矩阵（动态更新）

| 渠道 | 状态 | 评级 | 单价区间 | 出金周期 | 当前动作 | 优先级 |
|------|------|------|----------|----------|----------|--------|
| dealwork.ai | 验证通过 | S | $24-72 | 1-3天 | 4投标pending | P0 |
| HYRVE | API就绪 | A | 未知 | 未知 | 轮询jobs | P1 |
| AgentHansa | API就绪 | A | $10-200+ | 未知 | 需加盟+checkin | P1 |
| ClawMart | 监控中 | B | 7-14元 | 微信即时 | 任务池全灰产 | P2 |
| 波街 | 服务帖待审 | B | 自定价 | 支付宝托管 | 等曝光/私信 | P2 |
| UUMit | 后台运行 | B | 任务制 | 未知 | 4 timer跑后台 | P3 |
| minia2a.uk | 钱包就绪 | C | 微支付 | USDC即时 | 需上架技能服务 | P3 |

**新渠道发现队列**（持续更新）：
- [ ] Fiverr/Upwork API 自动化投标
- [ ] Replicate/Banana GPU 推理变现
- [ ] HuggingFace Spaces 商业化
- [ ] 数据标注平台
- [ ] 专业技术写作/文档变现
- [ ] 代码审查/安全审计服务
- [ ] MCP Server 商业化

---

## ⚡ Master 编排器集成清单

### 已完成
- [x] master_money_maker.py 主循环 (5min)
- [x] bid_status_monitor.py (5min) - dealwork 投标状态
- [x] cred_self_check.py (10min) - dealwork 凭据自检+自修复
- [x] full_platform_self_check.py (2h) - 7平台全景自检
- [x] 7平台凭据配置 + DB 同步
- [x] 飞书通知统一

### 进行中（需补全各 Handler 的 execute_task）
- [ ] dealwork.ai: `check_contracts` 已有，需补 `START_WORK` → 交付 → `SUBMIT_WORK` 完整流程
- [ ] HYRVE: 补全 `poll_tasks` → `claim_job` → 执行 → `submit`
- [ ] AgentHansa: 补全 `checkin`、加盟选择、`submit_quest`、红包抢夺
- [ ] ClawMart: 补全 `claim_task` → 执行 → `submit_result`
- [ ] 波街: 补全私信监听、任务接受、交付
- [ ] UUMit: 已跑后台 timer，需把能力映射到 master 统一调度
- [ ] minia2a: 补全技能上架、x402 服务调用、收益统计

### 待开发：新渠道发现模块
- [ ] `discover_new_channels.py` - 定期搜索、评分、写入候选池
- [ ] `validate_channel.py` - 自动化最小闭环验证
- [ ] `channel_registry.json` - 渠道元数据注册表（评级、SOP、Handler类名）

---

## 🚨 红线与止损

| 红线 | 触发动作 |
|------|----------|
| 连续 7 天 0 收入 | 触发全渠道复盘，暂停低优先级，集中资源跑通 1 个 |
| 单渠道连续 20 次投标全拒 | 降级该渠道优先级，分析拒标原因(价格/技能/信誉) |
| 平台 API 变更/封号 | 24h 内切换备用渠道，迁移凭据，不影响主力 |
| 技能蒸馏连续 3 次失败 | 降级该技能优先级，换权威源重试 |
| 单日电费/服务器成本 > 当日收益 | 立即停止该渠道，算账优化 |

---

## 📁 关键文件清单

| 文件 | 说明 |
|------|------|
| `/home/user01/.hermes/scripts/master_money_maker.py` | 主编排器 |
| `/home/user01/.hermes/scripts/bid_status_monitor.py` | 5min 投标监控 |
| `/home/user01/.hermes/scripts/cred_self_check.py` | 10min 凭据自检 |
| `/home/user01/.hermes/scripts/full_platform_self_check.py` | 2h 全景自检 |
| `/home/user01/.hermes/scripts/discover_new_channels.py` | 新渠道发现(待建) |
| `/home/user01/.hermes/scripts/validate_channel.py` | 渠道验证(待建) |
| `/home/user01/.hermes/money_maker/orchestrator.db` | 统一状态 DB |
| `/home/user01/.hermes/money_maker/channel_registry.json` | 渠道注册表(待建) |
| `~/.hermes/skills/devops/auto-skill-distill/` | 技能蒸馏 skill |

---

## 🔁 这是一个活文档

**每次循环结束，必须更新本 skill：**
1. 渠道优先级矩阵
- 新增/移除渠道
- 评级变更
- 单价/出金周期实测值
2. 编排器集成清单
- 完成/进行中/待开发 勾选
3. 新渠道发现队列
- 新增来源、筛选结果
4. 红线触发记录
- 触发时间、原因、应对动作
4. 新蒸馏的 skill 链接

**更新方式**：`skill_manage action="patch" name="autonomous-money-making-workflow" content="<完整新内容>"`

---

## 🎯 现在的执行指令

**立即执行**：补全 dealwork.ai `check_contracts` 完整交付流程（最近最可能出钱）
**并行**：HYRVE/AgentHansa Handler 补全
**后台**：新渠道发现脚本开发、minia2a 技能上架
**持续**：三层自检跑着、飞书通知通着、DB 记录存着

**记住**：不赚到钱不算数。每轮循环结束看 `earnings` 表有没有新记录。