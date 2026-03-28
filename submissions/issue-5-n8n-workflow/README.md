# n8n Weekly GitHub Dev Summary — Issue #5

An importable n8n workflow that fetches a week's worth of GitHub activity, sends it to Claude API for a narrative summary, and delivers it to Discord or Slack every Friday.

## Setup (5 steps)

**Step 1 — Import the workflow**

In n8n: Workflows → Import from File → select `workflow.json`

**Step 2 — Set credentials**

In the **Configuration** node, set these 5 values directly or via environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO` | Target repository | `vercel/next.js` |
| `ANTHROPIC_API_KEY` | Your Anthropic key | `sk-ant-...` |
| `LANGUAGE` | Summary language | `EN` or `FR` |
| `DELIVERY` | Where to send | `discord` or `slack` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | `https://discord.com/api/webhooks/...` |
| `SLACK_WEBHOOK_URL` | Slack webhook URL | `https://hooks.slack.com/services/...` |

Set environment variables in n8n: Settings → Environment Variables.

**Step 3 — (Optional) Add GitHub token**

For private repos or to increase the GitHub API rate limit, set `GITHUB_TOKEN` in n8n environment variables.

**Step 4 — Test run**

Click **Test workflow** to run it immediately. You should see a Discord/Slack message within 10–15 seconds.

**Step 5 — Activate**

Toggle the workflow to **Active**. It will run every Friday at 5:00 PM (server time).

---

## How to get webhook URLs

**Discord:**
1. Server Settings → Integrations → Webhooks → New Webhook
2. Choose a channel → Copy Webhook URL

**Slack:**
1. api.slack.com/apps → Create App → Incoming Webhooks → Add New Webhook
2. Choose a channel → Copy Webhook URL

---

## Workflow architecture

```
Schedule Trigger (Fri 17:00)
    │
    ▼
Configuration (Set variables)
    │
    ▼
Fetch GitHub Activity (Code node — parallel API calls)
  ├── commits since 7 days ago
  ├── closed issues since 7 days ago
  ├── merged PRs in last 7 days
  └── repo info (stars, description)
    │
    ▼
Generate Narrative (Claude API — claude-sonnet-4-20250514)
  └── 3-4 paragraph narrative summary
    │
    ▼
Format Message (Code node)
  ├── Discord embed with stats + narrative
  └── Slack mrkdwn with stats + narrative
    │
    ▼
Discord or Slack? (IF node)
  ├── DELIVERY=slack → Send to Slack
  └── DELIVERY=discord → Send to Discord
```

**8 nodes total.** No credentials required beyond API keys in the Configuration node.

---

## Sample output

**Discord embed:**
```
📅 Weekly Dev Summary — vercel/next.js

This week saw significant progress on the App Router with 23 commits
addressing performance regressions in server components. Three major
PRs were merged: support for React 20 concurrent features, improved
caching middleware, and a fix for the Edge runtime bundling issue
that had affected 12% of deployments...

📊 23 commits · 8 PRs merged · 14 issues closed
👥 Top contributors: timneutkens (8), ijjk (6), leerob (4)

Week of 2026-03-23 · 125,420⭐
```

**French version (LANGUAGE=FR):**
```
📅 Résumé hebdomadaire — vercel/next.js

Cette semaine a été marquée par des avancées significatives sur
l'App Router avec 23 commits traitant des régressions de performance
dans les composants serveur...
```

---

## Configurable variables

| Variable | Values | Default |
|----------|--------|---------|
| `GITHUB_REPO` | `owner/repo` | `owner/repo` (change this!) |
| `LANGUAGE` | `EN` \| `FR` | `EN` |
| `DELIVERY` | `discord` \| `slack` | `discord` |
| `GITHUB_TOKEN` | GitHub PAT | empty (public repos only) |

---

## Requirements

- n8n v1.0+ (self-hosted or cloud)
- Anthropic API key (`claude-sonnet-4-20250514` model access)
- Discord webhook URL or Slack incoming webhook URL
- (Optional) GitHub personal access token for private repos
