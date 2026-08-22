# Claude Code PR Reviewer Sub-Agent & Action

Automated sub-agent that analyzes Pull Request diffs and posts structured, actionable Markdown reviews.

## CLI Usage

```bash
# 1. Direct console output
python3 claude_review/cli.py --pr https://github.com/owner/repo/pull/123

# 2. Output to file
python3 claude_review/cli.py --pr https://github.com/owner/repo/pull/123 --output review.md

# 3. Automatically post comment to PR (requires gh CLI authenticated)
python3 claude_review/cli.py --pr https://github.com/owner/repo/pull/123 --post-comment
```

## GitHub Action Integration

Drop `.github/workflows/claude-pr-review.yml` into any repository for zero-config automated reviews on all new Pull Requests.
