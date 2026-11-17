---
name: web-content-fetcher
description: Use when regular web_fetch/web_search fails to fetch webpage content due to Cloudflare, paywalls, or anti-scraping. Supports r.jina.ai (general), markdown.new (Cloudflare), defuddle.md (fallback). Do NOT use for normal web browsing.
author: Boss
metadata:
  openclaw:
    emoji: 🌐
    tags:
    - web
    - fetch
    - markdown
    - cloudflare
    - bypass
  hermes:
    fallback_for_toolsets:
    - web
---





# 网页内容获取工具

当常规 web_fetch/web_search 无法获取内容时，使用替代服务获取网页 Markdown 格式内容。

## 支持的服务

| 优先级 | 服务 | 用法 | 适用场景 |
|--------|------|------|----------|
| 1 | **r.jina.ai** | `https://r.jina.ai/{url}` | 最稳定，通用性强 |
| 2 | **markdown.new** | `https://markdown.new/{url}` | Cloudflare 保护网站 |
| 3 | **defuddle.md** | `https://defuddle.md/{url}` | 备用方案 |

## 使用方法

### 直接调用

当需要获取网页内容时，按顺序尝试：

1. 首先用 `web_fetch` 尝试获取
2. 如果失败或被过滤，调用本工具

```bash
# 使用 jina.ai (首选)
curl -s "https://r.jina.ai/https://example.com"

# 使用 markdown.new (Cloudflare)
curl -s "https://markdown.new/https://example.com"

# 使用 defuddle.md (备用)
curl -s "https://defuddle.md/https://example.com"
```

### API 格式

```bash
# 简单获取
fetch_webpage <url>

# 指定方法
fetch_webpage <url> --method jina|markdown|defuddle
```

## 示例

```
用户: 帮我获取 https://news.example.com/article/123 的内容
助手: (使用 r.jina.ai 获取)
```

## 工具脚本

本目录包含 `fetch.sh` 脚本，可直接调用：

```bash
./fetch.sh https://example.com
./fetch.sh https://example.com jina
```

---

*让网页内容获取不再受限 🌐*
