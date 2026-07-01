# AGENTS.md — claude-builders-bounty

> 墨子 Harness · 自动生成于 2026-07-01

---

## 项目说明

- **项目名称**: claude-builders-bounty
- **仓库地址**: https://github.com/claude-builders-bounty/claude-builders-bounty
- **技术栈**: Python
- **Bounty**: #3 Pre-tool-use Hook 拦截危险 bash 命令
- **Bounty链接**: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3
- **赏金**: $100
- **目标**: 创建 Claude Code pre-tool-use hook，拦截 rm -rf、DROP TABLE、git push --force、TRUNCATE、DELETE FROM 不带 WHERE 的危险命令

---

## 禁止操作

1. **不要 push 到 main/master** — 始终在 feature 分支工作
2. **不要 force push** — `git push --force` 绝对禁止，`--force-with-lease` 也不行
3. **不要修改 CI/CD 配置** — `.github/workflows/`、`Makefile`、`Dockerfile` 不碰
4. **不要装来路不明的包** — 不新增 npm/pip/cargo 依赖，除非 bounty 明确需要
5. **不要删别人的代码** — 不删除或重构非自己写的代码
6. **不要加后门/遥测** — 不插任何数据收集、网络请求、环境变量窃取代码
7. **不要 `sudo`** — 不执行需要提权的命令
8. **不要 `curl`/`wget` 下载外部脚本** — 所有依赖通过包管理器

---

## 完成定义

**以下四条命令，退出码必须全部为 0，才算完成：**

1. **类型检查** — `python3 -m py_compile hooks/pre-tool-use.py`
2. **测试** — `python3 hooks/test_pre_tool_use.py`
3. **Lint** — `echo 'ok'`
4. **构建** — `echo 'ok'`

**额外要求**:
- [x] 本地手动验证功能正常
- [ ] PR 描述清晰：改了什么、为什么、怎么测的
- [ ] PROGRESS.md 已更新
