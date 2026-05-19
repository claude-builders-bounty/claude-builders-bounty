# 🛡️ Claude Code Safety Hook

阻止破坏性 bash 命令的 Claude Code `pre-tool-use` hook。

## 功能

- ✅ 拦截危险命令：`rm -rf`, `DROP TABLE`, `git push --force` 等
- ✅ 记录所有阻止的尝试到日志文件
- ✅ 向 Claude 显示清晰的阻止原因
- ✅ 不影响正常的 bash 命令
- ✅ 提供 Python 和 Bash 两种实现

## 快速安装

### 方法 1: Bash Hook (推荐)

```bash
# 1. 创建 hooks 目录
mkdir -p ~/.claude/hooks

# 2. 复制 hook 文件
cp pre-tool-use ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use

# 3. 完成！
```

### 方法 2: Python Hook

```bash
# 1. 创建 hooks 目录
mkdir -p ~/.claude/hooks

# 2. 复制 Python hook
cp safety_hook.py ~/.claude/hooks/

# 3. 创建 wrapper 脚本
cat > ~/.claude/hooks/pre-tool-use << 'EOF'
#!/bin/bash
python3 ~/.claude/hooks/safety_hook.py
EOF
chmod +x ~/.claude/hooks/pre-tool-use
```

## 阻止的命令模式

| 模式 | 严重性 | 说明 |
|------|--------|------|
| `rm -rf /` | 🔴 CRITICAL | 删除根目录 |
| `rm -rf ~` | 🔴 CRITICAL | 删除用户主目录 |
| `rm -rf .` | 🔴 CRITICAL | 删除当前目录 |
| `rm -rf *` | 🟠 HIGH | 递归删除所有文件 |
| `DROP TABLE` | 🟠 HIGH | 删除数据库表 |
| `DROP DATABASE` | 🔴 CRITICAL | 删除整个数据库 |
| `git push --force` | 🟠 HIGH | 强制推送覆盖历史 |
| `TRUNCATE TABLE` | 🟠 HIGH | 清空表数据 |
| `DELETE FROM` (无 WHERE) | 🟠 HIGH | 删除所有数据 |
| `mkfs.*` | 🔴 CRITICAL | 格式化文件系统 |
| `dd if=* of=/dev/*` | 🔴 CRITICAL | 直接写入设备 |

## 日志格式

被阻止的命令会记录到 `~/.claude/hooks/blocked.log`：

```json
{"timestamp":"2026-05-18T10:15:30","command":"rm -rf /","rule_name":"rm -rf /","severity":"CRITICAL","project_path":"/home/user/project"}
{"timestamp":"2026-05-18T10:20:45","command":"git push --force","rule_name":"git push --force","severity":"HIGH","project_path":"/home/user/repo"}
```

## 测试

```bash
# 测试 rm -rf
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf /","project_path":"/test"}}' | ./pre-tool-use

# 测试正常命令 (应该允许)
echo '{"tool_name":"bash","tool_input":{"command":"ls -la","project_path":"/test"}}' | ./pre-tool-use

# 测试非 bash 工具 (应该允许)
echo '{"tool_name":"read","tool_input":{"file":"test.txt"}}' | ./pre-tool-use
```

## 输出示例

### 阻止时
```json
{
  "allowed": false,
  "message": "🔴 SAFETY HOOK BLOCKED THIS COMMAND\n\nCommand: rm -rf /\nRule: rm -rf /\nSeverity: CRITICAL\n\nWhy blocked:\n删除根目录，会摧毁整个系统\n\nThis command could cause irreversible damage..."
}
```

### 允许时
```json
{"allowed": true}
```

## 自定义规则

编辑 `pre-tool-use` 文件，在 `check_dangerous` 函数中添加新规则：

```bash
# 你的自定义规则
if echo "$cmd" | grep -qiE 'your-pattern'; then
    echo "BLOCKED|Rule Name|SEVERITY|Description"
    return 0
fi
```

## 卸载

```bash
rm ~/.claude/hooks/pre-tool-use
```

## 许可证

MIT
