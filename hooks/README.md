# 🛡️ Claude Code 安全 Hook

在 Claude Code 执行破坏性 bash 命令前拦截并阻止。

## 安装（2 条命令）

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## 拦截的命令

| 命令 | 风险 |
|------|------|
| `rm -rf` | 递归强制删除，不可恢复 |
| `DROP TABLE` | 永久删除表和数据 |
| `TRUNCATE` | 清空表中所有行 |
| `DELETE FROM x;` (无 WHERE) | 删除所有行 |
| `git push --force` | 覆盖远程历史 |
| `git reset --hard` | 丢弃未提交修改 |
| `chmod 777` | 过度权限 |
| `dd of=/dev/sd*` | 覆盖磁盘 |
| 疑似 fork bomb `:(){` | 系统资源耗尽 |

## 日志

所有阻止记录写入 `~/.claude/hooks/blocked.log`，格式：

```
[2026-06-06T08:30:00Z] BLOCKED
  Command: rm -rf /important-data
  Reason:  rm -rf 会递归强制删除文件，不可恢复
  Project: /home/user/my-project
---
```

## 测试

```bash
# 测试 rm -rf 拦截（预期输出包含 "decision": "block"）
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"}}' | python3 hooks/pre-tool-use

# 测试正常命令放行（预期输出 "decision": "allow"）
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 hooks/pre-tool-use

# 测试非 Bash 工具放行
echo '{"tool_name":"Read","tool_input":{"file_path":"/tmp/test"}}' | python3 hooks/pre-tool-use
```

## 允许危险操作

如果真的需要执行被阻止的命令，先确认有备份，然后用 `--` 前缀（脚本会识别并放行）：

```bash
# 不推荐，但如果确实需要：
# 1. 先备份
# 2. 手动在终端执行（不走 Claude Code）
```
