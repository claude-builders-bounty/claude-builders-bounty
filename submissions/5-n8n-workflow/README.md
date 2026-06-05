# n8n + Claude API — Weekly Dev Summary Workflow

## Setup (4 steps)

1. **Import the workflow**: In n8n, go to Workflows → Import from File → select `weekly-summary.json`

2. **Configure Claude API credentials**: Create an HTTP Request node credential with:
   - Base URL: `https://api.anthropic.com`
   - Header: `x-api-key: YOUR_CLAUDE_API_KEY`
   - Header: `anthropic-version: 2023-06-01`

3. **Configure destination**: Choose one:
   - **Email**: Set your SMTP credentials in the Email node
   - **Slack**: Set your webhook URL in the Slack node
   - **Discord**: Set your webhook URL in the Discord node

4. **Set the repo**: In the "GitHub Repo" node, change `owner/repo` to your target repository

## Workflow Steps

```
[Cron trigger: Friday 5pm]
  → [GitHub API: fetch commits/issues/PRs for the week]
  → [Aggregate data into a text prompt]
  → [Claude API: generate narrative summary]
  → [Deliver via Email / Slack / Discord]
```

## Configurable Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `githubRepo` | `owner/repo` | GitHub repository to summarize |
| `destination` | `slack` | `email`, `slack`, or `discord` |
| `language` | `EN` | Summary language (`EN`/`FR`/`ZH`) |
| `daysToFetch` | `7` | Lookback window in days |

## Requirements

- n8n instance (self-hosted or cloud)
- Claude API key
- GitHub personal access token (read-only on the target repo)
- Email SMTP or Slack/Discord webhook URL
