# CHANGELOG Generator

自动生成结构化 CHANGELOG.md 的 Bash 脚本。

## 功能

- ✅ 自动获取上次 tag 以来的所有提交
- ✅ 智能分类: Added / Fixed / Changed / Removed
- ✅ 输出标准格式的 CHANGELOG.md
- ✅ 遵循 [Keep a Changelog](https://keepachangelog.com/) 规范

## 快速开始

### 1. 下载脚本

```bash
curl -O https://raw.githubusercontent.com/your-repo/changelog.sh
chmod +x changelog.sh
```

### 2. 运行脚本

```bash
./changelog.sh
```

### 3. 查看结果

生成的 `CHANGELOG.md` 文件会在当前目录。

## 分类规则

| 类别 | 关键词 |
|------|--------|
| Added | add, feature, feat, new, implement, introduce |
| Fixed | fix, bug, repair, correct, resolve, patch |
| Changed | change, update, modify, refactor, improve, enhance, optimize |
| Removed | remove, delete, drop, clean, cleanup, deprecate |

## 示例输出

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-03-31

### Added
- Add new feature X (a1b2c3d)
- Implement API endpoint (e4f5g6h)

### Fixed
- Fix bug in login (i7j8k9l)

### Changed
- Refactor database layer (m0n1o2p)
```

## 帮助

```bash
./changelog.sh --help
```

## 要求

- Git 仓库
- Bash 4.0+

## License

MIT
