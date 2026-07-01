# 🛡️ Pre-Tool-Use Hook: 危险命令拦截

> 一个 Claude Code `pre-tool-use` hook，拦截危险 bash 命令。

## 安装

两步搞定：

```bash
# 1. 克隆
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use.py ~/.claude/hooks/

# 2. 生效
chmod +x ~/.claude/hooks/pre-tool-use.py
```

下次 Claude Code 执行任何 bash 命令时，这个 hook 会自动检查并拦截危险操作。

## 拦截规则

| 模式 | 拦截原因 |
|------|---------|
| `rm -rf` | 递归强制删除（白名单路径除外） |
| `DROP TABLE` | 删除数据库表 |
| `git push --force` | 强制推送 |
| `TRUNCATE` | 清空数据库表 |
| `DELETE FROM` (无 WHERE) | 全表删除 |

## 安全白名单

以下 `rm -rf` 路径**不会**被拦截：
- `/tmp/` 下的文件
- `.git/` 对象
- `node_modules`
- `__pycache__`
- `*-env` 虚拟环境
- `dist/`, `build/`, `.next/`

## 日志

所有被拦截的命令记录在 `~/.claude/hooks/blocked.log`：

```
[2026-07-01T15:40:00+00:00] BLOCKED: DROP TABLE: 删除数据库表
  command: DROP TABLE users
  project: /Users/neo/my-project
------------------------------------------------------------
```

## 测试

```bash
python3 hooks/test_pre_tool_use.py
```

## 禁用

暂时移走文件即可：

```bash
mv ~/.claude/hooks/pre-tool-use.py ~/.claude/hooks/pre-tool-use.py.disabled
```

## 工作原理

Claude Code 的 `pre-tool-use` hook 机制：每次调用 tool 前，Claude 会执行这个脚本。
脚本读取 stdin 的 JSON（包含待执行命令），检查是否匹配危险模式。
- 退出码 0 → 放行
- 退出码 1 → 拒绝，stdout 输出原因给 Claude
