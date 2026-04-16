# CHANGELOG Generator Skill

自动从 git 历史生成结构化 CHANGELOG.md 的 Claude Code Skill。

## 功能特性

- 从上一个 git tag 开始获取所有 commits
- 自动分类为: Added / Fixed / Changed / Removed
- 输出格式化的 CHANGELOG.md
- 支持 Conventional Commits 规范

## 使用方法

### 方式 1: 作为 Claude Code Skill

将此目录复制到你的 Claude Code skills 目录，然后在 Claude Code 中:

```
/generate-changelog
```

### 方式 2: 直接运行脚本

```bash
python changelog_generator.py [--output CHANGELOG.md] [--from-tag TAG]
```

## 参数

- `--output`: 输出文件路径 (默认: CHANGELOG.md)
- `--from-tag`: 起始 tag (默认: 上一个 tag)
- `--dry-run`: 仅打印，不写文件

## 分类规则

基于 Conventional Commits:

| 前缀 | 分类 |
|------|------|
| feat | Added |
| fix | Fixed |
| refactor, perf, style | Changed |
| remove, delete | Removed |
| docs, test, chore | (跳过) |

## 依赖

- Python 3.6+
- Git
