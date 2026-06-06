# SafeGuard Hook

Claude Code pre-tool-use hook，自动拦截危险bash命令。

## 安装

```bash
# 一键安装
mkdir -p ~/.claude/hooks/
curl -o ~/.claude/hooks/pre-tool-use https://raw.githubusercontent.com/curry202504/claude-builders-bounty/main/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## 拦截能力

| 模式 | 拦截 |
|------|------|
| `rm -rf /` | ✅ 阻止 |
| `git push --force` | ✅ 阻止 |
| `DROP TABLE/DATABASE` | ✅ 阻止 |
| `TRUNCATE TABLE` | ✅ 阻止 |
| `DELETE FROM` 无WHERE | ✅ 阻止 |
| `mkfs` / `dd if=` | ✅ 阻止 |
| `chmod 000` | ✅ 阻止 |
| `curl | sh` | ✅ 阻止 |

## 日志

所有被阻止的命令记录到: `~/.claude/hooks/blocked.log`

格式: `[时间戳] 已阻止 | 项目路径 | 原因 | 命令`
