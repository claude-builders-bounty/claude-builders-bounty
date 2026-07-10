# Changelog Generator (git history -> structured CHANGELOG)

> Bounty: [BOUNTY $50] SKILL: Generate a structured CHANGELOG from git history

## 用法
```bash
python3 changelog.py --since v1.0.0
```
输出 `CHANGELOG.md`，按 type(feat/fix/docs) 分组，取自 conventional commits。

## 实现要点
## 💰 Bounty: $50 — powered by [Opire](https://opire.dev)

## Description
Create a Claude Code skill (`SKILL.md`) or a bash script that automatically generates
a structured `CHANGELOG.md` from a project's git history.

## Acceptance Criteria
- [ ] Works via `/generate-changelog` command or `bash changelog.sh`
- [ ] Fetches commits since the last git tag
- [ ] Auto-categorizes into: `Added` / `Fixed
- 解析 `git log --pretty=format:%s` 按前缀分类
- 输出 Keep-a-Changelog 格式
