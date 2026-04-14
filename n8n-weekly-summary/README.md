# Weekly GitHub Activity Summary — n8n + Claude AI

An automated n8n workflow that generates a **narrative weekly summary** of your GitHub repository's activity, powered by Claude AI (`claude-sonnet-4-20250514`).

## What It Does

Every **Friday at 5pm**, the workflow:

1. **Fetches** from GitHub API: commits, closed issues, merged PRs (last 7 days)
2. **Aggregates** data: contributor stats, most-changed files, label distribution
3. **Sends** to Claude API for narrative summary generation
4. **Delivers** via Slack/Discord webhook or email

## Setup (5 Steps)

### Step 1: Import the Workflow

In your n8n instance:
1. Go to **Workflows** → **Import from File**
2. Upload `weekly-summary-workflow.json`
3. Click **Import**

### Step 2: Configure GitHub Credentials

1. In n8n, go to **Credentials** → **Add Credential**
2. Select **GitHub API**
3. Generate a [GitHub Personal Access Token](https://github.com/settings/tokens) with `repo` scope
4. Paste the token and save

### Step 3: Set Environment Variables

Click on the workflow → **Settings** → **Environment Variables**:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GITHUB_REPO` | ✅ | Repository owner/name | `facebook/react` |
| `ANTHROPIC_API_KEY` | ✅ | Your Anthropic API key | `sk-ant-...` |
| `WEBHOOK_URL` | ⚠️* | Slack/Discord webhook URL | `https://hooks.slack.com/...` |
| `EMAIL_TO` | Email fallback address | `team@example.com` | |
| `EMAIL_FROM` | Sender email | `noreply@example.com` | |
| `LANGUAGE` | Output language | `EN` or `FR` | `EN` |

\* Either `WEBHOOK_URL` or `EMAIL_TO` must be set (or both).

### Step 4: Activate the Workflow

1. Toggle the **Active** switch in the top-right corner
2. The workflow will run every Friday at 5pm (your n8n server's timezone)

### Step 5: Test Manually

1. Click **Test Workflow** button (or **Execute Node** on any node)
2. Verify the output in the **Generate Summary (Claude API)** node
3. Check delivery in Slack/Discord or email inbox

## Workflow Architecture

```
┌──────────────────────┐
│  Schedule Trigger     │  Every Friday at 5pm
│  (Cron: 0 17 * * 5)  │
└──────────┬───────────┘
           ▼
┌──────────────────────┐    ┌───────────────────┐    ┌──────────────────┐
│  Get Repo Info        ├──▶│ Get Weekly Commits  │───▶│                   │
└──────────┬───────────┘    └───────────────────┘    │                   │
           │                                        │   Aggregate Data   │
┌──────────▼───────────┐    ┌───────────────────┐    │   (Code Node)      │
│  Get Closed Issues    ├──▶│ Get Merged PRs      ├──▶│                   │
└──────────────────────┘    └───────────────────┘    └────────┬──────────┘
                                                          │
                                                          ▼
                                           ┌──────────────────────────────┐
                                           │  Generate Summary            │
                                           │  (Claude API - sonnet 4)     │
                                           └──────────────┬───────────────┘
                                                          │
                                                          ▼
                                           ┌──────────────────────────────┐
                                           │  Format Output               │
                                           │  (Add header + markdown)      │
                                           └──────────────┬───────────────┘
                                                          │
                                    ┌─────────────────────┴─────────────────────┐
                                    ▼                                           ▼
                        ┌──────────────────────┐              ┌──────────────────┐
                        │  Send to Webhook      │              │  Send Email       │
                        │  (Slack / Discord)    │              │  (Fallback)       │
                        └──────────────────────┘              └──────────────────┘
```

## Configurable Variables

### GitHub Repository
Change which repo to monitor by updating `GITHUB_REPO`. Supports any public or private repo your token has access to.

### Delivery Channel
- **Slack**: Create an [Incoming Webhook](https://api.slack.com/messaging/webhooks) and set `WEBHOOK_URL`
- **Discord**: Create a [Webhook](https://support.discord.com/hc/en-us/articles/228383668) and set `WEBHOOK_URL`
- **Email**: Set `EMAIL_TO` and configure SMTP in n8n settings

### Language
Set `LANGUAGE=EN` (default) or `LANGUAGE=FR` for French output. The prompt instructs Claude to generate summaries in the specified language.

## Sample Output

```
📊 **Weekly Dev Summary — facebook/react**
📅 2026-04-07 → 2026-04-14

This week saw solid development activity with 47 commits across 23 files from 8 contributors.
The team made significant progress on the concurrent rendering pipeline...

### Key Highlights
• Merged 12 PRs including the new Suspense boundary optimization (#32001)
• Closed 8 issues, with 3 bug fixes shipped to production
• New contributor @janedoe made their first commit to the codebase

### Areas of Note
• High activity in `react-dom/src/` — consider splitting into focused PRs
• 3 issues labeled "bug" were closed — good velocity on tech debt
```

## Requirements

- **n8n** v1.0+ (self-hosted or cloud)
- **Anthropic API key** with access to `claude-sonnet-4-20250514`
- **GitHub Personal Access Token** with `repo` scope
- **Slack/Discord webhook** OR **SMTP** configured in n8n

## Customization

### Change Schedule
Edit the **Schedule Trigger** node and update the cron expression:
- Every Monday 9am: `0 9 * * 1`
- Daily at 6pm: `0 18 * * *`
- Bi-weekly Friday: `0 17 * * 5 % 2`

### Adjust Prompt
Edit the **Generate Summary (Claude API)** node's messages parameter to change tone, format, or add custom instructions.

### Add More Data Sources
Add additional GitHub nodes (releases, comments, reviews) before the **Aggregate Data** node, then include them in the aggregation script.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No commits found | Check `GITHUB_REPO` value and GitHub token permissions |
| Claude API error | Verify `ANTHROPIC_API_KEY` is valid and has credits |
| Webhook not firing | Test `WEBHOOK_URL` with curl first |
| Email not sending | Check n8n SMTP settings under Settings → Credentials |

## License

MIT
