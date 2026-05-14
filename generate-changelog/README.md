# Generate Changelog

从 git 提交历史自动生成结构化 CHANGELOG.md 文件的 Claude Code 技能。

## 安装（3 步）

1. 将 `generate_changelog.py` 复制到项目根目录
2. 将 `SKILL.md` 复制到 `.claude/skills/` 目录（可选，用于 Claude Code 集成）
3. 运行 `python3 generate_changelog.py`

## 用法

```bash
# 从最新 tag 到 HEAD（推荐）
python3 generate_changelog.py

# 自定义提交范围
python3 generate_changelog.py v1.0..v2.0

# 全部提交
python3 generate_changelog.py --all
```

## 提交分类规则

| 分类 | 匹配前缀 |
|------|----------|
| 🚀 **Added** | `feat:`, `feature:`, `add:`, `new:`, `implement:`, `create:` |
| 🐛 **Fixed** | `fix:`, `bug:`, `hotfix:`, `patch:`, `correct:`, `resolve:` |
| 🔧 **Changed** | `refactor:`, `chore:`, `ci:`, `build:`, `perf:`, `style:`, `docs:`, `test:` |
| 🔥 **Removed** | `remove:`, `delete:`, `drop:`, `cleanup:`, `revert:`, `deprecate:` |

提交信息前缀可以是约定式提交格式（如 `feat(scope): message`、`fix: message`），也支持 emoji 前缀。

## 依赖

- Python 3.6+
- Git
