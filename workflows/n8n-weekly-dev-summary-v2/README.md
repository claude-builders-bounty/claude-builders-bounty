# Weekly Dev Summary v2 - n8n Workflow

Automated weekly development summary using n8n, GitHub API, Claude AI, and Discord.

## Features

- **Schedule**: Runs every Friday at 5pm (UTC)
- **GitHub Data**: Fetches commits, closed issues, and merged PRs from the past week
- **AI Summary**: Uses Claude Sonnet 4 to generate a friendly narrative summary
- **Discord Delivery**: Sends formatted summary to your Discord channel
- **Multi-language**: Supports English (EN) and French (FR)
- **Error Handling**: Retry logic and error logging for robust execution

## Prerequisites

- n8n instance (self-hosted or cloud)
- GitHub personal access token
- Anthropic API key
- Discord webhook URL

## Setup (5 Steps)

### Step 1: Create n8n Credentials

1. **GitHub Token**: Create a GitHub personal access token with `repo` and `read:user` scopes
2. **Anthropic API Key**: Get your API key from [Anthropic Console](https://console.anthropic.com/)
3. In n8n, go to **Credentials** and create:
   - `httpHeaderAuth` for GitHub (header: `Authorization` = `Bearer YOUR_TOKEN`)
   - `httpQueryAuth` for Claude (key: `x-api-key`)

### Step 2: Import the Workflow

1. Open n8n
2. Click **Workflows** → **Import from File**
3. Select `weekly-dev-summary-v2.json`
4. Click **Save**

### Step 3: Configure Variables

In n8n **Settings** → **Variables**, add these workflow variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `GITHUB_OWNER` | `your-github-username` | GitHub repository owner |
| `GITHUB_REPO` | `your-repo-name` | GitHub repository name |
| `LANGUAGE` | `EN` or `FR` | Summary language |
| `DISCORD_WEBHOOK_URL` | `https://discord.com/api/webhooks/...` | Your Discord webhook URL |

### Step 4: Connect Credentials

1. Edit each HTTP Request node
2. For GitHub nodes: Select your GitHub `httpHeaderAuth` credential
3. For Claude API node: Select your Claude `httpQueryAuth` credential

### Step 5: Activate

1. Click **Activate** on the workflow
2. Test manually using the "Test workflow" button
3. Verify Discord receives the summary

## Workflow Structure

```
Schedule Trigger (Friday 5pm)
  └→ Set Config Variables
      └→ Calculate Date Range
          ├→ GitHub: Commits
          ├→ GitHub: Issues (closed)
          └→ GitHub: PRs (merged)
              └→ Format Data for Claude
                  └→ Call Claude API
                      └→ Discord Webhook
```

## Environment Variables

All sensitive data uses n8n variables/credentials, never hardcoded:

- `ANTHROPIC_API_KEY` - Your Claude API key
- `GITHUB_TOKEN` - Your GitHub personal access token (stored in credential)
- `DISCORD_WEBHOOK_URL` - Discord webhook URL

## Troubleshooting

- **No data fetched**: Verify GitHub credentials and repository name
- **Claude errors**: Check API key and quota
- **Discord not receiving**: Verify webhook URL is valid
- **Wrong date range**: n8n server timezone may differ - adjust cron expression if needed
