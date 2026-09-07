# Claude Code PR Review Agent

A Claude Code sub-agent that takes a PR diff as input, analyzes it, and returns a structured Markdown review comment.

## Installation (2 commands)

```bash
# Add to PATH (symlink or alias)
ln -s $(pwd)/claude_review.py /usr/local/bin/claude-review
chmod +x claude_review.py
```

## Usage

```bash
# Markdown output (default)
claude-review --pr https://github.com/owner/repo/pull/123

# JSON output
claude-review --pr https://github.com/owner/repo/pull/123 --json
```

## Features

- Fetches PR diff via GitHub API (supports public and private repos via `GITHUB_TOKEN`)
- Detects destructive commands: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE
- Detects hardcoded secrets and unsafe patterns
- Outputs structured Markdown with Summary, Risks, Suggestions, and Confidence Score

## Tested On

- [PR #1](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1) - detected empty diff gracefully
- [PR #3955](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3955) - analyzed real code changes
- Multiple Open PRs on GitHub - verified pattern detection

## Sample Output

```
## Claude Code PR Review

**Repository:** owner/repo
**PR:** #123
**Title:** Add user authentication

### Summary of Changes
- Changes affect **3 file(s)**
- Net change: **+45 / -12 lines**

### Identified Risks
- No critical risks identified

### Improvement Suggestions
- Consider adding unit tests for modified logic

### Confidence Score: **High**
```

## Requirements

- Python 3.6+ (no external dependencies)
- `GITHUB_TOKEN` or `GH_TOKEN` env var for private repos
