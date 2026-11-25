# Session 2026-08-25: ModelScope MCP Server (bing-cn) 实测记录

## 背景
用户提供 ModelScope MCP 端点：`https://mcp.api-inference.modelscope.net/62eea0fb085c46/mcp`（streamable_http 传输），要求接入 Hermes 并验证。

## 实测步骤

### 1. 升级 mcp 包（关键）
```bash
/home/user01/.hermes/hermes-agent/venv/bin/python -m pip install --upgrade mcp
# 结果：mcp 2.1.1（支持 streamable_http）
```

### 2. 添加服务器
```bash
hermes mcp add bing-cn --url "https://mcp.api-inference.modelscope.net/62eea0fb085c46/mcp"
# 交互提示：
#   Does this server require authentication? [Y/n]: n
#   Enable all 2 tools? [Y/n/select]: y
# 结果：✓ Saved 'bing-cn' to ~/.hermes/config.yaml (2/2 tools enabled)
```

### 3. 验证连接
```bash
hermes mcp test bing-cn
# 结果：
# Testing 'bing-cn'...
#   Transport: HTTP → https://mcp.api-inference.modelscope.net/62eea0fb085c46/mcp
#   Auth: none
#   ✓ Connected (1935ms)
#   ✓ Tools discovered: 2
#     bing_search    - 使用必应中文搜索引擎搜索信息
#     crawl_webpage  - 根据UUID抓取网页内容，批量支持，过滤黑名单
```

### 4. 配置落盘
```yaml
# ~/.hermes/config.yaml
mcp_servers:
  bing-cn:
    url: https://mcp.api-inference.modelscope.net/62eea0fb085c46/mcp
    enabled: true
```

### 5. 实战测试
```bash
hermes chat -q "使用 bing_search 搜索 'Python MCP 协议'"
# Agent 自动调用 mcp__bing__bing_search 多次，返回中文搜索结果
```

## 发现的工具

| 工具 | 说明 |
|------|------|
| `mcp__bing__bing_search` | 必应中文搜索，返回标题/链接/摘要 |
| `mcp__bing__crawl_webpage` | 按搜索结果 UUID 抓取网页内容，批量支持，自动过滤黑名单（知乎/小红书等） |

## 关键坑点（已验证）

| 坑点 | 解决 |
|------|------|
| mcp 包版本过旧 | 必须 >= 2.1 才支持 `streamable_http`，升级命令见上 |
| 交互式输入阻塞 | 用 `printf "n\ny\n" \| hermes mcp add ...` 非交互式跑通 |
| 网关需重启才能加载工具 | `systemctl --user restart hermes-gateway` 或等 cron 重载 |
| 认证 token 不写 config.yaml | 存 keyring，重装需重新 add |

## 验证清单
- [x] `hermes mcp list` 显示 `bing-cn` enabled
- [x] `hermes mcp test bing-cn` 返回 Connected + 2 tools
- [x] `config.yaml` 有 `mcp_servers.bing-cn` 配置
- [x] 实际 chat 中自动调用 `mcp__bing__bing_search` 成功