# n8n Weekly Dev Summary — GitHub + Claude

An n8n workflow that automatically generates a narrative weekly development summary from your GitHub repository activity and delivers it to Slack or Discord every Friday at 5pm.

## What it does

Every Friday at 5pm, the workflow:
1. Fetches all commits, closed issues, and merged PRs from the past 7 days via GitHub API
2. Aggregates and formats the data
3. Sends a structured prompt to Claude (`claude-sonnet-4-6`) asking for a prose narrative summary
4. Posts the result to a Slack or Discord webhook

## Setup (5 steps)

**Step 1 — Import the workflow**

In n8n: Settings → Import from file → select `workflow.json`

**Step 2 — Set variables**

In n8n Variables (Settings → Variables), create:

| Variable | Example | Description |
|----------|---------|-------------|
| `GITHUB_REPO` | `vercel/next.js` | `owner/repo` format |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | From console.anthropic.com |
| `WEBHOOK_URL` | `https://hooks.slack.com/...` | Slack or Discord webhook URL |
| `LANGUAGE` | `English` | Summary language (optional, defaults to English) |

**Step 3 — Add GitHub credentials**

In n8n: Credentials → New → GitHub API → add your Personal Access Token (needs `repo` read scope)

**Step 4 — Test**

Click the "Every Friday 5pm" trigger node → Execute workflow. Check your Slack/Discord channel for the summary.

**Step 5 — Activate**

Toggle the workflow to Active. It will run every Friday at 5pm automatically.

## Delivery options

The final node sends to any Slack or Discord webhook. To use email instead:
- Replace the "Send to Slack / Discord" node with an n8n Email node
- Set `To`, `Subject` to `{{ $json.subject }}`, and `Text` to `{{ $json.body }}`

## Example output

> **vercel/next.js — Week of 2026-06-08**
> 
> 📝 47 commits · 🔀 12 PRs merged · ✅ 8 issues closed
>
> This week the team focused primarily on performance improvements to the App Router's prefetching behavior, with three separate PRs landing fixes for stale cache entries under concurrent navigation. The most impactful change was the rework of `unstable_cache` invalidation in PR #67234, which resolves a class of stale-data bugs that had been reported by several large-scale users since 14.2...

## Architecture

```
[Cron: Fri 5pm]
      │
      ├── [GitHub API] → commits (7 days)
      ├── [GitHub API] → closed issues (7 days)  
      └── [GitHub API] → merged PRs (7 days)
            │
      [Aggregate Data] — JS code node, combines all 3
            │
      [Claude API] — generates narrative summary
            │
      [Format Message] — adds header + stats line
            │
      [Slack/Discord Webhook] → delivered
```
