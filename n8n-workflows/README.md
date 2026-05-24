# GitHub Weekly Dev Summary — n8n Workflow

> Automated weekly narrative summary of any GitHub repository, powered by Claude API and delivered via Discord/Slack webhook.

## Setup (5 Steps)

### 1. Import the workflow
In n8n, go to **Workflows → Add Workflow → Import from File** and select `weekly-dev-summary.json`.

### 2. Set environment variables
In n8n **Settings → Variables**, add these:

| Variable | Description | Example |
|----------|-------------|---------|
| `github_token` | GitHub personal access token (classic) with `repo` scope | `ghp_xxxxxxxxxxxx` |
| `anthropic_api_key` | Anthropic API key | `sk-ant-api03-...` |
| `webhook_url` | Discord/Slack incoming webhook URL | `https://hooks.slack.com/services/...` |
| `github_repo` | *(optional)* Target repository | `owner/repo` |
| `language` | *(optional)* Summary language: `EN` or `FR` | `EN` |
| `destination_channel` | *(optional)* Channel name for metadata | `general` |

### 3. Configure the trigger
Open the **"Weekly Trigger (Fri 5PM)"** node. By default it runs every Friday at 5:00 PM. Adjust the cron expression if needed.

### 4. Connect your webhook
Replace `webhook_url` with your actual Discord or Slack incoming webhook URL. The payload format is compatible with both platforms.

### 5. Activate & test
Click **Activate**, then click **Execute Workflow** to run a manual test. Check your Discord/Slack channel for the summary.

---

## Workflow Overview

| Step | Node | Purpose |
|------|------|---------|
| 1 | `Weekly Trigger (Fri 5PM)` | Cron schedule — every Friday at 5 PM |
| 2 | `Config & Date Setup` | Sets 7-day window, loads variables |
| 3 | `Fetch Commits` | GitHub API — commits from the last 7 days |
| 4 | `Fetch Closed Issues` | GitHub API — issues closed in the last 7 days |
| 5 | `Fetch Merged PRs` | GitHub API — PRs merged in the last 7 days |
| 6 | `Aggregate Data` | Parses & counts commits, PRs, issues |
| 7 | `Build Claude Prompt` | Assembles narrative prompt (EN or FR) |
| 8 | `Claude API` | Calls `claude-sonnet-4-20250514` for the summary |
| 9 | `Extract Summary` | Parses Claude response text |
| 10 | `Send to Webhook` | POSTs markdown summary to Discord/Slack |

---

## Customization

- **Language**: Set `language` variable to `FR` for French summaries; defaults to English.
- **Repository**: Override `github_repo` per workflow instance.
- **Delivery**: Swap the final HTTP Request node for Email, Telegram, or any other n8n node.

## Screenshot

*(Tested and executed successfully on n8n Cloud — see PR discussion for execution screenshot.)*
