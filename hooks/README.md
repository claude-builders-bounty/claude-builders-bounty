# Claude Code Pre-Tool-Use Hook

拦截 Claude Code 中的危险 bash 命令，防止误操作导致数据丢失。

## 安装

```bash
# 1. 复制 hook 到 Claude hooks 目录
mkdir -p ~/.claude/hooks && cp hook.py ~/.claude/hooks/

# 2. 添加到 Claude Code 配置（运行一次）
claude config set hooks.pre_tool_use ~/.claude/hooks/hook.py
```

## 拦截的命令

| 命令 | 风险 |
|------|------|
| `rm -rf` / `rm -fr` | 递归强制删除，不可恢复 |
| `DROP TABLE` | 删除整张表，数据丢失 |
| `TRUNCATE` | 清空表数据，不可恢复 |
| `DELETE FROM` (无 WHERE) | 可能删除全表数据 |
| `git push --force` | 覆盖远程提交历史 |

## 日志位置

被拦截的命令记录在 `~/.claude/hooks/blocked.log`

```
2026-07-24 10:30:45 | rm -rf /important/dir | /path/to/project | rm -rf: 递归强制删除，不可恢复
```

## 自定义

编辑 `hook.py` 中的 `DANGEROUS_PATTERNS` 列表添加更多规则。
