---
name: cashclaw-email-outreach
description: Automates cold email sequences for dealwork/HYRVE outreach.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [email, outreach, cold-email, lead-generation, revenue]
    related_skills: [lead-generator, payment-gateway, invoice-manager]
    requires_toolsets: [terminal, web, file, web_search]
---

# Cold Email Outreach Automation

## When to Use
- Need to automate cold email sequences for dealwork/HYRVE outreach
- Want to automate follow-up sequences for lead generation
- Need to track email replies and handle bounces

**使命**：自动化冷邮序列发送、跟踪、回复处理，用于 dealwork/HYRVE 等平台的主动获客。

---

## 🎯 触发条件

- 需主动联系潜在客户 (ICP 匹配)
- 需跟进未回复线索
- 需批量发送个性化邮件

---

## 🔧 核心能力矩阵

| 能力 | 说明 | 工具链 |
|------|------|--------|
| **邮件模板引擎** | 变量替换、A/B 测试、SPF/DKIM 检查 | Jinja2 + DNS 检查 |
| **发送调度** | 限速、时区感知、退订处理 | SMTP + 限流器 |
| **回复监控** | IMAP/Graph API 监听、情感分析、自动分类 | IMAP/Graph API |
| **序列管理** | 多步骤、条件分支、触发器 | 状态机 |
| **数据清洗** | 邮箱验证、去重、退信处理 | Hunter/ZeroBounce API |

---

## 📋 标准序列模板

```yaml
sequence:
  - step: 1
    delay: 0
    template: "intro_{{industry}}"
    condition: "always"
  - step: 2
    delay: 3d
    template: "followup_value_{{pain_point}}"
    condition: "not_replied"
  - step: 3
    delay: 7d
    template: "breakup_soft"
    condition: "not_replied"
```

---

## 📋 标准执行流程

```python
def run_email_outreach(icp_criteria: dict, sequence_name: str) -> dict:
    """执行冷邮推广完整流程"""
    # 1. 获取/清洗线索
    leads = fetch_and_clean_leads(icp_criteria)
    
    # 2. 加载序列模板
    sequence = load_sequence(sequence_name)
    
    # 3. 执行发送调度
    results = schedule_and_send(leads, sequence)
    
    # 4. 监控回复
    monitor_replies(results)
    
    return {"sent": len(results), "replied": 0, "bounced": 0}
```

---

## ⚠️ 关键注意事项

1. **合规性** - 遵守 CAN-SPAM/GDPR，含退订链接
2. **声誉管理** - 预热域名、监控退信率、SPF/DKIM/DMARC
3. **个性化** - 至少 3 个动态变量，避免模板感
4. **发送限速** - 新域名日发 <50，逐步预热
5. **数据隐私** - 加密存储、最小化收集、定期清理

---

## 💰 变现指标

| 指标 | 目标 | 基准 |
|------|------|------|
| 打开率 | > 40% | 行业均值 20% |
| 回复率 | > 10% | 行业均值 1-5% |
| 转化率 | > 2% | 视产品而定 |
| 退信率 | < 2% | 必须 < 5% |

---

## 🔗 关联 Skill

| Skill | 协作方式 |
|-------|----------|
| `lead-generator` | 提供 ICP 匹配的线索列表 |
| `payment-gateway` | 成交后自动开票 |
| `invoice-manager` | 管理发票和收款 |
| `cashclaw-invoice-manager` | 统一开票管理 |

---

*基于 CashClaw email-outreach 模式适配 Hermes 架构，持续进化。*