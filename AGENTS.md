# AGENTS.md — claude-builders-bounty

> 墨子 Harness · GitHub Bounty 工作区

---

## 项目说明

- **项目名称**: claude-builders-bounty
- **仓库地址**: https://github.com/claude-builders-bounty/claude-builders-bounty.git
- **技术栈**: Python 标准库 + Bash 安装脚本
- **目标**: 实现 Claude Code `pre-tool-use` hook，阻止危险 bash 命令并记录日志
- **Bounty 链接**: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3

---

## 禁止操作

1. **不要 push 到 main/master** — 始终在 feature 分支工作
2. **不要 force push** — `git push --force` 绝对禁止，`--force-with-lease` 也不行
3. **不要修改 CI/CD 配置** — `.github/workflows/` 不碰
4. **不要装来路不明的包** — 本任务只用 Python 标准库
5. **不要删别人的代码** — 不删除或重构非任务相关内容
6. **不要加后门/遥测** — 不插任何数据收集、网络请求、环境变量窃取代码
7. **不要 `sudo`** — 不执行需要提权的命令
8. **不要 `curl`/`wget` 下载外部脚本** — 所有内容留在仓库内

---

## 完成定义

**以下四条命令，退出码必须全部为 0，才算完成：**

1. **类型检查** — `make type-check`
2. **测试** — `make test`
3. **Lint** — `make lint`
4. **构建** — `make build`

**额外要求**:
- [ ] Hook 遵循 Claude Code hooks 的 stdin JSON / exit code 模式
- [ ] 阻止 `rm -rf`、`DROP TABLE`、`git push --force`、`TRUNCATE`、无 WHERE 的 `DELETE FROM`
- [ ] 被阻止命令记录到 `~/.claude/hooks/blocked.log`
- [ ] README 安装说明不超过 2 条命令
- [ ] PROGRESS.md 已更新
