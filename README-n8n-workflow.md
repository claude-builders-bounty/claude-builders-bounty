# n8n + Claude Weekly Dev Summary

Automatically generate a weekly development summary using n8n and Claude API.

## Setup (5 Steps)

### 1. Import the workflow
1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Select `weekly-summary-workflow.json`

### 2. Configure credentials
- **GitHub**: Add a `httpQueryAuth` credential with your GitHub token
- **Claude (Anthropic)**: Add a `httpHeaderAuth` credential with your Anthropic API key
- **Slack/Discord**: Add your webhook URL (optional)

### 3. Edit configuration variables
Open the **Load Config** node and set:
| Variable | Example | Description |
|----------|---------|-------------|
| `repo_url` | `https://api.github.com/repos/owner/repo` | GitHub repo to track |
| `language` | `EN` or `ZH` | Output language |
| `delivery_type` | `slack`, `discord`, or `console` | Where to send |
| `webhook_url` | `https://hooks.slack.com/...` | Webhook URL |
| `days_back` | `7` | Days of data to fetch |

### 4. Activate the workflow
Toggle the workflow to **Active**. It runs every Friday at 5 PM.

### 5. Test manually
Click **Execute Workflow** to generate an immediate report.

## Output Example
```
📊 Weekly Dev Report
📅 2026-06-30 ~ 2026-07-07
📦 owner/repo

📈 Stats: 23 commits | 5 issues | 3 PRs

## Weekly Summary
This week's development focused on...
```
