# Weekly GitHub Summary — n8n + Claude AI

> **Bounty:** [$200 — claude-builders-bounty #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)

Automatically generate a weekly narrative summary of any GitHub repository's activity using n8n + Claude API.

## Features

- **Weekly cron trigger** — runs every Friday at 5pm (configurable)
- **Full GitHub API integration** — fetches commits, closed issues, merged PRs
- **Claude AI summarization** — uses `claude-sonnet-4-20250514` for narrative summaries
- **Multi-channel delivery** — Slack, Discord, or email via webhook
- **Bilingual** — supports English and French
- **Configurable** — set repo, language, and delivery destination via environment variables

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐     ┌──────────────┐
│   Schedule   │────▶│  Set Params  │────▶│ GitHub API   │────▶│  Claude  │────▶│  Slack/      │
│  (Fri 5pm)   │     │ (repo/lang)  │     │ (3 parallel) │     │   AI     │     │  Discord     │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────┘     └──────────────┘
                       │                     │
                       │              ┌──────┴──────┐
                       │              │  Commits    │
                       │              │  Issues     │
                       │              │  Merged PRs │
                       │              └──────┬──────┘
                       │                     ▼
                       │              ┌──────────────┐
                       └─────────────▶│  Aggregate   │
                                      │  (Code node) │
                                      └──────────────┘
```

## Setup (5 Steps)

### 1. Install n8n

```bash
npm install n8n -g
n8n start
```

Or use Docker:
```bash
docker run -it --rm -p 5678:5678 n8nio/n8n
```

### 2. Configure Environment Variables

Set these in n8n (Settings → Environment Variables) or your `.env` file:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO` | Target GitHub repository | `facebook/react` |
| `GITHUB_TOKEN` | GitHub Personal Access Token (classic, `repo` scope) | `ghp_xxxx...` |
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-xxxx...` |
| `SUMMARY_LANGUAGE` | Output language: `en` or `fr` | `en` |
| `WEBHOOK_URL` | Delivery endpoint | Slack/Discord webhook URL |

### 3. Import the Workflow

1. Open n8n at `http://localhost:5678`
2. Click **Workflows** → **Import from File**
3. Select `weekly-github-summary.json`
4. The workflow will load with all nodes connected

### 4. Set Up Credentials

In n8n, configure these credentials:
- **GitHub API**: Header Auth → `Authorization: Bearer {{ $env.GITHUB_TOKEN }}`
- **Claude (Anthropic)**: Use the built-in Anthropic credential type with your `ANTHROPIC_API_KEY`

### 5. Activate & Test

1. Click **Activate** to enable the weekly cron schedule
2. Or click **Execute Workflow** to trigger a manual test run
3. Check the webhook destination for the delivered summary

## Workflow Nodes

| Node | Type | Purpose |
|------|------|---------|
| Weekly Trigger | Schedule | Cron: `0 17 * * 5` (Friday 5pm UTC) |
| Set Parameters | Set | Initialize repo, date range (7 days), language, token |
| Fetch Commits | HTTP Request | `GET /repos/{owner}/{repo}/commits?since=...` |
| Fetch Closed Issues | HTTP Request | `GET /repos/{owner}/{repo}/issues?state=closed&since=...` |
| Fetch Merged PRs | HTTP Request | `GET /repos/{owner}/{repo}/pulls?state=closed&base=main` |
| Aggregate Data | Code | Combine 3 API responses, build Claude prompt |
| Claude AI Summary | Anthropic LLM | Generate narrative summary (max 2000 tokens) |
| Send to Slack/Discord | HTTP Request | POST summary to webhook URL |

## Example Output

```
📊 Weekly GitHub Summary — facebook/react

This week saw impressive activity in the React repository with 47 commits,
12 closed issues, and 8 merged pull requests!

🔥 Highlights:
- PR #2847: Major performance optimization to the reconciler (+340/-120 lines)
- PR #2851: Fixed concurrent mode edge case in Suspense boundaries
- @gaearon led the charge with 12 commits this week

📈 Trends:
- 34% increase in PR merges compared to last week
- Issue resolution time improved to avg 2.3 days
- Top contributors: @gaearon, @eps1lon, @rickhanlonii

Keep up the great work, team! Next week we'll see if the new Suspense fixes
hold up under the upcoming stress test...
```

## Customization

### Change the Schedule
Edit the cron expression in the **Weekly Trigger** node. Examples:
- `0 9 * * 1` — Monday 9am
- `0 12 * * 5` — Friday noon

### Add Email Delivery
Replace the "Send to Slack/Discord" node with an **Email (SMTP)** node configured with your SMTP credentials.

### Add More Languages
The prompt in the **Aggregate Data** node supports any language Claude can handle. Just set `SUMMARY_LANGUAGE` to your preferred language code.

## License

MIT
