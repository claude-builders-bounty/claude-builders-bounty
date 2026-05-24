# n8n Weekly Dev Summary — Claude + GitHub

> An n8n workflow that automatically generates a weekly narrative summary of a GitHub repository's activity using the Claude API.

## What It Does

Every Friday at 5 PM, this workflow:

1. **Fetches** the past week's GitHub activity (commits, closed issues, merged PRs)
2. **Analyzes** contributor stats and top contributors
3. **Generates** a human-readable narrative summary via Claude (`claude-sonnet-4-20250514`)
4. **Delivers** the summary to Discord, Slack, or email

## Setup (5 Steps)

### Step 1: Import the Workflow

Open your n8n instance and import `workflow.json`:
- Go to **Workflows → Import from File**
- Select `workflow.json`

### Step 2: Configure GitHub Token Credential

In n8n, create an HTTP Header Auth credential named **"GitHub Token"**:
- **Header Name**: `Authorization`
- **Header Value**: `token ghp_YOUR_GITHUB_TOKEN`

> Generate a token at [github.com/settings/tokens](https://github.com/settings/tokens) with `repo` scope.

### Step 3: Configure Claude API Key Credential

Create an HTTP Header Auth credential named **"Claude API Key"**:
- **Header Name**: `x-api-key`
- **Header Value**: `sk-ant-YOUR_CLAUDE_API_KEY`

> Get your key at [console.anthropic.com](https://console.anthropic.com).

### Step 4: Set Environment Variables

Configure these environment variables in your n8n instance (Settings → Environment Variables):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WEEKLY_SUMMARY_REPO` | ✅ | `anthropics/claude-code` | GitHub repo in `owner/repo` format |
| `DISCORD_WEBHOOK_URL` | ✅* | — | Discord or Slack webhook URL |
| `WEEKLY_SUMMARY_LANG` | ❌ | `EN` | Summary language (`EN` or `FR`) |
| `FROM_EMAIL` | ❌ | `noreply@example.com` | Sender email (if using email) |
| `TO_EMAIL` | ❌ | `team@example.com` | Recipient email (if using email) |

> *Either `DISCORD_WEBHOOK_URL` or email must be configured.

### Step 5: Activate the Workflow

Toggle the workflow to **Active**. It will run automatically every Friday at 5 PM (UTC).

## Manual Test

Click **Test Workflow** in the n8n editor to run it immediately and verify all connections work.

## Customization

- **Change the schedule**: Edit the "Weekly Cron" node's cron expression
- **Switch to email delivery**: Enable the "Send Email" node and configure SMTP credentials in n8n
- **Adjust summary prompt**: Edit the "Generate Summary with Claude" node to change the prompt language or structure
- **Multiple repos**: Duplicate the workflow and set different `WEEKLY_SUMMARY_REPO` values

## Workflow Architecture

```
┌─────────────────┐
│  Weekly Cron     │  (Friday 5pm)
│  (Friday 5pm)    │
└────────┬────────┘
         │
    ┌────▼────┐
    │  Set    │  (repo, date range)
    │Variables│
    └────┬────┘
         │
    ┌────┼────────────────┐
    │    │                │
    ▼    ▼                ▼
┌──────┐┌──────┐  ┌──────────┐
│Commit││Issues│  │ Merged   │
│ API  ││ API  │  │ PRs API  │
└──┬───┘└──┬───┘  └────┬─────┘
   │       │           │
   └───────┼───────────┘
           │
    ┌──────▼──────┐
    │Merge &      │  (stats, filtering)
    │Analyze Data │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │Claude API   │  (narrative generation)
    │(Sonnet)     │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │Extract Text │
    └──────┬──────┘
           │
    ┌──────┼──────────┐
    ▼      ▼          ▼
┌───────┐┌───────┐┌────────┐
│Discord││Slack  ││ Email  │
│Webhook││Webhook││(opt.)  │
└───────┘└───────┘└────────┘
```

## Sample Output

```markdown
# 📊 Weekly Dev Summary — owner/repo

**Period:** 2026-05-15 → 2026-05-22

## High-Level Overview
This was a productive week with 47 commits across 8 contributors, closing 12 issues
and merging 9 pull requests. The team focused on authentication improvements and
performance optimization.

## Key Accomplishments
- **OAuth2 Provider Support**: Merged the long-awaited OAuth2 integration (#234)
- **Query Performance**: Database queries are now 3x faster after index optimization (#241)
- **CI/CD Pipeline**: Reduced build times from 12min to 4min (#238)

## Notable PRs
- #234: Add OAuth2 provider support by @alice
- #241: Optimize database query performance by @bob
- #238: Overhaul CI/CD pipeline by @charlie

## Community Highlights
Top contributor this week: @alice with 15 commits
New contributor: @diana made their first PR (#245)

## What to Watch Next Week
- API v2 migration is in progress (#250)
- New dashboard redesign PR coming soon
```

## Requirements

- n8n v1.0+ (self-hosted or cloud)
- GitHub Personal Access Token with `repo` scope
- Anthropic API key
- Discord/Slack webhook URL (or SMTP configured)

## License

MIT
