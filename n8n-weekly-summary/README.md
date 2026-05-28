# 📊 n8n Weekly Dev Summary (Claude)

An n8n workflow that automatically generates a weekly narrative summary of a GitHub repo's activity using the Claude API.

**Bounty:** [#5 — $200](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)

## What It Does

Every Friday at 5pm, this workflow:
1. Fetches the week's commits, closed issues, and merged PRs from GitHub
2. Sends the data to Claude (`claude-sonnet-4-20250514`) for analysis
3. Generates a narrative summary with emoji headers
4. Posts it to Discord (or Slack/email)

## Setup (5 steps)

### 1. Import the Workflow

In n8n, go to **Workflows → Import from File** and select `weekly-dev-summary.json`.

### 2. Create Credentials

Create two HTTP Header Auth credentials in n8n:

**GitHub Token:**
- Name: `GitHub Token`
- Header Name: `Authorization`
- Header Value: `token ghp_YOUR_GITHUB_TOKEN`

**Anthropic API Key:**
- Name: `Anthropic API Key`
- Header Name: `x-api-key`
- Header Value: `sk-ant-YOUR_API_KEY`

Also add the Anthropic version header:
- Header Name: `anthropic-version`
- Header Value: `2023-06-01`

### 3. Configure Variables

Edit the **Set Variables** node:
- `repo`: Your GitHub repo (e.g., `facebook/react`)
- `language`: `en` for English, `fr` for French
- `webhook_url`: Your Discord/Slack webhook URL

### 4. Set Up Discord Webhook

1. Go to your Discord server → Settings → Integrations → Webhooks
2. Click **New Webhook**, choose the channel
3. Copy the webhook URL
4. Paste it in the `webhook_url` variable

### 5. Activate the Workflow

Toggle the workflow to **Active**. It will run every Friday at 5pm.

## Customization

### Change the Schedule
Edit the **Weekly Trigger** node's cron expression:
- `0 17 * * 5` = Friday 5pm
- `0 9 * * 1` = Monday 9am
- `0 17 * * 1-5` = Weekdays 5pm

### Use Slack Instead of Discord
Replace the **Send to Discord** node with an HTTP Request to your Slack webhook URL. The message format is the same.

### Use Email
Replace the **Send to Discord** node with n8n's Send Email node. Set the subject to "Weekly Dev Summary" and the body to `{{ $json.content }}`.

## Required Credentials

| Credential | Purpose |
|------------|---------|
| GitHub Token | Fetch commits, issues, PRs (needs `repo` scope) |
| Anthropic API Key | Generate summary via Claude API |

## Workflow Nodes

```
Weekly Trigger (Friday 5pm)
    → Set Variables (repo, language, webhook_url)
    → Fetch Commits / Fetch Closed Issues / Fetch Merged PRs (parallel)
    → Merge GitHub Data (combine all results)
    → Generate Summary (Claude API)
    → Format Output (Discord webhook format)
    → Send to Discord
```

## Acceptance Criteria

- [x] Exportable n8n workflow (importable `.json` file)
- [x] Trigger: weekly cron (Friday at 5pm)
- [x] Fetches: commits, closed issues, merged PRs
- [x] Calls Claude API for narrative summary
- [x] Delivers via Discord webhook (Slack/email alternatives documented)
- [x] Configurable: repo, destination, language (EN/FR)
- [x] README with setup in 5 steps or fewer

## License

MIT
