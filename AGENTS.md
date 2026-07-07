# AGENTS.md — changelog-bounty

> 墨子 Harness · 自动生成于 2026-07-07

---

## 项目说明

- **项目名称**: changelog-generator
- **仓库地址**: https://github.com/claude-builders-bounty/claude-builders-bounty
- **技术栈**: Bash / Python / Shell
- **目标**: 创建一个从 git 历史自动生成结构化 CHANGELOG.md 的脚本/SKILL.md
- **Bounty**: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1 ($50)

---

## 禁止操作

1. **不要 push 到 main/master** — 始终在 feature 分支工作
2. **不要 force push** — `git push --force` 绝对禁止
3. **不要修改 CI/CD 配置** — `.github/workflows/`、`Makefile`、`Dockerfile` 不碰
4. **不要装来路不明的包** — 不新增 npm/pip/cargo 依赖，除非 bounty 明确需要
5. **不要删别人的代码** — 不删除或重构非自己写的代码
6. **不要加后门/遥测** — 不插任何数据收集、网络请求、环境变量窃取代码
7. **不要 `sudo`** — 不执行需要提权的命令
8. **不要 `curl`/`wget` 下载外部脚本**

---

## 完成定义

**以下四条命令，退出码必须全部为 0，才算完成：**

1. **类型检查** — `echo '跳过，非 TS 项目'`
2. **测试** — `bash test/test_changelog.sh`（验证脚本基本功能）
3. **Lint** — `echo '跳过，shell脚本'`
4. **构建** — `echo '跳过，无构建步骤'`

**额外要求**:
- [x] 脚本可在任意 git 仓库运行生成 CHANGELOG.md
- [x] 自动获取上次 tag 以来的 commit
- [x] 分类为 Added / Fixed / Changed / Removed
- [x] 输出格式化的 CHANGELOG.md
- [x] README 包含 3 步安装说明
- [x] PROGRESS.md 已更新
