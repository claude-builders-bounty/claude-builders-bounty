# n8n + Claude Code — Weekly Dev Summary Workflow

An n8n workflow that runs weekly, fetches your GitHub activity (commits, PRs, issues), and generates a structured markdown summary using Claude Code. Distributes to Slack, Discord, email, and saves a local file.

## What It Does

| Step | Action |
|------|--------|
| 1 | Triggers every week (configurable) |
| 2 | Fetches commits, PRs, and issues from the last 7 days |
| 3 | Aggregates stats (authors, merge counts, issue closures) |
| 4 | Sends aggregated data to Claude for natural language summarization |
| 5 | Distributes the summary to Slack / Discord / Email / File |

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub personal access token
- Anthropic API key (for Claude)
- (Optional) Slack bot token, Discord webhook, or SMTP credentials

## Setup

### 1. Import the workflow

In n8n:
```
Settings → Workflows → Import from File → Select n8n-claude-code-workflow.json
```

### 2. Configure credentials

| Credential | Where to Get |
|------------|-------------|
| GitHub | Settings → GitHub → New Credential → Personal Access Token |
| Anthropic | Settings → Anthropic → New Credential → API Key |
| Slack | Settings → Slack → New Credential → OAuth2 or Bot Token |
| Discord | Discord Server Settings → Integrations → Webhooks |
| SMTP | Your email provider settings |

### 3. Set workflow parameters

Edit the "Weekly Trigger" node and set your repo details in the workflow JSON:
```json
{
  "repoOwner": "your-org",
  "repoName": "your-repo",
  "slackChannel": "#dev-updates",
  "discordWebhook": "https://discord.com/api/webhooks/...",
  "emailRecipients": ["team@company.com"]
}
```

### 4. Activate

Toggle the workflow to **Active**. It runs every Monday at 9 AM by default.

## Sample Output

```markdown
# Weekly Dev Summary: your-repo
**Period:** 2026-05-05 to 2026-05-12

## Commits (23)
- **Authors:** alice, bob, charlie
- **Highlights:**
  - feat: add OAuth2 login flow
  - fix: resolve race condition in payment webhook
  - refactor: migrate database layer to SQLAlchemy 2.0

## Pull Requests
- **Opened:** 5
- **Merged:** 3
- **Closed (unmerged):** 1

## Issues
- **Opened:** 4
- **Closed:** 6

## Summary
This week saw significant progress on authentication and payment stability. The OAuth2 feature is nearing completion with 3 merged PRs. The payment webhook race condition was a critical fix. Database migration work is ongoing.
```

## Customization

- Change cron schedule in "Weekly Trigger" node
- Add more data sources (Linear, Jira, Sentry) by forking the workflow
- Modify the Claude prompt in the "Claude Code Summary" node
- Add conditional logic (only send if commits > 0)

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Weekly     │───▶│   Fetch     │───▶│  Aggregate  │
│  Trigger    │    │   GitHub    │    │   Data      │
└─────────────┘    │   Data      │    └──────┬──────┘
                   └─────────────┘           │
                                              ▼
                                        ┌─────────────┐
                                        │ Claude Code │
                                        │  Summary    │
                                        └──────┬──────┘
                                               │
                        ┌──────────────────────┼──────────────────────┐
                        ▼                      ▼                      ▼
                   ┌─────────┐          ┌─────────┐           ┌────────┐
                   │  Slack  │          │ Discord │           │ Email  │
                   └─────────┘          └─────────┘           └────────┘
                        │                      │                      │
                        └──────────────────────┼──────────────────────┘
                                               ▼
                                        ┌─────────────┐
                                        │ Save .md    │
                                        │ File        │
                                        └─────────────┘
```

## License

MIT — use it in your team, modify it, sell it if you want.
