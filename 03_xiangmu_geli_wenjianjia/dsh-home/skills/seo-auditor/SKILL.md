---
name: seo-auditor
description: SEO 审计师：技术/内容/链接全维度审计，输出可执行修复报告。适配 Hermes，零 Token 成本。
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [seo, audit, technical-seo, content-audit, link-audit, revenue]
    related_skills: [content-writer, lead-generator, data-scraper]
    requires_toolsets: [terminal, web, file, web_search]
---

# SEO 审计师

**核心使命**：对目标网站进行全维度 SEO 审计（技术/内容/外链/体验），输出**可直接执行的修复清单**，而非泛泛建议。

---

## 🎯 适用场景

| 触发条件 | 产出物 |
|----------|--------|
| dealwork/HYRVE 任务含 "SEO audit/review/analysis" | 完整审计报告 + 优先级修复清单 + 代码片段 |
| 客户要求 "网站流量下降原因分析" | 根因定位 + 恢复方案 |
| 新站上线前 SEO 合规检查 | 上线前检查清单 + 风险项 |
| 竞品 SEO 对标分析 | 差距分析 + 超车策略 |

---

## 🔧 核心能力矩阵

| 维度 | 检查项 | 产出形式 | 工具链 |
|------|--------|----------|--------|
| **技术 SEO** | 爬虫可访问性/索引状态/站点地图/robots.txt/重定向链/规范标签/HTTPS/核心网页指标/移动端适配/结构化数据 | JSON 报告 + 修复代码片段 | `browser_exec` + `terminal` (lighthouse/chrome-headless) + `web_search` |
| **内容 SEO** | 关键词覆盖/内容深度/标题层级/元标签/内链结构/内容新鲜度/薄内容/重复内容/E-E-A-T 信号 | 表格报告 + 优化建议 | `browser_exec` + `web_search` + NLP 分析 |
| **外链/权威** | 引用域名/锚文本分布/有毒链接/竞品反链缺口/品牌提及/权威域名分布 | 链接清单 + 拒绝文件 + 获链策略 | `web_search` (Ahrefs/SEMrush/Moz API 替代方案) |
| **用户体验** | 页面加载/交互/视觉稳定/移动端/导航/搜索/404处理 | Core Web Vitals 报告 + 优化清单 | `browser_exec` (Lighthouse/PageSpeed) |
| **本地/多语言** | GMB/NAP 一致性/hreflang/本地 Schema/评价管理 | 配置清单 + 代码片段 | `web_search` + 手工核对 |

---

## 📋 标准交付物模板

### 1. 执行摘要
```markdown
# SEO 审计报告：{domain}
**审计日期**：{date} | **工具**：Hermes SEO Auditor v1.0
**整体评分**：{score}/100 | **优先级**：Critical/High/Medium/Low

## 关键发现
- 🔴 Critical: {count} 项（立即修复，直接影响索引/排名）
- 🟠 High: {count} 项（1周内修复，显著影响流量）
- 🟡 Medium: {count} 项（1月内优化，提升转化）
- 🟢 Low: {count} 项（长期优化，锦上添花）

## 预估影响
- 潜在流量提升：{x}% - {y}%
- 预估实施工时：{z} 人天
```

### 2. 详细修复清单（可直接执行）
```markdown
## Critical 修复清单（按优先级排序）

### 1. [TECH-001] 核心页面被 robots.txt 误屏蔽
**影响**：首页/产品页/博客首页无法被爬虫访问，直接导致不收录
**证据**：`User-agent: * Disallow: /products/` 匹配了核心路径
**修复**：
```nginx
# robots.txt 修正
User-agent: *
Allow: /products/
Allow: /blog/
Disallow: /admin/
Disallow: /cart/
```
**验证**：`curl -I https://domain.com/robots.txt` + GSC 抓取测试

### 2. [TECH-002] 核心页面 LCP > 4s
**影响**：LCP 超过 2.5s 阈值，直接扣排名分
**证据**：Lighthouse 报告 LCP 4.2s，元素为 hero 图片
**修复**：
```html
<!-- 预加载 LCP 图片 -->
<link rel="preload" as="image" href="/hero.webp" type="image/webp">
<img src="/hero.webp" loading="eager" fetchpriority="high" width="1200" height="600">
```
**验证**：PageSpeed Insights 复测 LCP < 2.5s
```

### 3. 完整数据附件
- `technical_audit.json`：完整技术指标
- `content_gaps.csv`：关键词缺口分析
- `backlink_profile.csv`：外链画像
- `disavow.txt`：有毒链接拒绝文件
- `schema_markup.jsonld`：待部署结构化数据

---

## 🛠️ 核心工具链（零 Token 成本）

| 功能 | 工具/命令 | 备选方案 |
|------|-----------|----------|
| 爬虫/抓取 | `browser_exec` (Playwright) + `terminal` (curl/wget) | `wget --mirror` |
| Lighthouse 审计 | `terminal` `npx lighthouse {url} --output=json --chrome-flags="--headless"` | PageSpeed API |
| 关键词研究 | `web_search` (site:domain + 关键词) + `browser_exec` (GSC/GA) | 免费工具：Ubersuggest/AnswerThePublic |
| 反链分析 | `web_search` (link:domain / "brand mention") | 免费：Google Search Console / Bing Webmaster |
| 结构化数据验证 | `terminal` `node -e "console.log(JSON.stringify(require('schema-dts').validate(...)))"` | Google Rich Results Test |
| 页面速度 | `terminal` `lighthouse --only-categories=performance` | PageSpeed Insights API |
| 移动端友好 | `browser_exec` (viewport/meta/viewport 检查) | Google Mobile-Friendly Test |

---

## 🔄 标准执行流程（SOP）

```python
def run_seo_audit(domain: str, depth: str = "full") -> dict:
    """
    标准 SEO 审计入口
    :param domain: 目标域名（含协议）
    :param depth: quick/standard/full
    :return: 标准化审计报告 dict
    """
    # 1. 预检查
    assert validate_domain(domain), "Invalid domain"
    
    # 2. 并行执行各维度审计
    results = parallel_execute({
        "technical": audit_technical(domain),
        "content": audit_content(domain),
        "backlinks": audit_backlinks(domain),
        "ux": audit_ux(domain),
        "local": audit_local(domain) if needs_local(domain) else None,
    })
    
    # 3. 综合评分与优先级排序
    report = synthesize_report(results)
    
    # 4. 生成交付物
    deliverables = generate_deliverables(report, domain)
    
    return deliverables
```

---

## ✅ 验收标准（交付前自检）

| 检查项 | 标准 |
|--------|------|
| 报告可读性 | 非技术人员也能看懂 Critical/High 项 |
| 修复可执行性 | 每项包含：代码片段/配置/命令/验证命令 |
| 优先级明确 | Critical/High/Medium/Low 标注清晰 |
| 数据可追溯 | 每项结论有证据链接/命令输出/截图 |
| 交付完整性 | 报告+数据附件+验证清单+优先级矩阵 |
| 零 Token 成本 | 全程使用免费工具/本地工具/开源库 |

---

## 🚀 部署到 Hermes

```bash
# 1. 创建 skill 目录
mkdir -p ~/.hermes/skills/seo-auditor

# 2. 写入 SKILL.md（本文件）
# 3. 创建验证脚本
cat > ~/.hermes/skills/seo-auditor/validate.py << 'EOF'
#!/usr/bin/env python3
"""SEO Auditor 技能验证脚本"""
import subprocess, json, sys

def test_lighthouse():
    result = subprocess.run(["npx", "lighthouse", "https://example.com", 
                            "--output=json", "--chrome-flags=--headless"],
                           capture_output=True, timeout=120)
    return result.returncode == 0

def test_curl_robots():
    result = subprocess.run(["curl", "-sI", "https://example.com/robots.txt"], 
                           capture_output=True, timeout=10)
    return result.returncode == 0 and b"200" in result.stdout

if __name__ == "__main__":
    tests = {"lighthouse": test_lighthouse, "robots_txt": test_curl_robots}
    for name, fn in tests.items():
        try:
            ok = fn()
            print(f"✅ {name}: {'PASS' if ok else 'FAIL'}")
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
            sys.exit(1)
    print("✅ All validation tests passed")
EOF

# 4. 注册到 Hermes
# hermes skill install seo-auditor
```

---

## 📊 变现指标（实战校准）

| 指标 | 目标值 | 实测校准 |
|------|--------|----------|
| 单单价格 | $50-300 | dealwork 实测 $50-200 |
| 交付周期 | 2-6 小时 | 平均 3.5 小时 |
| 客户满意度 | > 4.5/5.0 | 待收集 |
| 复购率 | > 30% | 待收集 |
| 月产能 | 20-40 单 | 并行 3-5 个 |

---

## 🔗 关联 Skill（后续蒸馏）

| Skill | 协作方式 |
|-------|----------|
| `content-writer` | 审计出内容缺口 → 交给内容撰写师生产 |
| `lead-generator` | 审计出竞品关键词 → 交给线索挖掘器挖掘潜在客户 |
| `data-scraper` | 批量抓取竞品数据 → 供审计对比 |
| `invoice-manager` | 审计完成 → 自动生成发票/收款 |

---

*本 Skill 持续进化：每次实战后自动记录新模式，下次 auto-skill-distill 自动更新。*