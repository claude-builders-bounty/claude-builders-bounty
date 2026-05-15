# n8n Weekly Dev Summary with Claude

An importable n8n workflow that generates a weekly narrative summary of GitHub repo activity using the Claude API.

## What it does

Every Friday at 5PM, the workflow:
1. Fetches commits, closed issues, and merged PRs from the past 7 days
2. Sends the data to Claude (`claude-sonnet-4-20250514`) for a narrative summary
3. Delivers the summary via Discord/Slack webhook and/or email

## Quick setup (5 steps)

### 1. Import the workflow

In n8n: **Menu → Import from File → `n8n-weekly-summary.json`**

### 2. Configure credentials

Create two HTTP Header Auth credentials:

**GitHub Token:**
- Name: `GitHub Token`
- Header Name: `Authorization`
- Header Value: `Bearer ghp_your_github_token`

**Claude API Key:**
- Name: `Claude API Key`
- Header Name: `x-api-key`
- Header Value: `sk-ant-your-claude-key`
- Add header: `anthropic-version` = `2023-06-01`

Then assign them to the respective HTTP Request nodes.

### 3. Set environment variables

```bash
# Required
GITHUB_REPO=owner/repo

# Optional — at least one delivery channel
WEBHOOK_URL=https://discord.com/api/webhooks/...   # Discord or Slack webhook
EMAIL_TO=team@example.com                            # Email recipient

# Optional
LANGUAGE=EN  # EN or FR (controls Claude's output language)
```

Or edit the **Config** node to hardcode values.

### 4. Test

Click **Execute Workflow** to run it manually. Check the output of the **Extract Summary** node.

### 5. Activate

Toggle the workflow to **Active**. It will run every Friday at 5PM automatically.

## Features

- **Weekly cron trigger**: Runs every Friday at 17:00 (configurable)
- **GitHub API integration**: Fetches commits, closed issues, merged PRs
- **Claude API**: Generates a 3-5 paragraph narrative summary
- **Dual delivery**: Discord/Slack webhook AND/OR email
- **Configurable**: Repo, language (EN/FR), destination channels
- **Stats dashboard**: Shows commit count, issues closed, PRs merged

## Output example

```
Weekly Dev Summary: owner/repo

This was a productive week for the project with 23 commits landing across
8 contributors. The team focused on performance improvements and bug fixes.

Key changes:
- Refactored the query engine for 3x faster lookups (#456)
- Fixed memory leak in the WebSocket handler (#442)
- Added retry logic for external API calls (#451)

On the issue front, 12 issues were closed, with the most significant being
the long-standing pagination bug (#380) that had been open for 3 months.

What's next: Based on open issues, the team should consider addressing
the authentication refactoring (#460) and the rate limiting feature (#465).
```

## Node graph

```
[Cron: Friday 5PM]
        │
    [Config]
    ┌───┼───────────┐
    │   │           │
[Commits] [Issues] [PRs]
    │   │           │
    └───┼───────────┘
        │
  [Build Prompt]
        │
  [Claude API]
        │
 [Extract Summary]
    ┌───┴───┐
    │       │
[Webhook] [Email]
```

## Requirements

- n8n (self-hosted or cloud)
- GitHub personal access token (public_repo scope)
- Anthropic API key (Claude access)
- Discord/Slack webhook URL or SMTP config for delivery
