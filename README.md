# changelog.sh - Git 提交记录生成 CHANGELOG

从 git 历史自动生成结构化的 `CHANGELOG.md`，按 conventional commit 前缀自动分类。

## 安装与使用

**只需 2 步：**

```bash
# 1. 克隆仓库（或直接下载 changelog.sh）
chmod +x changelog.sh

# 2. 在任意 git 仓库中运行
bash changelog.sh
```

## 示例

```bash
# 基础用法：生成 CHANGELOG.md
bash changelog.sh

# 指定输出文件
bash changelog.sh -o docs/CHANGELOG.md

# 查看帮助
bash changelog.sh -h
```

## 输出样例

```markdown
# Changelog

## [Unreleased] - 2026-05-17

### Added

- fd9995c: feat: add another feature
- b5543d4: feat: add new feature for processing

### Fixed

- 288b174: fix: fix the bug in processing

### Changed

- 942274e: change: update the processing algorithm

### Removed

- 1a5ac7b: remove: remove feature.txt as it is obsolete
```

## 分类规则

| 提交前缀 | 分类 |
|----------|------|
| `feat:` / `add:` / `new:` | Added |
| `fix:` / `bug:` / `patch:` | Fixed |
| `remove:` / `delete:` | Removed |
| 其他 | Changed |
