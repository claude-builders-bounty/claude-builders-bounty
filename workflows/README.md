# Weekly Dev Summary — n8n + Claude API

> **Bounty #5 ($200)** — Automated weekly GitHub activity summary

An n8n workflow that runs every Friday at 5pm, fetches the week's GitHub activity
(commits, closed issues, merged PRs), generates a narrative summary via Claude API,
and saves it as a Markdown file + posts as a GitHub Issue.

## Quick Install

```bash
# 1. Import into n8n
#    n8n → Settings → Import → select workflows/weekly-dev-summary.json

# 2. Set environment variables
export GITHUB_OWNER="your-org"
export GITHUB_REPO="your-repo"
export CLAUDE_API_KEY="sk-ant-..."

# 3. Configure credentials in n8n:
#    - GitHub API (personal access token with repo scope)
#    - HTTP Header Auth (for Claude API)
```

## Workflow Steps

| Step | Node | Purpose |
|---|---|---|
| 1 | Cron Trigger | Runs every Friday at 5pm |
| 2 | GitHub API ×3 | Fetches commits, closed issues, merged PRs |
| 3 | Code (Aggregate) | Structures raw GitHub data |
| 4 | Code (Prompt) | Builds Claude prompt from structured data |
| 5 | HTTP Request | Calls Claude Sonnet API |
| 6 | Code (Format) | Extracts response, formats Markdown |
| 7a | Write File | Saves summary as `.md` file |
| 7b | GitHub Issue | Posts summary as an issue |
| 7c | Log | Records completion |

## Sample Output

```markdown
# Weekly Dev Summary

**Repo:** acme/saas-app
**Period:** 2026-05-15 to 2026-05-21

## Overview
This week saw 23 commits across 5 merged PRs, focused primarily on...

## Highlights
- Payment integration with Stripe completed (#142)
- Authentication middleware refactored for performance (#138)

## Pull Requests
- #142 Stripe payment integration by @alice
- #138 Auth middleware perf improvements by @bob
- #135 Fix dashboard loading state by @carol
- #131 Update README with setup docs by @dave
- #128 Upgrade Next.js to 15.2 by @eve

## Issues Resolved
- #140: Bug: invoice PDF generation timeout
- #137: Feature: Add dark mode toggle

## What's Next
Based on activity patterns, expect focus on...
```

## Requirements

- n8n (self-hosted or cloud)
- GitHub personal access token (repo scope)
- Anthropic API key (Claude Sonnet)
