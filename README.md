# 📊 n8n + Claude API — Weekly Dev Summary

Auto-generate a narrative weekly summary of your GitHub repo's activity using Claude AI.

## Setup (5 steps)

### 1️⃣ Import the workflow
- Open your n8n instance → **Workflows** → **Import from File**
- Select `n8n_weekly_dev_summary.json`

### 2️⃣ Configure credentials
| Variable | Where | Description |
|---|---|---|
| `ghToken` | **Get GitHub Commits/Issues/PRs** nodes → **Options** → **Headers** | GitHub personal access token (`repo` scope) |
| `anthropicApiKey` | **Call Claude API** node → **Headers** | Your Anthropic API key |

### 3️⃣ Set your repo
In the **Get GitHub Commits/Issues/PRs** nodes (or the **Prepare Data** Code node):
- Replace `https://api.github.com/repos/n8n-io/n8n` with your repo URL

### 4️⃣ Pick a delivery method
In the **Route by Delivery Method** Code node, available options:
- **Slack** — Set `deliveryMethod: "slack"` + provide a Slack webhook URL
- **Discord** — Set `deliveryMethod: "discord"` + provide a Discord webhook URL
- **Email** — Set `deliveryMethod: "email"` + configure an SMTP node (not included)

The workflow auto-routes based on the `deliveryMethod` variable.

### 5️⃣ Activate
- Click **Save** → **Active** toggle
- Workflow runs every **Friday at 17:00 UTC** ✨

## Customization

- **Language**: Set `language: "FR"` in the **Prepare Data** Code node for French output
- **Schedule**: Edit the **Weekly Cron Trigger** node's cron expression
- **Max results**: Change `per_page` in the GitHub API URLs (default: 50)

## Output example

```
📅 Weekly Dev Summary — n8n-io/n8n (2026-04-28 → 2026-05-05)

This week saw 47 commits, 12 closed issues, and 8 merged PRs...

🔑 Highlights:
- New HTTP Request node v4.2 with OAuth2 support
- Fixed Webhook memory leak (#12345)
- Community PR: Better error messages for SQLite (#12367)

🚀 Looking ahead: DB query node refactor in progress...
```

## Screenshot

![Workflow overview](screenshot.png)
