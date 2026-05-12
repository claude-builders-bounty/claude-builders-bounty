# Weekly Dev Summary: n8n + Claude Code

Automated weekly development summary workflow for n8n. Fetches GitHub activity (commits, closed issues, merged PRs) from the past 7 days, generates a narrative summary using Claude (claude-sonnet-4-20250514), and delivers it to a Discord channel.

## Architecture

```
Cron (Friday 17:00 UTC)
  -> Set Date Range & Variables
  -> Fetch Commits / Closed Issues / Merged PRs (parallel)
  -> Combine & Format Data
  -> Call Claude API (claude-sonnet-4-20250514)
  -> Format Output
  -> Send to Discord Webhook
```

## Setup (5 Steps)

### 1. Import the workflow

Open your n8n instance, go to **Workflows > Import from File**, and select `workflow.json`.

### 2. Set up a GitHub Personal Access Token

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens) and create a **Fine-grained** or **Classic** token with `repo` read access.
2. In n8n, go to **Settings > Environment Variables** (or your `.env` file) and add:
   ```
   GITHUB_TOKEN=ghp_your_token_here
   ```

### 3. Set up an Anthropic API Key

1. Get your API key from [console.anthropic.com](https://console.anthropic.com/).
2. Add to n8n environment variables:
   ```
   ANTHROPIC_API_KEY=sk-ant-your_key_here
   ```

### 4. Configure Discord Webhook URL

1. In your Discord server, go to **Server Settings > Integrations > Webhooks > New Webhook**.
2. Copy the webhook URL and add to n8n environment variables:
   ```
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```

### 5. Set your repo and language preference

Add these environment variables in n8n:

```
GITHUB_REPO=owner/repo-name
LANGUAGE=EN
```

- `GITHUB_REPO`: The GitHub repository to track (e.g., `facebook/react`).
- `LANGUAGE`: `EN` for English or `FR` for French summaries.

## Environment Variables Summary

| Variable              | Required | Description                                  |
|-----------------------|----------|----------------------------------------------|
| `GITHUB_REPO`         | Yes      | GitHub repo in `owner/repo` format           |
| `GITHUB_TOKEN`        | Yes      | GitHub personal access token                 |
| `ANTHROPIC_API_KEY`   | Yes      | Anthropic API key for Claude                 |
| `DISCORD_WEBHOOK_URL` | Yes      | Discord webhook URL for delivery             |
| `LANGUAGE`            | No       | Summary language: `EN` (default) or `FR`     |

## Workflow Nodes

| Node                        | Type            | Purpose                                         |
|-----------------------------|-----------------|--------------------------------------------------|
| Weekly Cron (Friday 17:00)  | Schedule Trigger| Fires every Friday at 17:00 UTC                 |
| Set Date Range & Variables  | Code            | Calculates 7-day window, reads env variables     |
| Fetch Commits               | HTTP Request    | GET /repos/{owner}/{repo}/commits                |
| Fetch Closed Issues         | HTTP Request    | GET /repos/{owner}/{repo}/issues?state=closed    |
| Fetch Merged PRs            | HTTP Request    | GET /repos/{owner}/{repo}/pulls?state=closed     |
| Combine & Format Data       | Code            | Merges data into structured prompt               |
| Call Claude API             | HTTP Request    | POST to Anthropic Messages API                   |
| Format Output               | Code            | Extracts summary, truncates for Discord limits   |
| Send to Discord             | HTTP Request    | POST to Discord webhook with rich embed          |

## Error Handling

All HTTP Request nodes have `continueOnFail` enabled. If a GitHub API call fails, the workflow continues with available data. If the Claude API call fails, the error message is forwarded to Discord so you know something went wrong.

## Customization

- **Change schedule**: Edit the cron trigger node to change day/time.
- **Switch to Slack**: Replace the Discord webhook node with a Slack incoming webhook POST (same JSON structure, adjust the payload to Slack's block format).
- **Add email delivery**: Add an n8n Send Email node after Format Output as a parallel output.

## Testing

To test immediately without waiting for Friday:
1. Open the workflow in n8n
2. Click **Execute Workflow** (manual trigger)
3. Verify the Discord message appears in your channel
