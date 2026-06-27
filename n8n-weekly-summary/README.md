# Weekly GitHub Dev Summary — n8n + Claude Workflow

Automatically generates a narrative weekly summary of your GitHub repo's activity and posts it to Discord every Friday at 5PM.

## What it does

Every week the workflow:
1. Fetches commits, closed issues, and merged PRs from the past 7 days via GitHub API
2. Sends the data to Claude (`claude-sonnet-4-20250514`) with a structured prompt
3. Posts the AI-generated narrative summary as a Discord embed

## Setup — 5 steps

### Step 1 — Import the workflow

1. Open your n8n instance → **Workflows** → **Import from File**
2. Select `workflow.json`
3. The workflow opens in the editor

### Step 2 — Create credentials

You need two credentials (both are **HTTP Header Auth** type):

**GitHub Token** (`id: github-token-cred`):
- Name: `GitHub Token`
- Name (header): `Authorization`
- Value: `Bearer ghp_YOUR_GITHUB_PERSONAL_ACCESS_TOKEN`
- Required scopes: `repo` (read access to commits, issues, PRs)

**Anthropic API Key** (`id: anthropic-key-cred`):
- Name: `Anthropic API Key`
- Name (header): `x-api-key`
- Value: `sk-ant-YOUR_API_KEY`

Assign each credential to its respective HTTP Request node.

### Step 3 — Configure the `Config Variables` node

Open the **Config Variables** node and set:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO` | `owner/repo` to summarize | `octocat/Hello-World` |
| `LANGUAGE` | Summary language: `EN` or `FR` | `EN` |
| `DISCORD_WEBHOOK_URL` | Discord Incoming Webhook URL | `https://discord.com/api/webhooks/...` |
| `CLAUDE_MODEL` | Claude model ID | `claude-sonnet-4-20250514` |

### Step 4 — Create a Discord webhook

1. In Discord: **Server Settings** → **Integrations** → **Webhooks** → **New Webhook**
2. Choose the channel, copy the webhook URL
3. Paste into `DISCORD_WEBHOOK_URL` in the Config Variables node

### Step 5 — Activate

Toggle the workflow to **Active**. It will fire every Friday at 5PM (server timezone).

To test immediately: click **Test workflow** in n8n — this runs the full flow without waiting for the cron.

---

## Workflow architecture

```
Schedule Trigger (Friday 5PM)
        │
   Config Variables
        │
  Calculate Date Range
   ┌────┼────┐
   │    │    │
Commits Issues PRs   ← parallel GitHub API calls
   └────┼────┘
        │
  Format Data for Claude  ← builds prompt with all 3 data sources
        │
  Call Claude API         ← claude-sonnet-4-20250514, max 1024 tokens
        │
  Format Discord Embed    ← builds rich embed with stats footer
        │
  Post to Discord         ← sends to configured webhook
```

## Sample output

The Discord embed looks like this:

> **📊 Weekly Dev Summary — your-org/your-repo**
>
> This week the team shipped 14 commits across 6 merged PRs, with a strong focus on performance and reliability improvements. The standout change was the database connection pooling overhaul (#142), which reduces P99 query latency by ~40% according to the load test results in PR #143.
>
> On the issues front, 5 long-standing bugs were closed, including the notorious race condition in the job scheduler (#89, open for 3 months) and several edge cases in the CSV export feature. Notably, @alice led four of these closures single-handedly.
>
> Documentation had a good week too — the API reference was updated to cover the new pagination format, and the Docker Compose setup guide was rewritten from scratch (#PR147). New contributors should find onboarding significantly smoother.
>
> Looking ahead, several open issues around authentication refactoring suggest next week will bring more structural changes. The team seems to be building toward something bigger.
>
> *Week of 2026-06-20 – 2026-06-27 · 14 commits · 6 PRs merged · 5 issues closed*

## Language support

Set `LANGUAGE` to `FR` in the Config Variables node to receive the summary in French. The prompt instructs Claude to reply entirely in the selected language.

## Customization

- **Trigger time**: Edit the **Weekly Trigger** node → change day (0=Sunday … 6=Saturday) and hour
- **More delivery targets**: Duplicate the `Post to Discord` node and change the URL to a Slack webhook — the payload format differs (Slack uses `text` or `blocks`). A Slack variant is documented below.
- **Summary length**: Edit the Code node → change `400 words` in the prompt to your preference
- **Commit cap**: The `Format Data for Claude` node limits to 30 commits and 20 PRs/issues to stay within context. Adjust the `.slice()` calls for larger repos.

### Slack delivery (alternative)

Replace the `Post to Discord` node with an HTTP Request to your Slack Incoming Webhook URL, with this body:

```json
{
  "text": "*📊 Weekly Dev Summary — {{ repo }}*\n{{ summary }}",
  "unfurl_links": false
}
```

Or use Slack Block Kit for a richer layout.
