# claude-review — PR Reviewer Agent

A Claude Code sub-agent that analyzes GitHub PR diffs and outputs structured Markdown reviews.

## Setup (2 steps)

```bash
# 1. Make executable
chmod +x claude-review

# 2. Ensure gh CLI is authenticated
gh auth login
```

Requires Python 3.8+ and [`gh` CLI](https://cli.github.com/).

## Usage

```bash
# Full Markdown review
./claude-review --pr https://github.com/owner/repo/pull/123

# Save to file
./claude-review --pr https://github.com/owner/repo/pull/123 -o review.md

# JSON output
./claude-review --pr https://github.com/owner/repo/pull/123 --json

# Raw diff only (pipe into Claude)
./claude-review --pr https://github.com/owner/repo/pull/123 --diff-only
```

## As Claude Code Sub-Agent

Place `SKILL.md` and `claude-review` in your project, then invoke:

```
/claude-review --pr https://github.com/owner/repo/pull/123
```

## GitHub Action

Copy `.github/workflows/claude-review.yml` to your repo to auto-review PRs on open/update.

## Output Format

```markdown
# PR Review: <title>

**PR**: <url> | **Author**: <login> | **Stats**: +X / -Y | N files

## Summary of Changes
...

## Identified Risks
- ...

## Improvement Suggestions
- ...

## Confidence Score
**Low / Medium / High**
```
