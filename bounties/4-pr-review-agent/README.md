# Claude PR Review Agent

**Bounty #4 - $150**

A CLI tool that reviews GitHub PRs and posts structured review comments with severity levels.

## Quick Start

```bash
# Requirements: Python 3.8+
export GITHUB_TOKEN=ghp_xxx

# Review any PR
python3 claude-review https://github.com/owner/repo/pull/42

# Post as comment
python3 claude-review https://github.com/owner/repo/pull/42 | gh pr comment 42 --body-file -
```

## Features

- ? PR description quality analysis
- ? Change summary (files/additions/deletions)
- ? Security scan: secrets, code execution, hardcoded values
- ? Code quality: TODO/FIXME markers, debug statements
- ? Test coverage detection
- ? Structured markdown report with severity status table
- ? Zero external dependencies (stdlib only)

## Files

| File | Description |
|------|-------------|
| `claude-review` | Main review script |
| `README.md` | This file |

## How It Works

1. Fetches PR metadata via GitHub API
2. Downloads the full diff
3. Analyzes for security issues, code quality, test coverage
4. Outputs a structured review report as markdown
5. Ready to pipe into `gh pr comment` for posting

## Requirements

- Python 3.8+
- GitHub token (classic, with `repo` scope)
- Network access to api.github.com
