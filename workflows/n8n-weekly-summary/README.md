# Weekly Dev Summary — n8n + Claude API Workflow

Automated weekly narrative summary of GitHub repo activity, powered by Claude.

## Setup (5 steps)

1. **Import workflow**: In n8n, go to Workflows > Import > paste `weekly-dev-summary.json`

2. **Add GitHub credential**: Settings > Credentials > HTTP Header Auth
   - Name: `GitHub Token`
   - Header Name: `Authorization`
   - Header Value: `Bearer ghp_your_token_here`

3. **Set environment variables** in n8n Settings > Variables:
   ```
   GITHUB_REPO=owner/repo
   ANTHROPIC_API_KEY=sk-ant-...
   SUMMARY_LANGUAGE=EN           # or FR
   NOTIFICATION_EMAIL=you@email.com
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...  (optional)
   ```

4. **Configure email** (optional): Settings > Credentials > SMTP > add your email server

5. **Activate**: Toggle the workflow ON. Runs every Friday at 5PM.

## How It Works

```
Cron (Fri 5PM) → Config → [Fetch Commits, PRs, Issues] → Merge → Claude Prompt → Claude API → [Email, Discord]
```

1. **Trigger**: Weekly cron every Friday at 5PM
2. **Fetch**: Gets commits, merged PRs, and closed issues from GitHub API (last 7 days)
3. **Prompt**: Builds a structured prompt with all activity data
4. **Generate**: Calls Claude Sonnet to write a narrative summary (3-5 paragraphs)
5. **Deliver**: Sends via email AND Discord webhook (both configurable)

## Configurable Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_REPO` | `anthropics/claude-code` | Target repository |
| `SUMMARY_LANGUAGE` | `EN` | Summary language (EN/FR) |
| `NOTIFICATION_EMAIL` | — | Email recipient |
| `DISCORD_WEBHOOK_URL` | — | Discord channel webhook |
| `ANTHROPIC_API_KEY` | — | Claude API key |

## Output Example

> **Weekly Dev Summary: anthropics/claude-code (Apr 10, 2026)**
>
> This week saw significant progress with 47 commits across 12 contributors...

## Requirements

- n8n v1.30+ (self-hosted or cloud)
- GitHub personal access token (read-only)
- Anthropic API key (Claude Sonnet)
- SMTP credentials or Discord webhook URL
