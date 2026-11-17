---
name: lead-generator
description: 线索挖掘师：基于 ICP 画像，多源挖掘+清洗+画像+评分，输出可直接外联的高意向线索清单
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [lead, generation, prospecting, b2b, icp, enrichment, scoring, revenue]
    related_skills: [seo-auditor, content-writer, data-scraper, invoice-manager]
    requires_toolsets: [terminal, web, file, web_search]
---

# 线索挖掘师

**核心使命**：基于理想客户画像（ICP），从多源挖掘潜在客户，完成清洗、画像、评分，输出**可直接外联的高意向线索清单**。

---

## 🎯 适用场景

| 触发条件 | 产出物 |
|----------|--------|
| 客户提供 ICP 画像 | 高意向线索清单 + 外联话术 |
| SEO 审计发现高意图关键词 | 基于关键词挖掘搜索者线索 |
| 内容发布后植入线索捕获 | 表单提交者自动画像评分 |
| 竞品客户挖掘 | 竞品客户名单 + 切入点分析 |

---

## 🎯 ICP 画像标准（输入标准）

```json
{
  "icp": {
    "company": {
      "size": "10-200",
      "industry": ["SaaS", "FinTech", "E-commerce", "HealthTech"],
      "location": ["US", "CA", "UK", "DE", "SG"],
      "revenue": "1M-50M",
      "tech_stack": ["React", "Node.js", "AWS", "PostgreSQL"]
    },
    "persona": {
      "titles": ["CTO", "VP Engineering", "Head of Product", "Founder"],
      "seniority": "Director+",
      "pain_points": ["技术债务", "交付慢", "人才招聘难", "技术选型失误"],
      "goals": ["加速交付", "降低技术债务", "提升团队效能"]
    },
    "signals": {
      "tech": ["招聘 Senior/Lead", "技术栈迁移", "融资公告", "新产品发布"],
      "content": ["发布技术博客", "开源项目", "技术分享"],
      "hiring": ["大量招聘", "新设岗位", "团队扩张"]
    }
  }
}
```

---

## 🔍 多源挖掘矩阵

| 来源 | 方法 | 关键词/查询 | 产出 | 工具 |
|------|------|-------------|------|------|
| **LinkedIn** | 搜索/销售导航 | site:linkedin.com "title" "company" "location" | 个人档案 URL | web_search + browser_exec |
| **公司官网** | 团队页/招聘页/博客 | site:domain.com "hiring" "team" "about" | 团队结构/痛点 | browser_exec + web_search |
| **GitHub** | 组织/成员/贡献者 | org:xxx members / repo contributors | 技术栈/活跃度 | web_search + GitHub API |
| **招聘网站** | JD 分析 | site:indeed.com "company" "tech stack" | 技术栈/扩张信号 | web_search |
| **融资/新闻** | Crunchbase/TechCrunch | "company" "funding" "series" | 融资阶段/扩张 | web_search |
| **内容平台** | Medium/Dev.to/Substack | author:company 技术博客 | 技术栈/痛点 | web_search |
| **开源项目** | GitHub Org/Stars/Forks | org:xxx stars:>100 | 技术栈/团队能力 | GitHub API / web_search |
| **招聘信号** | LinkedIn Jobs/Indeed | "company" "hiring" "senior" | 扩张方向/技术栈 | web_search |

---

## 🧹 线索清洗与去重流程

```python
def clean_and_deduplicate(raw_leads: list) -> list:
    """线索清洗标准流程"""
    cleaned = []
    seen = set()  # (domain, email, linkedin_url)
    
    for lead in raw_leads:
        # 1. 基础字段补全
        lead = enrich_basic_fields(lead)
        
        # 2. 去重键
        dedup_key = (
            lead.get("domain", "").lower(),
            lead.get("email", "").lower(),
            lead.get("linkedin", "").lower()
        )
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        
        # 3. 邮箱格式验证
        if lead.get("email") and not validate_email(lead["email"]):
            lead["email"] = None
            lead["email_verified"] = False
        else:
            lead["email_verified"] = True
            
        # 4. LinkedIn URL 标准化
        if lead.get("linkedin"):
            lead["linkedin"] = normalize_linkedin(lead["linkedin"])
            
        # 5. 公司域名标准化
        if lead.get("domain"):
            lead["domain"] = normalize_domain(lead["domain"])
            
        cleaned.append(lead)
    
    return cleaned
```

---

## 🎯 线索评分模型（0-100 分）

| 维度 | 权重 | 评分规则 |
|------|------|----------|
| **ICP 匹配度** | 30% | 公司规模/行业/地区/技术栈/收入/地域 全匹配=30，缺1项-5，缺2项-10 |
| **人员匹配度** | 25% | 职级/职能/决策权 全匹配=25，仅影响者-10 |
| **意图信号** | 25% | 招聘/融资/内容发布/开源/技术栈迁移/竞品提及 每个信号 +5，上限 25 |
| **联系方式完整度** | 10% | 邮箱验证通过=10，仅 LinkedIn=5，仅域名=2 |
| **时效性** | 10% | 7天内活跃=10，30天内=5，90天内=2，更久=0 |

**评分分级**：
- **A 级 (80-100)**：立即外联，高转化
- **B 级 (60-79)**：常规外联，常规转化
- **C 级 (40-59)**：培育池，内容营销/AD 受众
- **D 级 (<40)**：归档，不主动外联

---

## 📧 外联话术模板（按评分分级）

### A 级 - 直击痛点
```markdown
> Hi {first_name}，
> 
> 看到 {company} 正在 {signal: 招聘 Senior/融资/技术栈迁移}，我们帮 {similar_company} 解决了 {pain_point}，{result}。
> 
> 想知道我们如何帮 {company} {benefit} 吗？15 分钟通话同步。
> 
> 方便的话，回复个时间，我发日历邀请。
```

### B 级 - 价值前置
```markdown
> Hi {first_name}，
> 
> 我们刚帮 {industry} 企业 {result}。想到 {company} 可能也面临 {pain_point}。
> 
> 整理了份《{industry} {topic} 避坑指南》，想发给您参考。需要吗？
```

### C 级 - 内容触达
```markdown
> Hi {first_name}，
> 
> 刚发了篇《{article_title}》，覆盖了 {topic}。觉得 {company} 团队可能用得上。
> 链接：{url}
> 
> 有反馈随时交流。
```

---

## 📦 交付标准

```
leads-package/
├── leads.csv                    # 标准化线索表
├── leads-scored.csv             # 含评分明细
├── leads-A-grade.csv            # A 级线索（优先外联）
├── outreach-templates.md        # 话术模板
├── icp-profile.json             # ICP 画像
├── signals-detected.json        # 检测到的信号明细
├── enrichment-report.md         # 画像补充报告
└── metadata.json                # 元数据：来源/时间/评分模型版本
```

### leads.csv 标准字段
| 字段 | 必填 | 说明 |
|------|------|------|
| lead_id | ✅ | 唯一标识 |
| company_name | ✅ | 公司名称 |
| domain | ✅ | 公司域名 |
| company_size | | 规模 |
| industry | | 行业 |
| location | | 地区 |
| tech_stack | | 技术栈 |
| person_name | ✅ | 姓名 |
| title | ✅ | 职位 |
| seniority | | 资历 |
| email | | 邮箱 |
| email_verified | | 邮箱验证状态 |
| linkedin | | LinkedIn URL |
| linkedin_verified | | LinkedIn 验证状态 |
| phone | | 电话 |
| icp_score | ✅ | 0-100 |
| grade | ✅ | A/B/C/D |
| signals | | 检测到的信号列表 |
| source | ✅ | 来源平台 |
| source_url | | 来源链接 |
| enriched_at | ✅ | 画像完成时间 |

---

## 📊 变现指标

| 指标 | 目标值 |
|------|--------|
| 单价 | $50-200/百条线索 |
| 线索准确率 | ≥ 85% (邮箱验证通过) |
| ICP 匹配度 | ≥ 70% A/B 级占比 |
| 交付周期 | 2-6 小时 |
| 线索转化率 | 客户端外联转化 ≥ 15% |

---

## 🔗 协作 Skill

| Skill | 协作方式 |
|-------|----------|
| `seo-auditor` | 审计出高意图关键词 → 挖掘搜索者线索 |
| `content-writer` | 文章末尾植入线索捕获表单/CTA |
| `invoice-manager` | 线索交付 → 自动生成发票 |
| `seo-auditor` | 线索来源关键词反哺 SEO 策略 |

---

## 🚀 部署到 Hermes

```bash
mkdir -p ~/.hermes/skills/revenue/lead-generator/scripts
# SKILL.md 已创建
# 验证脚本
cat > ~/.hermes/skills/revenue/lead-generator/scripts/validate.py << 'EOF'
#!/usr/bin/env python3
import shutil, sys

tools = {
    "curl": ["curl", "--version"],
    "node": ["node", "--version"],
    "python3": ["python3", "--version"],
}
for name, cmd in [("curl", ["curl", "--version"]), ("python3", ["python3", "--version"])]:
    try:
        import subprocess
        subprocess.run(cmd, capture_output=True, timeout=5, check=True)
        print(f"✅ {cmd[0]}: OK")
    except:
        print(f"❌ {cmd[0]}: MISSING")
EOF
```