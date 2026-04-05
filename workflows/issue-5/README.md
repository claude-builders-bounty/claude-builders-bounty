# Weekly Dev Summary — n8n Workflow

Automated weekly narrative summary of GitHub repo activity, powered by Claude AI, delivered to Discord.

## What It Does

Every Friday at 5 PM, this workflow:
1. Fetches this week's commits, closed issues, and merged PRs from GitHub API
2. Filters to the last 7 days of activity
3. Sends a structured prompt to Claude (claude-sonnet-4-20250514)
4. Posts the generated narrative summary to Discord webhook

## 5-Minute Setup

### Step 1: Import into n8n
- Open n8n → click **"Import from File"** → select `weekly-dev-summary.json`

### Step 2: Configure Variables
In n8n **Settings → Variables**, add these workflow variables:

| Variable | Value |
|----------|-------|
| `GITHUB_REPO` | `owner/repo` (e.g. `claude-builders-bounty/claude-builders-bounty`) |
| `GITHUB_TOKEN` | Your GitHub PAT (needs `repo` scope) |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `DISCORD_WEBHOOK_URL` | `https://discord.com/api/webhooks/...` |

For `LANGUAGE`, set `EN` (English) or `JA` (Japanese).

### Step 3: Adjust Repo
Edit the three GitHub HTTP Request nodes and update the repo name if needed.

### Step 4: Test
Click **"Test Workflow"** — you should see a Discord message appear in your channel.

### Step 5: Activate
Toggle the workflow **ON**. It runs automatically every Friday at 5 PM.

## Acceptance Criteria

- [x] Exportable n8n workflow (`.json` file, importable)
- [x] Trigger: weekly cron (`0 17 * * 5`, Friday 5 PM)
- [x] Fetches commits, closed issues, merged PRs from GitHub API
- [x] Calls Claude API (`claude-sonnet-4-20250514`)
- [x] Delivers summary via Discord webhook
- [x] Configurable: GitHub repo, Discord channel, language (EN/JA)
- [x] README with setup in 5 steps

## Example Output

```
📊 Weekly Dev Summary

This week the team shipped 12 commits, closed 3 issues, and merged 5 PRs.

Highlights:
- New CI pipeline cut build times by 40%
- @alice shipped the new onboarding flow
- 3 bugs fixed in the payment module

Keep shipping! 🚀
```
