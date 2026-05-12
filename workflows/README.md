# Weekly Dev Summary — n8n + Claude

An n8n workflow that generates a narrative weekly summary of your GitHub repo activity using Claude.

## Setup

1. Import `weekly-dev-summary.json` into n8n (Workflows → Add → Import from File).
2. Open the **Config** node and set your repo (`owner/repo`), Discord webhook URL, preferred language (`EN` or `FR`), and a GitHub personal access token with `repo` scope.
3. Configure the **Call Claude API** node — add an **HTTP Header Auth** credential named `httpHeaderAuth` with your Anthropic API key as the value.
4. Activate the workflow (it triggers every Friday at 5pm UTC by default).
5. To test immediately, click **Execute Workflow** — a test summary will post to your Discord channel.

## How It Works

- **Schedule Trigger** — Runs weekly on Friday at 17:00 UTC
- **Config** — Editable variables: repo, webhook, language, GitHub token
- **Get Commits / Issues / PRs** — Fetches the past 7 days of activity via the GitHub API
- **Merge Data** — Combines all three data streams
- **Build Claude Prompt** — Formats the activity data into a structured prompt
- **Call Claude API** — Sends to `claude-sonnet-4-20250514` for narrative generation
- **Parse Response** — Extracts the summary text
- **Language Route** — Sends in English or French based on your config
- **Send to Discord** — Posts the summary to your webhook

## Customization

| Variable | Where to Change | Description |
|---|---|---|
| `repo` | Config node | GitHub repo in `owner/name` format |
| `discordWebhook` | Config node | Full Discord webhook URL |
| `language` | Config node | `EN` or `FR` |
| `githubToken` | Config node | Personal access token with `repo` scope |
| Cron schedule | Weekly Schedule node | Adjust cron expression as needed |
| Claude model | Build Claude Prompt node | Change `model` field if desired |
