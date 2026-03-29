# Weekly Dev Summary — n8n + Claude API

Automated weekly narrative summary of GitHub repo activity, powered by Claude claude-sonnet-4-20250514.

## What It Does

Every Friday at 5 PM, this workflow:

1. Fetches the past week's **commits**, **closed issues**, and **merged PRs** from GitHub
2. Sends the data to **Claude API** to generate an engaging narrative summary
3. Posts the summary to a **Discord** channel via webhook

If there's no activity, it skips the Claude call and reports "no activity" instead.

## Setup (5 Steps)

### 1. Import the Workflow

In n8n, go to **Workflows → Import from File** and select `workflow.json`.

### 2. Create GitHub Token Credential

- Go to **Settings → Credentials → Add Credential → Header Auth**
- Name: `GitHub Token`
- Header Name: `Authorization`
- Header Value: `Bearer ghp_YOUR_GITHUB_TOKEN`

Your GitHub token needs `repo` scope (or just `public_repo` for public repos).

### 3. Create Anthropic API Key Credential

- Go to **Settings → Credentials → Add Credential → Header Auth**
- Name: `Anthropic API Key`
- Header Name: `x-api-key`
- Header Value: `sk-ant-YOUR_ANTHROPIC_KEY`

### 4. Set Environment Variables

In n8n **Settings → Environment Variables**, add:

| Variable | Example | Required |
|---|---|---|
| `GITHUB_REPO` | `owner/repo-name` | Yes |
| `SUMMARY_LANGUAGE` | `EN` or `FR` | No (default: EN) |
| `DISCORD_WEBHOOK_URL` | `https://discord.com/api/webhooks/...` | Yes |

### 5. Activate & Test

- Click **Execute Workflow** to test manually
- Toggle the workflow **Active** to enable the weekly cron

## Configuration

- **Schedule**: Edit the "Weekly Cron" node to change day/time (default: Friday 5 PM)
- **Language**: Set `SUMMARY_LANGUAGE` to `FR` for French summaries
- **Model**: Uses `claude-sonnet-4-20250514` — change in the Claude API node body if needed
- **Delivery**: Uses Discord webhook. To switch to Slack, replace the webhook URL (Slack incoming webhooks use the same `content` → `text` format — update the JSON body key)

## Workflow Architecture

```
Cron (Fri 5pm)
  → Set Variables (repo, language, date range)
    → [Parallel] Fetch Commits | Fetch Issues | Fetch PRs
      → Merge All Data
        → Process & Shape (Code node: filter, dedupe, format)
          → Has Activity?
            → YES → Claude API → Extract Text → Discord Webhook
            → NO  → "No activity" message
```

## Edge Cases Handled

- **No activity**: Skips Claude API call, avoids wasting tokens
- **Large repos**: Caps at 100 items per category, truncates to 50 for Claude prompt
- **Empty/error responses**: Safe array handling in the Code node
- **Discord message limit**: Truncates summary to 1900 chars
- **PR vs Issue dedup**: Filters out PRs from the issues endpoint (GitHub returns PRs as issues)
- **Merged-only PRs**: Only includes actually merged PRs, not just closed ones

## Cost Estimate

~$0.01–0.03 per weekly run (one Claude API call with ~2K input tokens).

## License

MIT
