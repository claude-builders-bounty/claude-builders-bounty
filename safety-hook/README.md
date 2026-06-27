# Safety Hook for Claude Code

拦截危险 bash 命令，防止意外数据丢失。

## 2 步安装

```bash
# 1. 复制 hook
cp safety-hook.sh ~/.claude/hooks/pre-tool-use.sh

# 2. 添加执行权限
chmod +x ~/.claude/hooks/pre-tool-use.sh
```

完成。Claude Code 执行 bash 命令时会自动检查。

## 拦截的命令

| 模式 | 风险 |
|------|------|
| `rm -rf /` | 递归删除根目录 |
| `DROP TABLE` | 删除数据库表 |
| `git push --force` | 覆盖远程历史 |
| `TRUNCATE TABLE` | 清空表数据 |
| `DELETE FROM` 无 `WHERE` | 删除全表数据 |
| `rm -rf .` | 递归删除当前目录 |
| `mkfs` | 格式化磁盘 |
| `dd of=/dev/` | 直接写入磁盘 |
| Fork bomb | 耗尽系统进程 |

## 工作原理

1. Claude Code 执行 bash 前调用 hook
2. Hook 检查命令是否匹配危险模式
3. 匹配则：记录日志 + 阻止执行 + 告知 Claude 原因
4. 不匹配则：正常放行

## 日志

被阻止的命令记录在 `~/.claude/hooks/blocked.log`：

```
[2026-06-27T12:00:00Z] BLOCKED | /path/to/project | rm -rf /tmp/test | rm -rf / — 递归删除根目录
```

## 卸载

```bash
rm ~/.claude/hooks/pre-tool-use.sh
```
