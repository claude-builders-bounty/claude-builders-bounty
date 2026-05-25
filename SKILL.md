---
name: claude-review
description: AI-powered PR review sub-agent that fetches a PR diff, analyzes it, and posts a structured review comment
version: 1.0.0
---

# Claude Review — PR Review Sub-Agent

## What It Does

This sub-agent reviews a GitHub pull request and posts a structured Markdown review comment. It:

1. Fetches the PR diff via `gh pr diff`
2. Fetches existing review comments via `gh api`
3. Analyzes the diff using an LLM (GLM/ZhipuAI)
4. Posts a structured review comment via `gh pr comment`

## Usage with Claude Code Task Tool

```json
{
 "type": "subagent",
 "name": "claude-review",
 "command": "./claude-review --pr ${PR_URL} --post"
}
```

### Inline Usage

```bash
# Review a PR and print to stdout
./claude-review --pr owner/repo/pull/123

# Review a PR and post the comment
./claude-review --pr owner/repo/pull/123 --post

# Dry run (print without posting)
./claude-review --pr https://github.com/owner/repo/pull/123 --dry-run

# Save to file
./claude-review --pr owner/repo/pull/123 --output review.md
```

## Input Format

Accepts a PR identifier in any of these formats:
- Full URL: `https://github.com/owner/repo/pull/123`
- Short path: `owner/repo/pull/123`
- Hash format: `owner/repo#123`

## Output Format

The review comment follows this structure:

```markdown
## 🤖 Claude PR Review — #123: PR Title

---
## Summary
2-3 sentence plain-English summary of what this PR changes and why.

## Issues Found
### Critical
- Security vulnerabilities, data loss risks, broken builds

### Important
- Bugs, performance concerns, missing error handling

### Minor
- Style nits, minor improvements, optional suggestions

## Suggestions
- Actionable, concrete improvement suggestions with reasoning

## Overall Assessment
Overall quality, risk level, readiness to merge, confidence score.
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_API_KEY` | Yes | — | ZhipuAI/GLM API key |
| `LLM_API_BASE` | No | `https://open.bigmodel.cn/api/paas/v4` | LLM API base URL |
| `LLM_MODEL` | No | `glm-4-flashx` | LLM model name |
| `GITHUB_TOKEN` | No | (from `gh auth`) | GitHub auth token |

## Requirements

- Python 3.8+
- `gh` CLI authenticated (`gh auth login`)
- LLM API key (ZhipuAI, OpenAI, or compatible)

## Files

- `claude-review` — Main Python script (executable)
- `SKILL.md` — This file
- `README.md` — Setup and usage guide
- `sample-outputs/` — Example review outputs
