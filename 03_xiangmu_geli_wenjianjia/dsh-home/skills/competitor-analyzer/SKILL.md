---
name: competitor-analyzer
description: 竞品分析师：多维度竞品情报收集/对标/差距分析/机会挖掘，输出可执行竞品报告
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [competitor, analysis, intelligence, benchmark, market-research, revenue]
    related_skills: [seo-auditor, content-writer, lead-generator, data-scraper]
    requires_toolsets: [terminal, web, file, web_search]
---

# 竞品分析师

**核心使命**：多维度竞品情报收集、对标分析、差距识别、机会挖掘，输出**可执行的竞品分析报告与行动建议**。

---

## 🎯 适用场景

| 触发条件 | 产出物 |
|----------|--------|
| 客户要求 "竞品分析/对标/benchmark" | 完整竞品分析报告 + 差距矩阵 + 行动建议 |
| SEO 审计发现竞品排名超越 | 具体超越策略 + 执行清单 |
| 新市场/新产品切入前 | 市场格局图 + 切入点建议 |
| 融资/路演前竞品情报 | 投资级竞品画像 + 护城河分析 |

---

## 🎯 分析维度矩阵

| 维度 | 核心指标 | 数据源 | 产出形式 |
|------|----------|--------|----------|
| **产品/功能** | 核心功能/定价/定位/路线图/发布节奏 | 官网/文档/更新日志/社区 | 功能对比矩阵 + 定价对比表 |
| **流量/获客** | 流量来源/关键词/转化路径/广告投放/SEO 策略 | SimilarWeb/Ahrefs/SEMrush/Google Ads/社媒 | 流量漏斗图 + 关键词缺口表 |
| **内容/SEO** | 内容类型/发布频次/关键词覆盖/内链/外链/Schema | 站点地图/博客/文档/Schema | 内容缺口表 + 关键词机会清单 |
| **技术栈/架构** | 技术栈/基建/性能/安全/部署/开源项目 | Wappalyzer/BuiltWith/GitHub/招聘JD | 技术栈雷达图 + 架构差异表 |
| **团队/组织** | 团队规模/关键人/招聘/文化/融资/投资方 | LinkedIn/Crunchbase/PitchBook/招聘JD | 组织架构图 + 关键人画像 |
| **商业模式** | 定价/包装/变现/留存/扩展/合作伙伴 | 官网/定价页/条款/案例研究/合作伙伴页 | 商业模式画布 + 定价对比 |
| **用户/口碑** | 评价/评分/NPS/流失/流失原因/支持响应 | G2/Capterra/Trustpilot/Reddit/Twitter/Discord | 情感分析报告 + 痛点清单 |
| **财务/增长** | 收入/ARR/增长率/烧钱/估值/融资/投资方 | Crunchbase/PitchBook/财报/融资公告 | 财务雷达图 + 融资时间线 |

---

## 🔍 标准分析流程（SOP）

```python
def run_competitor_analysis(targets: list, depth: str = "standard") -> dict:
    """
    标准竞品分析入口
    :param targets: 竞品域名/名称列表
    :param depth: quick/standard/deep
    :return: 标准化分析报告
    """
    # 1. 预处理：标准化输入
    targets = normalize_targets(targets)
    
    # 2. 并行采集各维度数据
    raw_data = parallel_collect(targets, depth)
    
    # 3. 结构化分析
    analysis = analyze_all_dimensions(raw_data)
    
    # 4. 差距识别与机会挖掘
    gaps = identify_gaps(analysis, our_baseline)
    opportunities = find_opportunities(gaps, analysis)
    
    # 5. 生成可执行建议
    recommendations = generate_recommendations(gaps, opportunities)
    
    # 6. 生成交付物
    return generate_deliverables(analysis, gaps, opportunities, recommendations)
```

---

## 📊 标准交付物

```
competitor-analysis/
├── executive-summary.md          # 高管摘要：核心发现 + 顶级建议
├── competitor-profiles/          # 各竞品详细档案
│   ├── {competitor-1}.md
│   ├── {competitor-2}.md
│   └── ...
├── comparison-matrix.xlsx        # 多维对比矩阵
├── gap-analysis.md               # 差距分析：我们缺什么/他们强什么
├── opportunity-map.md            # 机会地图：可切入点/差异化切入点
├── action-plan.md                # 行动计划：优先级/责任人/时间线/资源
├── battlecards/                  # 战卡：销售/售前用的单页战卡
│   ├── {competitor-1}-battlecard.md
│   └── ...
├── data-appendix/                # 原始数据附件
│   ├── traffic-data.csv
│   ├── keyword-gaps.csv
│   ├── backlink-profile.csv
│   ├── tech-stack.csv
│   ├── pricing-comparison.csv
│   └── hiring-signals.csv
└── metadata.json                 # 元数据
```

---

## 🎯 竞品画像标准模板

```markdown
# {Competitor Name} - 竞品档案

## 基础档案
- **名称**: {name}
- **官网**: {url}
- **定位**: {positioning_statement}
- **成立时间**: {founded}
- **团队规模**: {team_size}
- **融资历史**: {funding_history}
- **核心投资方**: {investors}

## 产品与定价
| 维度 | 详情 |
|------|------|
| 核心产品 | {product_name} |
| 定价模式 | {pricing_model} |
| 价格区间 | {price_range} |
| 免费/试用 | {free_trial} |
| 核心功能 | {core_features} |
| 差异化卖点 | {USP} |

## 流量与获客
- **月访问量**: {monthly_visits}
- **主要来源**: {traffic_sources: organic/paid/direct/referral/social}
- **核心关键词**: {top_keywords}
- **广告投放**: {ad_channels: Google/Facebook/LinkedIn/Twitter}
- **SEO 权重**: {domain_authority} / {organic_keywords}

## 内容与 SEO
- **内容类型**: {blog/docs/case-studies/webinars/podcasts}
- **发布频次**: {posts_per_month}/月
- **核心关键词**: {target_keywords}
- **内容深度**: {avg_word_count} 字/篇
- **Schema 覆盖**: {schema_types}

## 技术栈与架构
- **前端**: {frontend_stack}
- **后端**: {backend_stack}
- **基建**: {infra: AWS/GCP/Azure/Vercel/Cloudflare}
- **性能**: {LCP/FCP/TTFB}
- **开源项目**: {github_org/repos}

## 团队与组织
- **团队规模**: {total_employees}
- **工程占比**: {engineering_ratio}
- **关键人物**: {key_people: LinkedIn URLs}
- **招聘信号**: {open_roles: 近期 JD 分析}
- **文化/价值观**: {culture_keywords}

## 用户口碑
- **G2 评分**: {g2_score} / {review_count}
- **Capterra 评分**: {capterra_score}
- **Trustpilot**: {trustpilot_score}
- **核心痛点**: {top_complaints}
- **核心优势**: {top_praises}

## 财务与增长
- **ARR/营收**: {arr_estimate}
- **增长率**: {yoy_growth}%
- **融资历史**: {funding_rounds}
- **估值**: {valuation}
- **烧钱率**: {burn_rate}/月

## SWOT 分析
| Strengths | Weaknesses |
|-----------|------------|
| {s1} | {w1} |
| {s2} | {w2} |

| Opportunities | Threats |
|---------------|---------|
| {o1} | {t1} |
| {o2} | {t2} |
```

---

## 📊 差距矩阵与机会地图

```markdown
# 差距矩阵

| 维度 | 我们 | 竞品 A | 竞品 B | 竞品 C | 差距 | 优先级 |
|------|------|--------|--------|--------|------|--------|
| SEO 权重 | 45 | 78 | 62 | 55 | -33 | P0 |
| 内容深度 | 3/5 | 5/5 | 4/5 | 3/5 | -2 | P1 |
| 定价灵活性 | 3/5 | 4/5 | 2/5 | 5/5 | -1 | P2 |
| API 文档 | 2/5 | 5/5 | 3/5 | 4/5 | -3 | P0 |
| 客户成功 | 3/5 | 4/5 | 3/5 | 2/5 | -1 | P2 |

# 机会地图

| 机会 | 切入点 | 预估价值 | 实施难度 | 优先级 |
|------|--------|----------|----------|--------|
| 竞品 A 内容薄弱 | 快速产出深度内容抢流量 | 高 | 低 | P0 |
| 竞品 B API 文档差 | 推出完美 API 文档切入开发者 | 中 | 中 | P1 |
| 竞品 C 定价死板 | 推出灵活定价抢价格敏感客户 | 高 | 低 | P0 |
| 竞品 D 无中文支持 | 本地化切入中文市场 | 高 | 中 | P1 |
```

---

## 🛠️ 零 Token 成本工具链

| 环节 | 工具/命令 | 备选 |
|------|-----------|------|
| 流量/关键词 | `web_search` (site:competitor + 关键词) + SimilarWeb 免费版 | SimilarWeb/Ahrefs 免费额度 |
| 反链/权威 | `web_search` (link:domain) + Google Search Console | 免费：GSC/Bing Webmaster |
| 技术栈识别 | `web_search` (BuiltWith/Wappalyzer 免费版) | Wappalyzer Chrome 插件 |
| 技术栈/招聘 | `web_search` (site:github.com org:xxx + site:linkedin.com jobs) | GitHub API / LinkedIn |
| 内容审计 | `browser_exec` (爬取站点地图/博客/文档) | Screaming Frog 免费版 |
| 关键词缺口 | `web_search` (site:competitor + 关键词) | 手工对比 |
| 反链分析 | `web_search` (link:domain / "brand mention") | 免费：GSC/Bing Webmaster |
| 技术栈识别 | `browser_exec` (Wappalyzer/Wappalyzer CLI) | 手工识别 |
| 页面速度 | `terminal` (lighthouse/PageSpeed) | PageSpeed Insights |

---

## 📦 交付标准

```
competitor-analysis-{date}/
├── executive-summary.md          # 高管摘要（1页）
├── competitor-profiles/          # 各竞品详细档案
├── comparison-matrix.xlsx        # 多维对比矩阵
├── gap-analysis.md               # 差距分析
├── opportunity-map.md            # 机会地图
├── action-plan.md                # 行动计划（优先级/责任人/时间线）
├── battlecards/                  # 战卡（销售/售前用）
├── data-appendix/                # 原始数据附件
└── metadata.json                 # 元数据
```

---

## 🔗 协作 Skill

| Skill | 协作方式 |
|-------|----------|
| `seo-auditor` | 审计出竞品关键词/流量来源 → 深度分析 |
| `content-writer` | 竞品内容缺口 → 指导内容生产方向 |
| `lead-generator` | 竞品客户/合作伙伴 → 线索挖掘 |
| `seo-auditor` | 竞品关键词策略 → 反哺 SEO 策略 |
| `lead-generator` | 竞品客户/合作伙伴 → 线索挖掘 |

---

## 🚀 部署到 Hermes

```bash
mkdir -p ~/.hermes/skills/revenue/competitor-analyzer/scripts
# SKILL.md 已创建
# 验证脚本
cat > ~/.hermes/skills/revenue/competitor-analyzer/scripts/validate.py << 'EOF'
#!/usr/bin/env python3
import shutil, subprocess, sys

tools = {
    "curl": ["curl", "--version"],
    "node": ["node", "--version"],
    "python3": ["python3", "--version"],
}
for name, cmd in [("curl", ["curl", "--version"]), ("python3", ["python3", "--version"])]:
    try:
        subprocess.run(cmd, capture_output=True, timeout=5, check=True)
        print(f"✅ {cmd[0]}: OK")
    except:
        print(f"❌ {cmd[0]}: MISSING")
EOF
```