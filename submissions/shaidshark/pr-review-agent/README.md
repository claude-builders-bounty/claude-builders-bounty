# PR Review Sub-Agent

Automated PR review tool that analyzes diffs and posts structured review comments on GitHub.

## Usage

```bash
# Review only (print to stdout)
python review.py https://github.com/owner/repo/pull/123

# Review and post comment
python review.py https://github.com/owner/repo/pull/123 --post

# With custom token
python review.py https://github.com/owner/repo/pull/123 --token ghp_xxx --post
```

## What It Checks

| Category | Examples |
|----------|---------|
| 🔒 Security | Hardcoded secrets, eval(), SQL injection, shell=True |
| 🐛 Bugs | Bare except, empty blocks |
| ⚡ Performance | Redis keys(), unbounded queries |
| 🎨 Style | Long lines, print() vs logging |
| ✅ Positive | Test coverage, proper logging |

## Requirements

- Python 3.10+
- `gh` CLI (authenticated)
