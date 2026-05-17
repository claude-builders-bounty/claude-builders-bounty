# claude-review - PR Review Sub-Agent

Structured PR review agent for Claude.

## Setup
```bash
chmod +x claude-review
# Optional: sudo cp claude-review /usr/local/bin/
```

## Usage
- By URL: `claude-review --pr https://github.com/owner/repo/pull/123`
- By number: `claude-review --pr 123 --repo owner/repo`
- Local diff: `claude-review --diff-file changes.diff`
- Save: `claude-review --pr 123 --repo o/r -o review.md`

## Requirements
Python 3.8+, curl, GitHub token (optional, for private repos)
