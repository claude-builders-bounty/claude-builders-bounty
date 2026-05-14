---
title: "generate-changelog"
summary: "从项目的 git 历史自动生成结构化的 CHANGELOG.md"
triggers:
  - "/generate-changelog"
---

# SKILL.md — generate-changelog

从 git 历史自动生成结构化的 `CHANGELOG.md` 文件。

## 触发方式

- 在 Claude Code 中输入 `/generate-changelog`
- 或直接运行 `python3 generate_changelog.py`

## 用法

```bash
# 从最新 tag 到 HEAD（推荐）
python3 generate_changelog.py

# 自定义范围
python3 generate_changelog.py v1.0..v2.0

# 全部提交
python3 generate_changelog.py --all
```

## 功能

- ✅ 自动检测最新的 git tag
- ✅ 支持自定义提交范围
- ✅ 自动分类到 Added / Fixed / Changed / Removed
- ✅ 支持约定式提交格式（`feat:`、`fix:`、`chore:` 等）
- ✅ 支持 emoji 前缀
- ✅ 输出格式标准的 `CHANGELOG.md`
- ✅ 包含提交统计和贡献者列表
- ✅ 自动提取提交前缀后的人类可读消息

## 安装

1. 将 `generate_changelog.py` 复制到项目根目录
2. （可选）将本文件复制到 `.claude/skills/` 目录
3. 运行 `python3 generate_changelog.py`

## 依赖

- Python 3.6+
- git
