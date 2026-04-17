# PR Reviewer Agent

This directory contains the Claude Code PR Reviewer Agent.

## Files

- `claude-review.py` - Main CLI script
- `.github/workflows/pr-review.yml` - GitHub Action
- `README.md` - Documentation

## Usage

```bash
python claude-review.py --pr https://github.com/owner/repo/pull/123 --token TOKEN
```

## Requirements

- Python 3.7+
- GITHUB_TOKEN environment variable or --token argument
- Optional: ANTHROPIC_API_KEY for AI-powered analysis