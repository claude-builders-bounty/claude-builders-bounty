# CHANGELOG Generator Skill

自动生成结构化的 CHANGELOG.md 从 git 历史。

## 安装

```bash
# 技能已位于
~/.hermes/skills/productivity/github-changelog-generator/

# 使用方法 1: Bash 脚本
cd /path/to/your/repo
bash ~/.hermes/skills/productivity/github-changelog-generator/changelog.sh

# 使用方法 2: Python 版本（支持 tag 分组）
cd /path/to/your/repo
python3 ~/.hermes/skills/productivity/github-changelog-generator/changelog.py

# 使用方法 3: Claude Code Skill
/generate-changelog
```

## 功能

- ✅ 自动分类 commits（Added/Fixed/Changed/Removed/Other）
- ✅ 支持 Conventional Commits 规范
- ✅ 按 git tags 分组版本（如果有）
- ✅ 生成标准 markdown 格式
- ✅ 可配置最大 commit 数量

## Commit 分类规则

| 前缀 | 分类 |
|------|------|
| `feat:`, `add:` | Added |
| `fix:`, `bugfix:` | Fixed |
| `refactor:`, `update:`, `docs:`, `chore:` | Changed |
| `remove:`, `drop:`, `deprecate:` | Removed |

## 输出示例

```markdown
# Changelog

## [Unreleased]

### Added
- feat: Add user authentication system (abc123)
- feat: Implement dark mode toggle (def456)

### Fixed
- fix: Resolve memory leak in data processing (ghi789)

### Changed
- refactor: Improve error handling in API layer (jkl012)

### Removed
- remove: Deprecate legacy auth endpoints (mno345)
```

## 测试

```bash
cd /path/to/git/repo
bash changelog.sh test-output.md 50
cat test-output.md
```

## 文件说明

- `SKILL.md` - 完整技能文档
- `changelog.sh` - Bash 脚本版本（基础功能）
- `changelog.py` - Python 版本（支持 tag 分组，高级功能）
- `README.md` - 本文件（快速开始指南）

## Bounty

- **Issue:** [#1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)
- **Amount:** $50 USD
- **Platform:** Opire
- **Status:** ✅ Claimed

## License

MIT
