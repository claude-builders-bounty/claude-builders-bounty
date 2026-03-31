# Weekly Dev Summary — n8n + Claude API Workflow

Automatically generates a narrative weekly summary of any GitHub repository's activity using Claude (`claude-sonnet-4-20250514`) and delivers it to Discord or Slack.

## What It Does

Every Friday at 5 PM (configurable), this workflow:

1. **Fetches** the past 7 days of commits, closed issues, and merged PRs from the GitHub API
2. **Sends** the raw data to the Claude API with a structured prompt
3. **Delivers** a well-formatted narrative summary to your Discord or Slack channel via webhook

## Setup (5 Steps)

### 1. Import the Workflow

- Open your n8n instance → **Workflows** → **Add Workflow** → **Import from File**
- Select `weekly-dev-summary-workflow.json`

### 2. Set Environment Variables

Go to **Settings** → **Environment Variables** and add:

| Variable | Description |
|---|---|
| `GITHUB_TOKEN` | GitHub Personal Access Token ([create one here](https://github.com/settings/tokens)) — needs `repo` scope for private repos, or no scope for public repos |
| `CLAUDE_API_KEY` | Anthropic API key ([get one here](https://console.anthropic.com/settings/keys)) |

### 3. Configure Your Repository

Open the **Set Config** node and edit:

| Field | Default | Description |
|---|---|---|
| `repo_owner` | `n8n-io` | GitHub organization or username |
| `repo_name` | `n8n` | Repository name |
| `language` | `EN` | Summary language: `EN` (English) or `FR` (French) |
| `webhook_url` | — | Your Discord or Slack incoming webhook URL |

### 4. Get Your Webhook URL

**Discord:** Server Settings → Integrations → Webhooks → New Webhook → Copy URL

**Slack:** Create an [Incoming Webhook](https://api.slack.com/messaging/webhooks) → Copy the URL
> Note: For Slack, the payload format is slightly different. Change the `Send to Discord/Slack` node's JSON body to use `"text"` instead of `"content"`:
> ```json
> { "text": "📊 **Weekly Dev Summary** ..." }
> ```

### 5. Activate the Workflow

- Click the **Active** toggle in the top-right corner of the workflow editor
- The workflow will run automatically every Friday at 5 PM
- To test immediately: click **Test Workflow**

## Workflow Diagram

```
┌─────────────┐    ┌────────────┐    ┌───────────────────┐
│  Cron Trigger├───►│ Set Config ├──┬►│ Fetch Commits     │
│  (Fri 5 PM) │    └────────────┘  │ └────────┬──────────┘
│              │                    │          │
└──────────────┘                    ├►┌────────▼──────────┐
                                   │ │Fetch Closed Issues │
                                   │ └────────┬──────────┘
                                   │          │
                                   └►┌────────▼──────────┐
                                     │ Fetch Merged PRs   │
                                     └────────┬──────────┘
                                              │
                                     ┌────────▼──────────┐
                                     │  Aggregate Data    │
                                     └────────┬──────────┘
                                              │
                                     ┌────────▼──────────┐
                                     │  Claude API Call   │
                                     │ (claude-sonnet-4)  │
                                     └────────┬──────────┘
                                              │
                                     ┌────────▼──────────┐
                                     │  Extract Summary   │
                                     └────────┬──────────┘
                                              │
                                     ┌────────▼──────────┐
                                     │ Send to Discord/   │
                                     │ Slack Webhook      │
                                     └──────────────────┘
```

## Configurable Variables

| Variable | Location | Options |
|---|---|---|
| **Target repo** | Set Config node | Any public or private GitHub repo |
| **Language** | Set Config node | `EN` (English), `FR` (French) |
| **Delivery** | Set Config node | Discord webhook URL or Slack webhook URL |
| **Schedule** | Trigger node | Any cron expression (default: Friday 5 PM) |
| **Claude model** | Claude API node | Any Anthropic model (default: `claude-sonnet-4-20250514`) |

## Example Output

> 📊 **Weekly Dev Summary — n8n-io/n8n**
> 2026-03-21 → 2026-03-28
>
> This was a productive week for the n8n project with 47 commits landed across the codebase. The team focused primarily on node improvements and bug fixes...
>
> **Key Highlights:**
> - New Notion node with support for database queries (#8234)
> - Fixed critical memory leak in webhook processing (#8201)
> - Improved error messages across 12 nodes
>
> ---
> 📈 *47 commits · 8 issues closed · 12 PRs merged*

## License

MIT
