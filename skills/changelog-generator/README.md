# CHANGELOG Generator

一个简单易用的 CHANGELOG 生成工具，从 git 历史自动生成结构化的变更日志。

## 快速开始

### 安装

无需安装，直接运行 Python 脚本：

```bash
python changelog_generator.py
```

### 基本用法

```bash
# 在 git 仓库根目录运行
python changelog_generator.py

# 指定输出文件
python changelog_generator.py --output NEWS.md

# 从指定 tag 开始
python changelog_generator.py --from-tag v1.0.0

# 预览模式（不写文件）
python changelog_generator.py --dry-run
```

## 工作原理

1. 查找最新的 git tag 作为版本号
2. 获取从上一个 tag 到当前的所有 commits
3. 根据 Conventional Commits 规范分类
4. 生成格式化的 CHANGELOG.md

## 示例输出

```markdown
# Changelog

## [v1.2.0] - 2026-04-16

### Added
- Add user authentication feature ([a1b2c3d])
- Support dark mode ([d4e5f6g])

### Fixed
- Fix memory leak in parser ([g7h8i9j])

### Changed
- Refactor database connection pool ([k1l2m3n])

### Removed
- Remove deprecated API endpoints ([o4p5q6r])

[v1.2.0]: https://github.com/compare/v1.1.0...v1.2.0
```

## Commit 规范

推荐使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
type(scope): description
```

### 支持的类型

| 类型 | 分类 | 示例 |
|------|------|------|
| `feat` | Added | `feat(auth): add login page` |
| `fix` | Fixed | `fix(api): handle null response` |
| `refactor` | Changed | `refactor(core): simplify logic` |
| `perf` | Changed | `perf(query): optimize join` |
| `remove` | Removed | `remove(deps): delete unused package` |

### 跳过的类型

以下类型的 commits 默认不会出现在 CHANGELOG 中：

- `docs` - 文档变更
- `test` - 测试相关
- `chore` - 构建/工具相关
- `ci` - CI 配置
- `build` - 构建系统

使用 `--all` 参数可以包含这些 commits。

## 参数说明

| 参数 | 简写 | 说明 |
|------|------|------|
| `--output` | `-o` | 输出文件路径 (默认: CHANGELOG.md) |
| `--from-tag` | | 起始 tag |
| `--version` | | 指定版本号 (默认: 最新 tag 或 Unreleased) |
| `--dry-run` | | 预览模式，不写文件 |
| `--all` | | 包含所有类型的 commits |

## 依赖

- Python 3.6+
- Git

## 许可证

MIT License
