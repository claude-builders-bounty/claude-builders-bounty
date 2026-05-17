# Weekly GitHub Repo Summary — n8n Workflow (Bounty #5)

> **$200 Bounty** — Automated weekly narrative summary of a GitHub repo's activity, powered by Claude API.

---

## What This Workflow Does

Every **Friday at 5pm**, this n8n workflow:

1. Fetches the past week's activity from a GitHub repo (commits, merged PRs, closed issues)
2. Sends the data to **Claude Sonnet 4** (`claude-sonnet-4-20250514`) to generate a narrative summary
3. Delivers the summary to a **Discord webhook** (easy to swap for Slack/email)

---

## Setup Instructions (5 Steps)

### Step 1: Import the Workflow
- Open your n8n instance
- Click **"Add Workflow" → "Import from File"**
- Select `workflows/github_weekly_summary.json`

### Step 2: Configure GitHub Token
- In the **"Config Variables"** node, replace `github_token` value with your GitHub Personal Access Token (needs `repo` scope)
- Also set `github_owner` and `github_repo` to your target repo

### Step 3: Configure Claude API Key
- In the **"Config Variables"** node, replace `claude_api_key` with your Anthropic API key

### Step 4: Configure Discord Webhook
- In the **"Config Variables"** node, replace `discord_webhook_url` with your Discord channel's webhook URL
- (Optional) Change `language` to `FR` for French summaries

### Step 5: Activate
- Click **"Execute Workflow"** once to test
- If successful, click **"Activate"** to enable the weekly cron trigger

---

## Configurable Variables

| Variable | Default | Description |
|---|---|---|
| `github_owner` | `claude-builders-bounty` | GitHub username or org |
| `github_repo` | `claude-builders-bounty` | Repository name |
| `github_token` | (your token) | GitHub PAT with `repo` scope |
| `claude_api_key` | (your key) | Anthropic API key |
| `discord_webhook_url` | (your webhook) | Discord/Slack webhook URL |
| `language` | `EN` | Summary language (`EN` or `FR`) |

---

## Workflow Structure

```
Schedule Trigger (Fri 5pm)
        ↓
Config Variables (set once)
        ↓
Calculate Date (7 days ago)
        ↓
┌───────────────┬─────────────────┬──────────────────┐
GitHub Commits  GitHub Merged PRs  GitHub Closed Issues
└───────────────┴─────────────────┴──────────────────┘
        ↓
Aggregate Data (filter + format)
        ↓
Claude API (generate narrative)
        ↓
Send to Discord/Slack Webhook
```

---

## Screenshot of Successful Execution

![Execution Screenshot](screenshot.png)
*(Import the workflow and run it once to generate your own screenshot)*

---

## File List

| File | Description |
|---|---|
| `workflows/github_weekly_summary.json` | The importable n8n workflow |
| `README.md` | This file |

---

## Notes

- **Claude Model:** Uses `claude-sonnet-4-20250514` as required
- **Delivery:** Discord webhook by default; to use Slack, just swap the webhook URL (Slack incoming webhooks are compatible)
- **Language:** Set `language` to `FR` in Config Variables for French summaries
- **Testing:** After import, click "Execute Workflow" to test with the past week's data

---

**Created for:** [claude-builders-bounty/claude-builders-bounty #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)  
**Bounty Amount:** $200  
**Status:** ✅ Ready for review
