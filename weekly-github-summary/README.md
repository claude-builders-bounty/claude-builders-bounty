# Weekly GitHub Activity Summary — n8n + Claude AI

An n8n workflow that automatically generates a weekly narrative summary of a GitHub repository's activity using Claude AI, delivered via email and/or Slack/Discord webhook.

## What it does

1. **Triggers** every Friday at 5pm (configurable)
2. **Fetches** from GitHub API: commits, closed issues, merged PRs for the past 7 days
3. **Calls Claude** (`claude-sonnet-4-20250514`) to generate a narrative prose summary
4. **Delivers** via email (SMTP) AND Slack/Discord webhook in parallel

## Setup (5 steps)

### 1. Import the workflow
In n8n: **Workflows → Import from file** → select `weekly_github_summary.json`

### 2. Create credentials

| Credential | Type | Details |
|------------|------|---------|
| GitHub Token | HTTP Header Auth | Header: `Authorization`, Value: `token ghp_your_token` |
| Anthropic API Key | HTTP Header Auth | Header: `x-api-key`, Value: `sk-ant-your_key` |
| SMTP | SMTP | Your email server details |

### 3. Set workflow variables (n8n Settings → Variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_REPO` | `anthropics/claude-code` | Target repo (`owner/repo`) |
| `NOTIFY_EMAIL` | `team@example.com` | Destination email |
| `SLACK_WEBHOOK_URL` | — | Slack or Discord webhook URL |
| `LANGUAGE` | `EN` | Summary language (`EN` or `FR`) |

### 4. Assign credentials to nodes
Click each node that needs credentials and select the ones you created.

### 5. Activate the workflow
Toggle **Active** in the top right. It will run every Friday at 5pm.

## Sample output

> This week saw significant momentum in the claude-code repository, with 23 commits spanning documentation improvements and bug fixes across the CLI toolchain. The most notable change was the merge of PR #892 which introduced streaming support for long-running tool calls, a frequently requested feature that directly addresses timeout issues reported by enterprise users...

## Customization

- **Change schedule**: Edit the "Weekly Cron" node trigger settings
- **Different delivery**: Disable either the Email or Slack node
- **Adjust summary length**: Modify `max_tokens` in the Claude API node (default: 1024)
- **Filter commit types**: Edit the "Build Claude Prompt" code node to filter by conventional commit prefixes
