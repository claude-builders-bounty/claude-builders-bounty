# AGENTS.md — claude-builders-bounty

> 墨子 Harness · 2026-06-29

---

## 项目说明

- **项目名称**: claude-builders-bounty
- **仓库地址**: https://github.com/claude-builders-bounty/claude-builders-bounty
- **技术栈**: Node.js / TypeScript
- **目标**: 创建 Claude Code sub-agent，输入 PR diff，输出结构化 Markdown review 评论
- **Bounty链接**: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4

---

## 任务要求

创建 `claude-review` CLI 工具：
1. CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
2. 获取 PR diff → LLM 分析 → 输出结构化 review
3. 输出包含：Summary, Identified risks, Improvement suggestions, Confidence score
4. GitHub Action workflow 可选（额外加分）
5. README 安装和使用说明

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

1. **类型检查** — `npx tsc --noEmit`
2. **测试** — `npx vitest run`
3. **Lint** — `npx eslint src/`
4. **构建** — `npx tsc`

**额外要求**:
- [x] 本地手动验证功能正常
- [x] PR 描述清晰：改了什么、为什么、怎么测的
- [x] PROGRESS.md 已更新
