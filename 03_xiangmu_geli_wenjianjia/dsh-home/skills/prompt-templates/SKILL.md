---
name: prompt-templates
description: 任务全生命周期提示词模板系统，参考 CashClaw 使命生命周期，适配 Hermes 零 Token 成本
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [prompt, template, lifecycle, mission, quote, upsell, revenue]
    related_skills: [seo-auditor, content-writer, lead-generator, invoice-manager]
    requires_toolsets: [terminal, web, file]
---

# 提示词模板系统 - 任务全生命周期

参考 CashClaw 使命生命周期，适配 Hermes 零 Token 成本架构，提供标准化的任务全生命周期提示词模板。

---

## 🎯 使命生命周期 8 阶段模板

### Stage 1: INTAKE (接单/需求确认)
```markdown
# INTAKE - 需求接收与确认

## 任务标识
- Mission ID: {mission_id}
- 客户: {client_name}
- 服务类型: {service_type}
- 状态: INTAKE
- 创建时间: {iso_timestamp}
- 预算范围: {budget_min}-{budget_max} {currency}

## 原始需求
{raw_request}

## 需求澄清清单（逐项确认）
- [ ] 目标明确性: 目标是否具体可测量？
- [ ] 范围边界: 包含/不包含内容是否清晰？
- [ ] 验收标准: 如何判定完成？
- [ ] 交付格式: 代码/文档/数据/部署/其他？
- [ ] 时间要求: 硬性截止日期 vs 期望完成时间？
- [ ] 预算匹配: 预算是否覆盖预估工时？
- [ ] 技术栈限制: 是否有强制技术栈/框架？
- [ ] 依赖资源: 是否需要客户提供数据/账号/环境？

## 澄清问题模板
> 感谢您的需求！为了确保精准交付，我需要确认几个细节：
> 1. {clarification_1}
> 2. {clarification_2}
> 3. {clarification_3}
> 请回复确认，我将在收到回复后 30 分钟内给出报价与时间表。
```

---

### Stage 2: QUOTE (报价/投标)
```markdown
# QUOTE - 报价单

## 报价单
**Mission ID**: {mission_id}
**客户**: {client_name}
**服务**: {service_type}
**交付物**: {deliverables_list}
**预估工时**: {estimated_hours} 小时
**报价金额**: ${amount:.2f} {currency}
**有效期**: 48 小时

## 包含内容
- {included_item_1}
- {included_item_2}
- {included_item_3}

## 不包含内容（避免范围蔓延）
- {excluded_item_1}
- {excluded_item_2}

## 交付时间表
- 开始: {start_date}
- 里程碑 1: {milestone_1_date} - {milestone_1_desc}
- 里程碑 2: {milestone_2_date} - {milestone_2_desc}
- 最终交付: {delivery_date}

## 付款条款
- 方式: {payment_method} (Stripe/支付宝/微信/USDC)
- 节点: 启动 50% / 交付 50%（或按平台托管规则）
- 货币: {currency}

## 附加价值（可选升级）
- 💡 我们还提供持续的 {related_service} 服务，起价 ${upsell_price}/月
- 想了解更多吗？

---
**报价有效期 48 小时**。确认后我将立即开始工作。
```

---

### Stage 3: PLAN (规划/分解)
```markdown
# PLAN - 执行计划

## Mission ID: {mission_id}
## 总工时预估: {total_hours}h
## 并行度: {parallelism} 个并行任务

## 任务分解
| 任务 ID | 阶段 | 任务描述 | 预估工时 | 依赖 | 产出物 | 验收标准 |
|---------|------|----------|----------|------|--------|----------|
| T001 | SETUP | 环境搭建/依赖安装/配置 | 0.5h | - | 环境就绪 | 依赖安装成功/配置生效 |
| T002 | RESEARCH | 需求调研/竞品分析/技术选型 | 2h | T001 | 调研报告/选型文档 | 文档完整/结论明确 |
| T003 | DESIGN | 方案设计/架构设计/接口定义 | 2h | T002 | 设计文档/API 规范 | 评审通过/文档完整 |
| T004 | EXECUTE | 核心功能实现 | 8h | T003 | 代码/配置/脚本 | 测试通过/功能完整 |
| T005 | TEST | 单测/集成测试/压测 | 2h | T004 | 测试报告/覆盖率 | 覆盖率>80%/零阻断缺陷 |
| T006 | DOC | 文档/部署指南/使用手册 | 1h | T005 | 文档包 | 文档完整/可直接部署 |
| T007 | DELIVER | 打包/交付/部署/验收 | 1h | T006 | 交付包 | 客户验收通过 |

## 风险缓解
| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 需求变更 | 高 | 中 | 变更控制流程/变更单/重新报价 |
| 依赖阻塞 | 中 | 高 | 并行任务/备选方案/提前沟通 |
| 技术债务 | 低 | 高 | 代码审查/重构预算/重构 Sprint |
```

---

### Stage 4-7: EXECUTE / REVIEW / REVISE / DELIVER
```markdown
# EXECUTE - 执行与交付

## 执行原则
1. **小步快跑**: 每个任务 ≤ 2h，完成即提交
2. **测试先行**: 先写测试/验收标准，再写实现
3. **持续同步**: 每 2h 同步进度，阻塞立即升级
3. **零 Token 成本**: 优先免费工具/本地工具/开源库

## 执行日志模板
```
[HH:MM] TASK-{id} START: {task_desc}
[HH:MM] TASK-{id} PROGRESS: {progress}% - {current_subtask}
[HH:MM] TASK-{id} BLOCKED: {blocker} - ESCALATED
[HH:MM] TASK-{id} DONE: {output_summary} | artifacts: {paths}
```

## 质量门禁（每个任务完成前必检）
- [ ] 代码/文档通过基础语法检查
- [ ] 核心功能通过自测/冒烟测试
- [ ] 产出物符合验收标准
- [ ] 文档/注释完整
- [ ] 无硬编码/无调试代码/无敏感信息泄露

---

### Stage 5: REVIEW (内部复盘)
```markdown
# REVIEW - 内部复盘清单

## 自我检查清单
- [ ] 所有验收标准 100% 满足
- [ ] 代码/文档通过基础检查（语法/格式/规范）
- [ ] 核心功能通过自测/冒烟测试
- [ ] 无硬编码/调试代码/敏感信息
- [ ] 文档/注释完整可读
- [ ] 交付包结构规范/可直接部署

## 交付包结构
```
deliverables/
├── README.md              # 使用说明/部署指南
├── src/                   # 源代码/核心文件
├── tests/                 # 测试用例/测试报告
├── docs/                  # 设计文档/API文档/使用手册
├── config/                # 配置文件/环境变量模板
├── scripts/               # 部署/运维/工具脚本
└── METADATA.json          # 元数据：版本/依赖/构建信息
```
```

---

### Stage 6: DELIVER (交付)
```markdown
# DELIVER - 正式交付

## 交付确认单
**Mission ID**: {mission_id}
**交付时间**: {timestamp}
**交付物清单**: {deliverables_list}
**验收链接**: {verification_urls}

## 交付话术模板
> 工作已完成，交付包已上传至 {delivery_path}。
> 
> **验收方式**：
> 1. 访问 {verification_url} 验证核心功能
> 2. 查看 {report_url} 完整测试报告
> 3. 解压 {package_url} 部署测试
> 
> **包含内容**：
> - {deliverable_1}: {description}
> - {deliverable_2}: {description}
> 
> 如有问题请随时反馈，我会在 1 小时内响应修复。
> 
> 正式发票已通过 {payment_method} 发送，请查收。
```

---

### Stage 7: REVISE (修订/迭代)
```markdown
# REVISE - 修订响应

## 修订响应 SLA
- 收到反馈: 15 分钟内确认收到
- 问题分析: 30 分钟内给出根因分析
- 修复交付: Critical 1h / High 4h / Medium 24h

## 修订响应模板
> 收到反馈，感谢指正。
> 
> **问题**: {issue_summary}
> **根因**: {root_cause}
> **修复方案**: {fix_plan}
> **预计完成**: {eta}
> 
> 已开始修复，预计 {eta} 交付修订版。
```

---

### Stage 8: COMPLETE (结项/收款)
```markdown
# COMPLETE - 结项与收款

## 结项检查单
- [ ] 客户验收通过
- [ ] 发票已开具/支付链接已发送
- [ ] 收款确认到账
- [ ] 结项记录入账
- [ ] 客户档案更新
- [ ] 经验/模板沉淀

## 收款确认模板
> 确认收到款项 ${amount} {currency}（{payment_method}）。
> 
> **交易详情**：
> - Mission: {mission_id}
> - 服务: {service_type}
> - 金额: ${amount} {currency}
> - 到账时间: {timestamp}
> - 交易 ID: {transaction_id}
> 
> 感谢信任！期待下次合作。
```

---

## 💡 Upsell 策略模板（结项后自动触发）

```markdown
# UPSELL - 升单建议

## 场景映射
| 当前服务 | 推荐升单 | 话术 |
|----------|----------|------|
| SEO Audit | Content Writing | "修复我们发现的内容缺口，持续产出高排名内容" |
| SEO Audit | Lead Generation | "基于审计出的高意图关键词，挖掘精准潜在客户" |
| Content Writing | SEO Audit | "内容产出后需 SEO 优化，确保收录排名" |
| Lead Gen | Email Outreach | "线索挖到手，需要专业邮件序列转化" |
| Data Scraping | Data Analysis | "数据挖到手，需要深度分析挖掘商业洞察" |

## 自动触发条件
- 任务状态 = COMPLETE
- 客户满意度 ≥ 4/5
- 间隔 ≥ 7 天未主动下单
- 有明确关联服务未购买

## 推荐话术
> 很高兴 {service} 顺利交付！🎉
> 
> 我们发现 {insight}，如果您需要 {upsell_service}，我们可以：
> - {benefit_1}
> - {benefit_2}
> - 优惠价 ${upsell_price} 起（原价 ${original_price}）
> 
> 感兴趣请回复，我发详细方案。
```

---

## 📁 任务文件标准结构

```
.missions/
  MISSION-{YYYYMMDD}-{SEQ}.md          # 任务总览
  MISSION-{YYYYMMDD}-{SEQ}/
    deliverables/                      # 交付产出
    logs/                              # 执行日志
  clients/
    {client-slug}.json                 # 客户档案
  ledger.jsonl                         # 追加式事件日志
  revenue.jsonl                        # 收入记录
  dashboard.json                       # 仪表盘聚合统计
  templates/
    quote.md                           # 报价模板
    invoice.md                         # 发票模板
```

---

## 📋 任务元数据标准

```json
{
  "mission_id": "MISSION-20261004-001",
  "client": "client-slug",
  "service": "seo-audit",
  "status": "INTAKE|QUOTE|PLAN|EXECUTE|REVIEW|DELIVER|REVISE|COMPLETE|BLOCKED",
  "created_at": "2026-10-04T09:00:00Z",
  "deadline": "2026-10-05T18:00:00Z",
  "budget": {"min": 50, "max": 200, "currency": "USD"},
  "price": 150,
  "currency": "USD",
  "skill": "seo-auditor",
  "stages": {
    "INTAKE": {"started": "...", "completed": "...", "notes": "..."},
    "QUOTE": {"started": "...", "sent": "...", "accepted": "...", "price": 150},
    "PLAN": {"started": "...", "completed": "...", "tasks": 7},
    "EXECUTE": {"started": "...", "tasks_completed": 5, "tasks_total": 7},
    "REVIEW": {"started": "...", "passed": true},
    "DELIVER": {"started": "...", "delivered": "...", "accepted": true},
    "REVISE": {"count": 0, "last_feedback": null},
    "COMPLETE": {"completed_at": "...", "amount": 150, "payment_method": "Stripe"}
  },
  "revision_count": 0,
  "upsell_suggested": ["content-writer", "lead-generator"]
}
```