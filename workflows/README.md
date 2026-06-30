# Weekly Dev Summary — n8n + Claude Code

Automated weekly development summary workflow for n8n that uses the Claude API to generate narrative summaries of your GitHub repo activity.

## What it does

- **Triggers** every Friday at 5 PM (configurable)
- **Fetches** from GitHub API: commits, closed issues, merged PRs
- **Generates** a narrative summary using Claude (`claude-sonnet-4-20250514`)
- **Delivers** via Discord webhook or email (your choice)

## Setup (5 steps)

### 1. Import the workflow

In n8n, go to **Workflows > Import from File** and select `workflows/weekly-dev-summary.json`.

### 2. Set up environment variables

Configure these variables in n8n (**Settings > Variables**):

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO` | GitHub repo (owner/name) | `myorg/myrepo` |
| `ANTHROPIC_API_KEY` | Your Anthropic API key | `sk-ant-...` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL (if using Discord) | `https://discord.com/api/webhooks/...` |
| `SENDER_EMAIL` | Sender email address (if using email) | `bot@example.com` |
| `DEST_EMAIL` | Destination email address (if using email) | `team@example.com` |
| `SUMMARY_LANGUAGE` | Language for the summary: `EN` or `FR` | `EN` |

### 3. Set up credentials

In n8n, create an **HTTP Header Auth** credential named `GitHub Token`:
- **Header Name**: `Authorization`
- **Header Value**: `token ghp_YOUR_GITHUB_TOKEN`

The token needs `repo` scope to access commit and PR data.

### 4. Choose your delivery method

The workflow includes both Discord and Email delivery nodes. **Enable one and disable the other:**

- **Discord**: Enable the "Send to Discord" node, disable "Send Email"
- **Email**: Enable the "Send Email" node, disable "Send to Discord"

For email, configure SMTP credentials in n8n (**Settings > Credentials > SMTP**).

### 5. Activate the workflow

Toggle the workflow to **Active**. It will run every Friday at 5 PM and deliver a summary to your chosen channel.

## Customization

- **Change schedule**: Edit the `cronExpression` in the "Weekly Friday 5PM" node
- **Change model**: Update the `model` field in the "Claude API — Generate Summary" node
- **Add more data sources**: Add new HTTP Request nodes for GitHub API endpoints (releases, discussions, etc.)

## Example output

```markdown
# Weekly Dev Summary — myorg/myrepo

**Period:** 2026-06-23 to 2026-06-30

## Overview
This week we shipped 3 features and resolved 12 issues...

## Key Accomplishments
- Implemented the new authentication flow (#142)
- Fixed critical performance regression in search (#145)

## Statistics
- **Commits:** 47
- **Issues closed:** 12
- **PRs merged:** 8
```
