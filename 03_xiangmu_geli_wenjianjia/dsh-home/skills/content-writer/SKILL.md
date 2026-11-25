---
name: content-writer
description: 内容撰写师：技术/营销/SEO 文章全栈产出，从大纲到成品，零 Token 成本
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [content, writing, seo, technical-writing, marketing, blog, revenue]
    related_skills: [seo-auditor, lead-generator, data-scraper]
    requires_toolsets: [terminal, web, file, web_search]
---

# 内容撰写师

**核心使命**：产出**可直接发布、SEO 友好、转化导向**的高质量内容，从选题到成品全流程自动化。

---

## 🎯 适用场景

| 触发条件 | 产出物 |
|----------|--------|
| SEO 审计发现内容缺口 | 完整文章 + 发布就绪包 |
| 客户需要 "技术博客/技术文档/营销文案" | 成品 + 发布清单 |
| SEO 关键词覆盖缺口 | 批量文章 + 发布计划 |
| 竞品内容分析后的内容策略 | 内容日历 + 首批成品 |

---

## 📝 内容类型矩阵

| 类型 | 字数 | 结构 | SEO 要点 | 交付周期 |
|------|------|------|----------|----------|
| **技术教程** | 2000-4000 | 问题→方案→代码→测试→扩展 | 长尾词/代码片段/Schema | 2-4h |
| **技术深度解析** | 3000-5000 | 背景→原理→实战→对比→展望 | 核心词+长尾/结构化数据 | 3-5h |
| **产品对比/评测** | 2000-3000 | 维度表/优缺点/适用场景/结论 | 对比词/评测Schema | 2-3h |
| **行业趋势/深度报告** | 4000-8000 | 数据/趋势/案例/预测/建议 | 行业词/数据可视化 | 4-8h |
| **案例研究** | 2000-3000 | 背景/挑战/方案/结果/复盘 | 品牌词/案例Schema | 2-3h |
| **技术文档/API 文档** | 3000-6000 | 概览/快速开始/参考/示例/错误码 | 导航/搜索/代码示例 | 3-5h |

---

## 📋 标准产出包

```
deliverables/
├── article.md              # 正文（Markdown，含 Front Matter）
├── images/                 # 配图/图表/代码截图
├── code/                   # 代码示例/可运行 Demo
├── seo-package.json        # SEO 包：关键词/元标签/Schema/内链建议
├── social-snippets.md      # 社媒分发片段：Twitter/LinkedIn/Reddit
├── publishing-checklist.md # 发布前检查清单
└── metadata.json           # 元数据：字数/关键词/目标受众/阅读时长
```

---

## 📝 标准文章结构模板

```markdown
---
title: "{SEO 标题，含核心词，≤60字符}"
description: "{Meta Description，含核心词+价值主张，150-160字符}"
keywords: ["核心词", "长尾词1", "长尾词2", "长尾词3"]
target_audience: "{目标受众画像}"
reading_time: "{预估阅读分钟数} min"
difficulty: "Beginner|Intermediate|Advanced"
schema_type: "Article|HowTo|TechArticle|FAQPage"
---

# {H1 标题，含核心词，有吸引力}

> **TL;DR** {一句话核心价值，≤50字}

## 🎯 为什么读这篇？（读者收益）
- {收益点 1}
- {收益点 2}
- {收益点 3}

## 📚 背景与问题
{问题背景 + 痛点 + 为什么现在解决}

## 🛠️ 核心方案（分步骤）
### 步骤 1：{标题}
{说明 + 代码/配置/截图}

```language
# 可直接复制运行的代码
```

> ⚠️ **避坑指南**：{常见错误 + 避免方法}

### 步骤 2：{标题}
...

## 📊 结果与验证
- **指标 1**：{数值 + 对比}
- **指标 2**：{数值 + 对比}

## ❓ 常见问题 (FAQ)
### Q1: {常见问题}
**A**: {简练回答}

### Q2: {常见问题}
**A**: {简练回答}

## 🔗 延伸阅读/相关资源
- [{相关文章 1}]({url})
- [{工具/资源 1}]({url})

## 📌 关键要点回顾
- {要点 1}
- {要点 2}
- {要点 3}

---

> **下一步**：{行动号召：下载代码/试用工具/阅读下篇/联系我们}
```

---

## 🎯 SEO 优化清单（每篇必检）

| 项目 | 标准 | 验证方式 |
|------|------|----------|
| 标题长度 | 50-60 字符，含核心词前置 | 字符计数 |
| Meta Description | 150-160 字符，含核心词+价值 | 字符计数 |
| H1 含核心词 | 唯一 H1，含核心词 | HTML 检查 |
| H2/H3 覆盖长尾 | ≥ 3 个 H2，覆盖长尾词 | 结构检查 |
| 关键词密度 | 核心词 1-2%，长尾词自然分布 | 密度工具 |
| 内链/外链 | ≥ 3 个内链，≥ 2 个权威外链 | 链接检查 |
| 图片 Alt | 所有图片含描述性 Alt | 批量检查 |
| Schema Markup | Article/HowTo/FAQ 结构化数据 | Google Rich Results Test |
| 核心网页指标 | LCP<2.5s/CLS<0.1/FID<100ms | Lighthouse |
| 移动端适配 | 响应式/字体≥16px/点击区≥48px | Mobile-Friendly Test |

---

## 🛠️ 零 Token 成本工具链

| 环节 | 工具 | 备选 |
|------|------|------|
| 选题/关键词 | `web_search` (site:competitor + 关键词) + GSC/GA | Ubersuggest/AnswerThePublic |
| 大纲生成 | `web_search` (竞品大纲分析) + 手工结构化 | 手工 |
| 写作 | 本地编辑器 + `terminal` (Markdown lint) | VS Code + Markdown All in One |
| 代码示例 | `terminal` (运行验证) + `browser_exec` (截图) | 本地运行 |
| 图表/图表 | `terminal` (Mermaid/PlantUML/PlantUML) | Mermaid Live Editor |
| SEO 检查 | `terminal` (lighthouse/markdown-link-check) | 手工核对 |
| 发布包 | `terminal` (打包/压缩/校验) | 手工打包 |

---

## 📦 交付包标准

```
article-package/
├── article.md              # 正文（含 Front Matter）
├── images/                 # 所有图片（WebP，≤100KB/张）
├── code/                   # 代码文件（可直接运行）
├── seo-package.json        # SEO 包
│   ├── keywords: [...]
│   ├── meta_title: ""
│   ├── meta_description: ""
│   ├── schema_markup: {}
│   ├── internal_links: [...]
│   └── external_links: [...]
├── social-snippets.md      # 社媒分发片段
├── publishing-checklist.md # 发布前检查
└── metadata.json           # 元数据
```

---

## 📊 变现指标

| 指标 | 目标值 | 备注 |
|------|--------|------|
| 单价 | $50-500 | 视类型/深度/行业 |
| 交付周期 | 2-8 小时 | 平均 4h |
| 字数/小时 | 800-1200 词/h | 含调研/写作/优化 |
| SEO 得分 | ≥ 90/100 | Lighthouse/自研评分 |
| 客户满意度 | ≥ 4.5/5 | 待收集 |

---

## 🔗 协作 Skill

| Skill | 协作方式 |
|-------|----------|
| `seo-auditor` | 审计出内容缺口 → 交给内容撰写师 |
| `lead-generator` | 文章植入线索捕获表单/CTA |
| `seo-auditor` | 发布后复盘 → 复盘数据反馈优化 |
| `lead-generator` | 文章末尾植入线索捕获/CTA |

---

## 🚀 部署到 Hermes

```bash
mkdir -p ~/.hermes/skills/revenue/content-writer
# SKILL.md 已创建
# 创建验证脚本
cat > ~/.hermes/skills/revenue/content-writer/scripts/validate.py << 'EOF'
#!/usr/bin/env python3
import shutil, subprocess, sys

tools = {
    "node": ["node", "--version"],
    "npx": ["npx", "--version"],
    "markdownlint": ["npx", "markdownlint", "--version"],
    "markdown-link-check": ["npx", "markdown-link-check", "--version"],
}
for name, cmd in [("node", ["node", "--version"]), ("markdownlint", ["npx", "markdownlint", "--version"])]:
    try:
        subprocess.run(cmd, capture_output=True, timeout=10, check=True)
        print(f"✅ {cmd[0]}: OK")
    except:
        print(f"❌ {cmd[0]}: MISSING")
EOF
```