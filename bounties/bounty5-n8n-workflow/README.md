# 📊 n8n + Claude API — Weekly Dev Summary

> **Bounty #5** — Automated weekly narrative summaries of GitHub repo activity.

## Overview

This n8n workflow runs every Friday at 5pm:
1. **Fetches** commits, closed issues, and merged PRs from GitHub API
2. **Analyzes** the data with Claude API (`claude-sonnet-4-20250514`)
3. **Delivers** a narrative summary via email and/or Slack/Discord webhook

## Setup (5 Steps)

### 1. Import the workflow

1. Open n8n
2. **Workflows → Add workflow → Import from file**
3. Select `github_weekly_summary.json`

### 2. Configure GitHub credentials

1. Create a [GitHub Personal Access Token](https://github.com/settings/tokens) with `repo` scope
2. In n8n, add it as a **Header Auth** credential:
   - Name: `GitHub API`
   - Header Name: `Authorization`
   - Header Value: `Bearer ghp_your_token`

3. Assign this credential to the three HTTP Request nodes (**Get Commits**, **Get Closed Issues**, **Get Merged PRs**)

### 3. Add Claude API key

1. Get your [Anthropic API key](https://console.anthropic.com)
2. In n8n, add it as a **Header Auth** credential:
   - Name: `Claude API`
   - Header Name: `x-api-key`
   - Header Value: `sk-ant-your-key`

3. Assign this credential to the **Claude API - Generate Summary** node

### 4. Set your repo

Edit the **GitHub Config** node and set the default `owner_repo` value (e.g., `my-org/my-project`).

### 5. Configure delivery

**Email**: Edit the **Send Email Summary** node with your SMTP credentials.

**Slack/Discord**: Set the `webhook_url` variable, or delete the webhook node if not needed.

## Configurable Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `owner_repo` | `owner/repo` | GitHub repo to track |
| `since_date` | 7 days ago | Start of the report window |
| `until_date` | today | End of the report window |
| `from_email` | `weekly@devsummary.dev` | Email sender address |
| `to_email` | `team@example.com` | Email recipient(s) |
| `webhook_url` | (empty) | Slack/Discord webhook URL |

## Sample Output

> **Weekly Dev Summary: my-org/docs-engine**
> _June 28 – July 4, 2026_
>
> This was a productive week for the docs-engine team with 47 commits, 12 merged PRs, and 8 closed issues across 5 contributors.
>
> **Features**: The new Markdown import pipeline was the highlight — PR #342 adds drag-and-drop file upload with real-time preview, and PR #338 introduces the citation manager. The team also shipped the dark mode toggle (PR #345) after weeks of design iteration.
>
> **Quality**: Three bug fixes addressed edge cases in the search indexer (issue #129, #131), and the WebSocket reconnection logic was hardened against network drops (PR #340).
>
> **Suggestions for next week**: Consider adding error boundary tests for the new import pipeline, and prioritize the remaining open accessibility issues (#135, #136) before the next release.
