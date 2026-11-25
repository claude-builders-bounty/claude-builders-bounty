# Git History CHANGELOG Generator

从 git history 自动生成结构化 `CHANGELOG.md`（Added / Fixed / Changed / Removed）。

## 快速开始（3 步）

1. **放置脚本**：将 `tools/changelog/changelog.sh` 复制到你的项目仓库根目录。
2. **执行**：在仓库根目录运行 `bash changelog.sh`，或在 Claude Code 中运行 `/generate-changelog`。
3. **查看结果**：生成的 `CHANGELOG.md` 位于仓库根目录，按提交归类列出所有自上次 tag 以来的变更。

## 工作原理

- 读取 `git log --format='%h|%s'`（只读，不修改仓库）。
- 若存在 git tag，只抓取自上一个 tag 以来的提交；无 tag 时从首个提交开始。
- 按提交主题归类为 `Added` / `Fixed` / `Changed` / `Removed`（常规提交格式：feat/add → Added，fix → Fixed，remove/delete → Removed，其余 → Changed）。
- 输出规范格式的 `CHANGELOG.md`（`# Changelog` / `## [Unreleased]` / 各类条目）。

## 接受标准（claude-builders-bounty/claude-builders-bounty#1）

- [x] 通过 `/generate-changelog` 命令或 `bash changelog.sh` 运行
- [x] 抓取自上一个 git tag 以来的提交
- [x] 自动归类为 Added / Fixed / Changed / Removed
- [x] 输出规范格式的 `CHANGELOG.md`
- [x] 在真实 GitHub 仓库上测试（见下方样例输出）
- [x] README 设置 3 步或更少

## 样例输出（本仓库 `bounty-hunter` 生成）

```markdown
# Changelog


## [Unreleased]


### Added

- 5f5ec6f — feat: add github_bounties_public zero-credential adapter and 5 task deliverables

### Fixed

### Changed

- 452b050 — chore: add 99_xiazaiqu download folder (gitignored)
- a68427a — chore: init gongzuoqu workspace with 6-folder structure and .gitignore

### Removed

---
*由 `changelog.sh` 从 git history 自动生成。*
```

## 注意

- 脚本仅读取 git 历史，不修改任何仓库文件，仅在指定路径写入新的 `CHANGELOG.md`。
- 如需自定义分类规则，编辑 `changelog.sh` 中的 `classify()` 函数。
