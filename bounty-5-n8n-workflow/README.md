# Bounty #5: n8n + Claude API — Weekly Dev Summary

Automated n8n workflow that generates a narrative weekly development summary of any GitHub repo using the Claude API.

## What it does

Every Friday at 5pm, this workflow:

1. Fetches the last 7 days of GitHub activity (commits, closed issues, merged PRs)
2. Sends the raw data to Claude API (`claude-sonnet-4-20250514`) for narrative summarization
3. Delivers the summary via Discord webhook and/or email

## Setup (5 steps)

### 1. Import the workflow
- Open n8n → **Workflows** → **Import from File**
- Select `weekly-dev-summary.json`

### 2. Configure GitHub credentials
- In n8n, go to **Credentials** → **New** → **Header Auth**
- Name: `GitHub Token`
- Header Name: `Authorization`
- Header Value: `Bearer ghp_YOUR_GITHUB_TOKEN`

### 3. Configure Claude API credentials
- In n8n, go to **Credentials** → **New** → **Header Auth**
- Name: `Anthropic API Key`
- Header Name: `x-api-key`
- Header Value: `sk-ant-YOUR_API_KEY`

### 4. Edit the Configuration node
Open the **Configuration** node and set:
```javascript
repo: 'your-org/your-repo',    // Target GitHub repo
language: 'EN',                 // EN or FR
webhookUrl: 'https://...',      // Discord/Slack webhook (optional)
toEmail: 'team@example.com',   // Email recipient (optional)
```

### 5. Activate the workflow
Click **Active** toggle → the workflow runs every Friday at 5pm.

To test immediately: click **Execute Workflow** manually.

## Workflow Architecture

```
[Cron: Fri 5pm] → [Config] → [GitHub API x3 (parallel)]
                                    ↓
                              [Combine Data]
                                    ↓
                           [Claude API: Summarize]
                                    ↓
                            [Format Output]
                              ↙         ↘
                    [Discord]          [Email]
```

## Configurable Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `repo` | GitHub repository (owner/name) | `anthropics/claude-code` |
| `language` | Summary language | `EN` |
| `webhookUrl` | Discord/Slack webhook URL | empty |
| `toEmail` | Email recipient | empty |

## Delivery Options

- **Discord**: Set `webhookUrl` to your Discord webhook URL
- **Slack**: Set `webhookUrl` to your Slack incoming webhook URL (same format)
- **Email**: Configure the n8n email credentials and set `toEmail`
- Both can be active simultaneously

## Sample Output

See [sample-summary.md](./sample-summary.md) for an example of generated output.

## Requirements

- n8n instance (self-hosted or n8n.cloud)
- GitHub Personal Access Token (read-only scope: `repo`)
- Anthropic API key
- Discord webhook URL or email SMTP credentials
