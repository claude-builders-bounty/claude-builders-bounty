# AGENTS.md — claude-builders-bounty

> 墨子 Harness · 自动生成于 2026-06-24 · 已定制

---

## 项目说明

- **项目名称**: claude-builders-bounty
- **仓库地址**: https://github.com/claude-builders-bounty/claude-builders-bounty.git
- **技术栈**: Python (hook 脚本)
- **目标**: 实现 Issue #3 — Pre-tool-use hook 拦截危险 bash 命令
- **Bounty链接**: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3
- **赏金**: $100

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

1. **类型检查** — `echo 'OK (Python 项目，无类型检查)'`
2. **测试** — `python3 -m pytest hooks/pre-tool-use/ -q`
3. **Lint** — `python3 -m py_compile hooks/pre-tool-use/hook.py && echo 'OK'`
4. **构建** — `echo 'OK (无构建步骤)'`

**额外要求**:
- [x] 本地手动验证 hook 逻辑
- [x] PR 描述清晰：改了什么、为什么、怎么测的
- [x] README 安装说明 2 步以内
- [x] PROGRESS.md 已更新
