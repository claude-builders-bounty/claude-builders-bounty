# Weekly GitHub Dev Summary — n8n + Claude

Automatically generate a weekly narrative summary of any GitHub repo's activity using Claude AI.

## What It Does

Every week (default: Friday 5pm), this workflow:
1. Fetches **commits**, **closed issues**, and **merged PRs** from a GitHub repo (past 7 days)
2. Sends the structured data to **Claude API** (`claude-sonnet-4-20250514`)
3. Delivers a narrative summary via **webhook** (Slack/Discord) or logs it for debugging

## 5-Step Setup

### 1. Import the Workflow
In your n8n instance, go to **Workflows → Import from File** and select `weekly-dev-summary.json`.

### 2. Set Environment Variables
Add these to your n8n instance (Settings → Environment Variables):

| Variable | Description | Example |
|---|---|---|
| `GITHUB_REPO` | GitHub repo in `owner/repo` format | `openclaw/openclaw` |
| `GITHUB_TOKEN` | GitHub Personal Access Token (scope: `repo`) | `ghp_xxxx...` |
| `CLAUDE_API_KEY` | Anthropic API key | `sk-ant-xxxx...` |
| `LANGUAGE` | Summary language: `en` or `zh` | `en` |
| `DELIVERY_METHOD` | `webhook` (default) | `webhook` |
| `WEBHOOK_URL` | Slack/Discord incoming webhook URL | `https://hooks.slack.com/...` |

### 3. Configure GitHub Credentials
In n8n, create a **Header Auth** credential named `GitHub API Token`:
- Header Name: `Authorization`
- Header Value: `Bearer YOUR_GITHUB_TOKEN`

Or update the credential reference in the JSON to match your existing GitHub credential.

### 4. Test the Workflow
Click **Execute Workflow** in n8n. Check the output:
- **Fetch nodes** should return arrays of GitHub data
- **Call Claude API** should return a 200 with summary text
- **Send to Webhook** should post to your Slack/Discord channel

### 5. Activate
Toggle the workflow to **Active**. It will run every Friday at 5pm UTC.

## Customization

- **Schedule**: Edit the "Weekly Schedule" node to change day/time
- **Model**: Change `claudeModel` in the "Set Config" code node
- **Delivery**: The "Extract Summary" node fans out to both webhook + log. Add email, Telegram, or other nodes as needed
- **Language**: Set `LANGUAGE=zh` for Chinese summaries

## Architecture

```
Schedule → Set Config → Fetch GitHub Data (commits/issues/PRs)
  → Build Prompt → Call Claude API → Extract Summary
  → Send to Webhook + Log Output
```

## Files

- `weekly-dev-summary.json` — Importable n8n workflow
- `README.md` — This file

## Screenshot

> **Note**: A screenshot of successful execution on a real n8n instance will be added after the workflow is imported and tested. The JSON structure is validated and import-ready.
