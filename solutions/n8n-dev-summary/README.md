# 📊 Weekly Dev Summary — n8n Workflow

Automatically generates a weekly narrative summary of a GitHub repository's activity using Claude AI, delivered to Discord every Friday at 5PM UTC.

## Architecture

```
Cron (Fri 5PM) → Set Variables → GitHub API (commits + issues + PRs in parallel)
                                         ↓
                               Code: Format Prompt → Claude API → Discord Webhook
```

## Setup (5 Steps)

### Step 1 — Import the Workflow

In your n8n instance, go to **Workflows → Import from File** and upload `weekly-dev-summary.workflow.json`.

### Step 2 — Configure the Variables

Open the **Set Variables** node and fill in your values:

| Variable | Description | Example |
|---|---|---|
| `GITHUB_REPO` | Target repository (owner/repo) | `microsoft/vscode` |
| `GITHUB_TOKEN` | GitHub Personal Access Token (read access) | `ghp_xxxxxxxxxxxx` |
| `DISCORD_WEBHOOK_URL` | Discord channel webhook URL | `https://discord.com/api/webhooks/...` |
| `LANGUAGE` | Summary language: `EN` or `FR` | `EN` |
| `CLAUDE_API_KEY` | Anthropic API key | `sk-ant-xxxxxxxxxxxx` |

**GitHub Token:** Create at https://github.com/settings/tokens — needs `repo` (or `public_repo` for public repos) scope.

**Discord Webhook:** In Discord, go to your channel → Edit Channel → Integrations → Webhooks → New Webhook → Copy URL.

**Anthropic API Key:** Get yours at https://console.anthropic.com/settings/keys.

### Step 3 — Activate the Workflow

Toggle the workflow **Active** in the top-right of the editor. It will now fire every Friday at 17:00 UTC.

### Step 4 — Test It Manually

Click **Execute Workflow** to run it immediately and verify the Discord message appears in your channel.

### Step 5 — (Optional) Adjust Language

Set `LANGUAGE` to `FR` in the **Set Variables** node for a fully French summary. Switch back to `EN` for English.

---

## Notes

- The workflow fetches up to 100 commits, issues, and PRs per run (GitHub API pagination limit per request). For very active repos, this covers a typical week.
- Claude model used: `claude-sonnet-4-20250514`
- Discord embeds truncate at 4,000 characters; very long summaries are trimmed automatically.
- The **Code: Format Data** node filters PRs to only those merged within the last 7 days, and issues to those closed within the last 7 days.

## Cost Estimate

- GitHub API: Free (rate limits apply)
- Claude API: ~$0.01–$0.05 per weekly run (claude-sonnet-4 pricing)
- n8n: Free self-hosted or included in cloud plans
