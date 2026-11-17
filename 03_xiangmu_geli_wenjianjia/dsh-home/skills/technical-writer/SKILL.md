---
name: technical-writer
description: 技术文档师：API/开发者/用户/架构文档全栈产出，从 OpenAPI 到部署指南，零 Token 成本
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [technical-writing, documentation, api-docs, openapi, developer-experience, revenue]
    related_skills: [seo-auditor, content-writer, data-scraper, competitor-analyzer]
    requires_toolsets: [terminal, web, file, web_search]
---

# 技术文档师

**核心使命**：产出**开发者友好、可直接使用、持续可维护**的技术文档，从 API 参考到架构决策记录全栈覆盖。

---

## 🎯 适用场景

| 触发条件 | 产出物 |
|----------|--------|
| API 发布/更新 | OpenAPI/Swagger + SDK 示例 + 认证指南 |
| 新功能发布 | 功能文档 + 迁移指南 + 破坏性变更日志 |
| 开发者入职/对外开放 | 快速开始 + SDK 指南 + 最佳实践 |
| 架构评审/合规 | ADR + 威胁建模 + 合规清单 |

---

## 📚 文档类型矩阵

| 类型 | 目标受众 | 核心要素 | 交付周期 |
|------|----------|----------|----------|
| **API 参考** | 开发者 | 端点/参数/响应/错误码/示例/Schema | 2-4h |
| **快速开始** | 新开发者 | 5分钟跑通/认证/首个请求/常见错误 | 1-2h |
| **SDK/库指南** | 开发者 | 安装/配置/核心API/进阶用法/迁移 | 3-5h |
| **架构决策记录 (ADR)** | 架构师/Tech Lead | 背景/决策/后果/替代方案/影响 | 1-2h |
| **部署/运维指南** | DevOps/SRE | 部署/配置/监控/告警/扩容/回滚 | 2-3h |
| **安全/合规** | 安全/法务 | 威胁模型/数据流/合规清单/审计 | 2-4h |
| **故障排查/FAQ** | 支持/开发者 | 症状/根因/解决/预防/联系方式 | 1-2h |

---

## 📋 标准文档结构

### API 参考标准结构
```markdown
# {API 名称} API 参考

## 概览
- **Base URL**: `https://api.example.com/v1`
- **认证**: `Bearer Token` / `API Key` / `OAuth 2.0`
- **限流**: 100 req/min (可申请提升)
- **版本**: `v1` (当前稳定) | `v2` (Beta)

## 认证
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.example.com/v1/health
```

## 端点列表
| 方法 | 路径 | 说明 | 认证 | 限流 |
|------|------|------|------|------|
| GET | /health | 健康检查 | 否 | 1000/min |
| POST | /v1/tasks | 创建任务 | 是 | 100/min |

## 端点详情

### POST /v1/tasks
创建新任务

**请求**
```json
{
  "title": "string, required",
  "description": "string, optional",
  "priority": "low|normal|high, default: normal"
}
```

**响应 (201)**
```json
{
  "id": "task_abc123",
  "title": "My Task",
  "status": "pending",
  "created_at": "2026-10-04T09:00:00Z"
}
```

**错误码**
| 码 | 含义 | 解决 |
|------|------|------|
| 400 | 参数错误 | 检查请求体 |
| 401 | 未认证 | 检查 Token |
| 429 | 限流 | 降低频率/申请提升 |
| 500 | 服务端错误 | 重试/联系支持 |

**代码示例**
```python
import requests
resp = requests.post("https://api.example.com/v1/tasks",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={"title": "My Task"})
print(resp.json())
```

```cURL
curl -X POST https://api.example.com/v1/tasks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Task"}'
```

---

## 快速开始标准结构
```markdown
# 快速开始

## 前置条件
- Python 3.10+ / Node 18+ / Go 1.21+
- API Key (从 [Dashboard](https://dashboard.example.com) 获取)

## 30 秒跑通
```bash
# 1. 安装 SDK
pip install example-sdk

# 2. 配置
export EXAMPLE_API_KEY="your-key"

# 3. 运行第一个请求
python -c "
from example import Client
client = Client(api_key='your-key')
print(client.health())
"
```

## 常见问题
| 问题 | 解决 |
|------|------|
| 401 Unauthorized | 检查 API Key 是否正确/过期 |
| 429 Rate Limited | 降低频率/申请提升限额 |
| 500 Server Error | 重试/查看状态页/联系支持 |
```

---

## 📋 文档质量清单

| 维度 | 标准 | 验证 |
|------|------|------|
| **准确性** | 所有示例可直接运行 | CI 自动运行示例代码 |
| **完整性** | 覆盖所有公开端点/参数/错误码 | OpenAPI Spec 覆盖率 100% |
| **一致性** | 术语/格式/风格统一 | Vale/Stylelint 自动检查 |
| **可用性** | 新手 10 分钟上手 | 新人测试/可用性测试 |
| **可维护性** | 单一来源/自动生成/版本控制 | 单一来源原则/自动化生成 |
| **可发现性** | 搜索/导航/版本切换/语言切换 | Algolia/DocSearch 集成 |

---

## 🛠️ 零 Token 成本工具链

| 环节 | 工具 | 备选 |
|------|------|------|
| **OpenAPI 编辑** | VS Code + OpenAPI 插件 / Swagger Editor | Stoplight Studio |
| **文档站点** | Mintlify / Docusaurus / VitePress / GitBook | MkDocs + Material |
| **API 测试** | `terminal` (curl/HTTPie) / Postman CLI | Hoppscotch |
| **示例验证** | `terminal` (自动运行代码片段) | GitHub Actions |
| **链接检查** | `terminal` (markdown-link-check) | Lychee |
| **拼写/术语** | Vale / cspell | cSpell |
| **部署** | Vercel / Netlify / Cloudflare Pages / GitHub Pages | 自建 Nginx |

---

## 📦 交付包标准

```
docs-package/
├── openapi.yaml              # OpenAPI 3.1 规范
├── postman_collection.json   # Postman 集合
├── docs/                     # Markdown 文档源文件
│   ├── getting-started.md
│   ├── api-reference.md
│   ├── sdk-guide.md
│   ├── adr/
│   └── troubleshooting.md
├── code-samples/             # 多语言示例
│   ├── python/
│   ├── javascript/
│   ├── go/
│   └── curl/
├── sdks/                     # SDK 发布包 (可选)
│   ├── python/
│   ├── javascript/
│   └── go/
├── assets/                   # 图片/图表/Logo
├── redoc/                    # Redoc 静态站点
├── metadata.json             # 元数据
└── README.md                 # 包说明
```

---

## 📊 变现指标

| 指标 | 目标值 |
|------|--------|
| 单价 | $200-2000/项目 |
| 交付周期 | 1-5 天 |
| 文档覆盖率 | 100% 公开 API |
| 示例可运行率 | 100% |
| 客户满意度 | ≥ 4.5/5 |

---

## 🔗 协作 Skill

| Skill | 协作方式 |
|-------|----------|
| `seo-auditor` | API 文档 SEO 优化 / 开发者搜索意图分析 |
| `content-writer` | 技术博客/教程配套文档 |
| `data-scraper` | 竞品 API 文档采集 → 对标分析 |
| `competitor-analyzer` | 竞品文档对标 / 差距分析 |

---

## 🚀 部署到 Hermes

```bash
mkdir -p ~/.hermes/skills/revenue/technical-writer/scripts

cat > ~/.hermes/skills/revenue/technical-writer/scripts/validate.py << 'EOF'
#!/usr/bin/env python3
import shutil, subprocess, sys

checks = {
    "node": ["node", "--version"],
    "npx": ["npx", "--version"],
    "markdownlint": ["npx", "markdownlint", "--version"],
    "markdown-link-check": ["npx", "markdown-link-check", "--version"],
    "vale": ["vale", "--version"],
    "spectral": ["npx", "@stoplight/spectral", "--version"],
    "redocly": ["npx", "@redocly/cli", "--version"],
    "spectral": ["npx", "@stoplight/spectral", "--version"],
}

for name, cmd in [
    ("node", ["node", "--version"]),
    ("markdownlint", ["npx", "markdownlint", "--version"]),
    ("markdown-link-check", ["npx", "markdown-link-check", "--version"]),
]:
    try:
        import subprocess
        subprocess.run(cmd, capture_output=True, timeout=10, check=True)
        print(f"✅ {cmd[0]}: OK")
    except:
        print(f"❌ {cmd[0]}: MISSING (可后续安装)")

print("Technical Writer 环境检查完成")
EOF
```