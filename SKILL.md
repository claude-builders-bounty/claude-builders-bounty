---
name: claude-pr-reviewer
description: "AI-powered PR review using Claude. CLI + GitHub Action."
tags: [code-review, pr, claude, github-action]
---

# Claude PR Reviewer

AI-powered PR review tool using Claude. Works as CLI and GitHub Action.

## CLI Usage

```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/123
```

## GitHub Action

Auto-reviews PRs and posts structured comments:
- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score

## Features

- Zero dependencies (stdlib only)
- Focus areas (--focus security,performance)
- JSON output (--format json)
- Smart diff truncation
- Comment dedup (updates existing, no spam)
