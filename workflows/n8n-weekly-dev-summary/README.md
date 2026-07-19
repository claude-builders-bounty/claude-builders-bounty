# n8n Weekly Dev Summary with Claude

Automatically generates a weekly narrative summary of a GitHub repo's activity using the Claude API and delivers it via Discord webhook or email.

## Setup (5 steps)

### 1. Import the workflow

In n8n, click **Workflows** → **Import from File** → select `weekly-dev-summary.json`.

### 2. Configure environment variables

In your n8n instance, set these environment variables:

```bash
GITHUB_TOKEN=ghp_your_github_token
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key
GITHUB_REPO_OWNER=your-org        # e.g. tscircuit
GITHUB_REPO_NAME=your-repo         # e.g. dsn-converter
SUMMARY_LANGUAGE=EN                # EN or FR

# Choose one or both delivery methods:
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
SUMMARY_EMAIL_TO=team@example.com
```

### 3. Configure SMTP (if using email delivery)

In n8n settings, configure SMTP:
```bash
N8N_SMTP_HOST=smtp.gmail.com
N8N_SMTP_PORT=587
N8N_SMTP_USER=your@gmail.com
N8N_SMTP_PASS=your-app-password
```

### 4. Test the workflow

Click **Execute Workflow** manually to verify it runs end-to-end. Check the output of each node:
- **Fetch Commits** — should return commit array
- **Fetch Closed Issues** — should return issues closed this week
- **Fetch Merged PRs** — should return merged PRs
- **Claude API Summary** — should return a Markdown narrative summary
- **Send to Discord / Send Email** — should deliver the summary

### 5. Activate the workflow

Toggle the workflow **Active** switch. It will run every Friday at 5:00 PM automatically.

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Cron Trigger │────▶│ Config Vars  │────▶│ Fetch Commits   │
│  (Fri 5pm)   │     │              │     │ Fetch Issues    │
└─────────────┘     └──────────────┘     │ Fetch PRs       │
                                          └────────┬────────┘
                                                   │
                                          ┌────────▼────────┐
                                          │ Aggregate Data  │
                                          └────────┬────────┘
                                                   │
                                          ┌────────▼────────┐
                                          │ Claude API      │
                                          │ (narrative gen) │
                                          └────────┬────────┘
                                                   │
                                          ┌────────▼────────┐
                                          │ Format Output   │
                                          └────────┬────────┘
                                                   │
                                    ┌──────────────┼──────────────┐
                                    │              │              │
                              ┌─────▼─────┐  ┌────▼─────┐  ┌────▼─────┐
                              │ Discord?  │  │  Email?  │  │  (skip)  │
                              └─────┬─────┘  └────┬─────┘  └──────────┘
                              ┌─────▼─────┐  ┌────▼─────┐
                              │  Send to  │  │   Send   │
                              │  Discord  │  │   Email  │
                              └───────────┘  └──────────┘
```

## Configurable Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_REPO_OWNER` | GitHub org/owner | `tscircuit` |
| `GITHUB_REPO_NAME` | GitHub repo name | `dsn-converter` |
| `SUMMARY_LANGUAGE` | Summary language (`EN` or `FR`) | `EN` |
| `DISCORD_WEBHOOK_URL` | Discord webhook for delivery | (none — skips Discord) |
| `SUMMARY_EMAIL_TO` | Email recipient | (none — skips email) |
| `GITHUB_TOKEN` | GitHub API token | (required) |
| `ANTHROPIC_API_KEY` | Anthropic API key | (required) |

## Output Format

The summary includes:

1. **Overview** — 2-3 sentences on the week's overall theme
2. **Highlights** — Key PRs and changes with context
3. **Issues Resolved** — Summary of closed issues
4. **Contributors** — Who contributed this week
5. **Looking Ahead** — What's in progress based on commit patterns

## Notes

- Uses `claude-sonnet-4-20250514` model as specified
- Fetches up to 100 items per API call (GitHub's max per_page)
- Retries failed API calls up to 3 times with backoff
- Filters PRs to only those merged within the last 7 days
- Discord delivery uses embeds for rich formatting (4000 char limit)
- Email delivery uses HTML formatting with inline styles
