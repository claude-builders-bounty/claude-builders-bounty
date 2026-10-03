# Claude Code PR Reviewer Agent

A lightweight, automated sub-agent and GitHub Action that evaluates pull request diffs, performs static risk analysis, and publishes a structured Markdown review comment.

## CLI Usage
```bash
./bin/claude-review --pr https://github.com/owner/repo/pull/123
```

## Features
- Structured summary (insertions/deletions + context)
- Risk and regression detection
- Actionable improvement suggestions
- Output confidence level (Low / Medium / High)
