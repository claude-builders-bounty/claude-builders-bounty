# Changelog Generator (git history -> structured CHANGELOG)

> Bounty: [BOUNTY $150] AGENT: Claude Code sub-agent that reviews a PR and posts a structured comment

## 用法
```bash
python3 changelog.py --since v1.0.0
```
输出 `CHANGELOG.md`，按 type(feat/fix/docs) 分组，取自 conventional commits。

## 实现要点
## 💰 Bounty: $150 — powered by [Opire](https://opire.dev)

## Description
Create a Claude Code agent that takes a PR diff as input, analyzes it,
and returns a structured Markdown review comment.

## Acceptance Criteria
- [ ] Works via CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- [ ] OR via GitHub Action (include the workflow YAML)
- [ ] Structured Markdown output with:
  - Su
- 解析 `git log --pretty=format:%s` 按前缀分类
- 输出 Keep-a-Changelog 格式
