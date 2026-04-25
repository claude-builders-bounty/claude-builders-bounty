# CHANGELOG Generator

从 git history 自动生成结构化的 CHANGELOG.md，支持 conventional commits 分类。

## 功能

- ✅ 自动获取最新 tag 之后的 commits
- ✅ 按 `Added` / `Fixed` / `Changed` / `Removed` 自动分类
- ✅ 支持 conventional commit 格式解析
- ✅ 生成标准格式的 CHANGELOG.md
- ✅ 支持自定义版本号和输出文件

## 安装

```bash
# 克隆仓库
git clone <repo-url>
cd changelog-generator

# 确保有 Python 3.6+ 和 git
python --version
git --version
```

## 使用

### 基本用法

```bash
# 从最新 tag 生成 CHANGELOG
python changelog.py

# 指定版本号
python changelog.py -v 1.2.0

# 输出到指定文件
python changelog.py -o RELEASE_NOTES.md
```

### 高级用法

```bash
# 从指定 tag 生成
python changelog.py --since v1.0.0

# 包含所有 commits
python changelog.py --all

# 添加仓库链接 (生成可点击的 commit 链接)
python changelog.py --repo-url https://github.com/user/repo
```

## 分类规则

根据 commit message 自动分类：

| 类别 | 匹配规则 |
|------|---------|
| **Added** | `feat:`, `add`, `implement`, `introduce`, `new` |
| **Fixed** | `fix:`, `bugfix`, `hotfix`, `patch`, `resolve`, `correct` |
| **Changed** | `refactor:`, `update`, `modify`, `change`, `improve`, `docs:`, `style:`, `chore:` |
| **Removed** | `remove`, `delete`, `drop`, `deprecate`, `clean`, `revert` |

## 示例输出

```markdown
# Changelog

## [Unreleased] - 2026-04-25

### Added
- 新增用户登录功能 (a1b2c3d)
- 支持深色模式 (e4f5g6h)

### Fixed
- 修复首页加载慢的问题 (i7j8k9l)

### Changed
- 优化数据库查询性能 (m0n1o2p)
```

## 要求

- Python 3.6+
- Git

## 许可证

MIT
