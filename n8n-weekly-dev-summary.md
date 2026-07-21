# Weekly Dev Summary — n8n + Claude API

An n8n workflow that automatically generates a weekly narrative summary of a GitHub repo's activity using the Claude API.

## Requirements

- [n8n](https://docs.n8n.io) instance (self-hosted or cloud)
- [GitHub Personal Access Token](https://github.com/settings/tokens) (recommended for higher rate limits)
- [Claude API key](https://console.anthropic.com/) (model: claude-sonnet-4-20250514)
- [Discord webhook URL](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) or Slack webhook URL

## Setup (5 steps)

1. **Import the workflow** — In n8n, go to **Workflows → Add Workflow → ⋮ → Import from File** and select `n8n-weekly-dev-summary.json`.

2. **Configure credentials** — Open the **Set Variables** node and update the `repoOwner`, `repoName`, `language`, `claudeApiKey`, and `webhookUrl` fields.

3. **Set up GitHub auth** (optional) — Open each **GitHub API** node, set **Credentials → Header Auth**, and enter `Authorization` as header name with `Bearer <your-github-pat>` as the value.

4. **Test** — Click **Execute Workflow** to run it manually. Verify all nodes execute without errors.

5. **Activate** — Toggle **Active** on. The workflow runs every Friday at 5pm automatically.

## Configuration

| Variable       | Default     | Description                          |
|----------------|-------------|--------------------------------------|
| `repoOwner`    | `owner`     | GitHub organization or username      |
| `repoName`     | `repo`      | GitHub repository name               |
| `language`     | `EN`        | Summary language (`EN` or `FR`)      |
| `claudeApiKey` | —           | Anthropic Claude API key             |
| `webhookUrl`   | —           | Discord/Slack webhook destination    |

## How It Works

1. **Cron trigger** fires every Friday at 17:00
2. **Set Variables** loads configurable parameters
3. **3 GitHub API calls** fetch commits, closed issues, and merged PRs from the past week
4. **Merge nodes** combine the data into a single stream
5. **Claude API** (`claude-sonnet-4-20250514`) generates a narrative summary with sections: Key achievements, Challenges, Next week focus
6. **Webhook** delivers the summary to Discord or Slack
7. **Respond** returns a success confirmation

## Screenshot

*(Add a screenshot of a successful n8n execution here)*
