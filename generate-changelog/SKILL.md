---
name: generate-changelog
description: 自动从 git history 生成结构化 CHANGELOG.md 的 Claude Code skill。根据 conventional commits 规范（feat/fix/docs/style/refactor/test/chore），自动分类 commits 到 Added/Fixed/Changed/Removed/Other 五个分类。支持 `/generate-changelog` 命令调用或直接运行 `bash changelog.sh`。当用户需要「生成更新日志」「从 git 历史创建 changelog」「自动生成版本更新说明」时使用。
---

# Generate CHANGELOG from Git History

## 任务目标

自动从 git history 生成结构化的 `CHANGELOG.md`，支持：
- 从最后一个 git tag 获取 commits
- 自动分类到 Added / Fixed / Changed / Removed / Other
- 输出标准格式的 CHANGELOG.md

## 使用方式

### 方式一：Claude Code 命令（推荐）

```
/generate-changelog
```

### 方式二：直接运行脚本

```bash
bash changelog.sh
# 或指定输出文件
bash changelog.sh --output CUSTOM_CHANGELOG.md
# 或指定起始 tag
bash changelog.sh --from-tag v1.0.0 --to-tag v1.1.0
```

## 核心功能

### 1. 自动检测最新 Tag

```bash
# 获取最新 tag 作为起始点
git describe --tags --abbrev=0
```

### 2. Conventional Commits 分类

| Commit 前缀 | CHANGELOG 分类 |
|-------------|----------------|
| `feat:` | **Added** |
| `fix:` | **Fixed** |
| `perf:` | **Changed** |
| `refactor:` | **Changed** |
| `docs:` | **Changed** |
| `style:` | **Changed** |
| `test:` | **Other** |
| `chore:` | **Other** |
| `revert:` | **Removed** |

### 3. 输出格式

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - YYYY-MM-DD

### Added
- New feature description

### Fixed
- Bug fix description

### Changed
- Enhancement description

### Removed
- Removed feature description

### Other
- Miscellaneous changes
```

## 依赖要求

- Git
- Bash 4.0+
- 标准 Unix 工具：`grep`, `sed`, `awk`, `date`

## 常见用法

### 基础用法

```bash
# 生成 changelog
bash generate-changelog.sh

# 指定输出文件
bash generate-changelog.sh --output CHANGELOG.md

# 指定 tag 范围
bash generate-changelog.sh --from-tag v1.0.0 --to-tag v1.1.0

# 仅显示不提交
bash generate-changelog.sh --dry-run
```

### 与 Git Tag 配合

```bash
# 创建新 tag 后生成 changelog
git tag -a v1.1.0 -m "Release version 1.1.0"
bash generate-changelog.sh
```

## 注意事项

1. **建议使用 conventional commits**：使用 `feat:`、`fix:` 等前缀可获得更准确的分类
2. **输出覆盖**：脚本默认覆盖已存在的 CHANGELOG.md，如需保留请先备份
3. **无 tag 时**：会从第一个 commit 开始生成
4. **空分类**：不包含任何 commit 的分类不会出现在输出中
