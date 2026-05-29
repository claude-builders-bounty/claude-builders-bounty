# PR Reviewer Agent

Analyzes GitHub PR diffs and outputs structured Markdown reviews.

## Usage

```
/claude-review --pr https://github.com/owner/repo/pull/123
```

## What it does

1. Fetches the PR diff and metadata via `gh` CLI
2. Analyzes the diff for:
   - Change categories (Added / Modified / Removed / Renamed)
   - Security risks (hardcoded credentials, destructive commands)
   - Code quality issues (debug logs, swallowed errors)
   - PR size and complexity
3. Outputs a structured Markdown review with:
   - Summary of changes
   - Identified risks
   - Improvement suggestions
   - Confidence score (Low / Medium / High)

## Requirements

- `gh` CLI installed and authenticated (`gh auth login`)
- Python 3.8+

## Commands

| Command | Description |
|---------|-------------|
| `claude-review --pr <URL>` | Full Markdown review to stdout |
| `claude-review --pr <URL> -o review.md` | Save review to file |
| `claude-review --pr <URL> --json` | JSON output |
| `claude-review --pr <URL> --diff-only` | Raw diff only (for piping) |
