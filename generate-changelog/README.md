# Generate CHANGELOG

自动从 git history 生成结构化 CHANGELOG.md 的工具。

## 设置说明（3 步）

### 1. 下载脚本

```bash
git clone <repo-url>
cd generate-changelog
```

### 2. 运行脚本

```bash
# 生成 CHANGELOG.md
bash scripts/generate-changelog.sh

# 或使用 --dry-run 预览
bash scripts/generate-changelog.sh --dry-run
```

### 3. 完成！

CHANGELOG.md 已生成在当前目录。

## 高级用法

```bash
# 指定输出文件
bash scripts/generate-changelog.sh --output CUSTOM.md

# 指定 tag 范围
bash scripts/generate-changelog.sh --from-tag v1.0.0 --to-tag v1.1.0
```

## Commit 规范

推荐使用 [Conventional Commits](https://www.conventionalcommits.org/)：

| 类型 | CHANGELOG 分类 |
|------|----------------|
| `feat:` | Added |
| `fix:` | Fixed |
| `perf:`, `refactor:`, `docs:`, `style:` | Changed |
| `revert:` | Removed |
| `test:`, `chore:` | Other |

## 示例输出

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [v1.0.0] - 2026-04-12

### Added
- New user authentication feature
- Support for dark mode

### Fixed
- Login button not responding on mobile
- Memory leak in data processor

### Changed
- Updated dependencies
- Improved documentation
```

## 依赖

- Git
- Bash 4.0+
