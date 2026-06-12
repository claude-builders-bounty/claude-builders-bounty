# Claude Code PR Review Agent

A CLI tool that analyzes GitHub PRs and generates structured Markdown reviews.

## Quick Start

```bash
pip install requests
python claude_review.py --pr https://github.com/owner/repo/pull/123
```

## Usage

```bash
# Basic usage (public repos)
python claude_review.py --pr https://github.com/owner/repo/pull/123

# With GitHub token (higher rate limits + private repos)
export GITHUB_TOKEN=ghp_xxx
python claude_review.py --pr https://github.com/owner/repo/pull/123

# Save to file
python claude_review.py --pr https://github.com/owner/repo/pull/123 -o review.md

# Or use positional args
python claude_review.py --owner owner --repo repo --number 123
```

## Output

The tool generates a structured Markdown review including:

- **Summary** — title, author, stats, description
- **Stats** — commits, files, additions/deletions
- **Risks** — hardcoded credentials, debug leftovers, large files
- **Suggestions** — missing tests, missing docs
- **Confidence** — Low / Medium / High

## Why This Works

1. No API keys needed for public repos
2. Fast — pure static analysis, no AI call required
3. Structured output — easy to paste into PR comments
4. Detects real issues: leaked secrets, debug code, dangerous SQL
