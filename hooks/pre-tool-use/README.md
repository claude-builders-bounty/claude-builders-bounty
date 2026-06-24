# 🛡️ Pre-Tool-Use Hook: 阻止危险 bash 命令

Claude Code hook。在你执行危险命令之前拦截它。

## 安装

两步：

```bash
mkdir -p ~/.claude/hooks
ln -sf "$(pwd)/hook.py" ~/.claude/hooks/pre-tool-use
```

搞定。Claude Code 下次启动时自动加载这个 hook。

## 它拦截什么

| 类别 | 示例 | 严重级别 |
|------|------|---------|
| 🗑️ 毁灭性删除 | `rm -rf /`, `rm -rf /var` | CRITICAL |
| 🗄️ 数据库破坏 | `DROP TABLE`, `TRUNCATE`, `DELETE FROM` 无 WHERE | CRITICAL / HIGH |
| 🔄 Git 破坏 | `git push --force`, `git reset --hard` | CRITICAL / HIGH |
| ⚡ 危险 shell | `eval "$(curl ...)"`, `exec` | HIGH |
| 🔒 权限作弊 | `sudo rm -rf`, `chmod -R 777` | CRITICAL / HIGH |
| 🌐 远程脚本执行 | `curl ... | bash`, `wget ... | sh` | HIGH |
| 💾 系统路径写入 | `>/etc/passwd`, `dd of=/dev/sda` | CRITICAL |

没问题的不拦：`rm file.txt`、`git push origin main`、`delete from where` 都正常。

## 日志

所有被拦截的操作都记录在：

```
~/.claude/hooks/blocked.log
```

格式是 JSONL，每条包含时间戳、严重级别、原因、完整命令和项目路径。

## 测试

```bash
pip install pytest   # 只需一次
pytest               # 在 hooks/pre-tool-use/ 目录下跑
```

## 卸载

```bash
rm ~/.claude/hooks/pre-tool-use
```
