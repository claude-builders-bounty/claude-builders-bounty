# n8n Weekly GitHub Summary

Automatically generate a narrative weekly summary of your GitHub repository activity using Claude AI and send it to Discord/Slack.

## Quick Start

1. **Import workflow**: Open n8n, go to Workflows → Import from File → select `workflow.json`.
2. **Configure variables**: Edit the "Configuration" node with your:
   - GitHub repo (e.g., `owner/repo`)
   - GitHub personal access token
   - Claude API key
   - Webhook URL (Discord/Slack)
   - Language preference (EN/FR)
3. **Activate workflow**: Toggle the workflow to Active.
4. **Test**: Manually execute once to verify all connections work.
5. **Schedule**: The workflow runs every Friday at 5 PM (cron: `0 17 * * 5`).

## Configuration Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO` | Repository to track | `octocat/Hello-World` |
| `GITHUB_TOKEN` | GitHub personal access token (repo scope) | `ghp_xxxxxxxxxxxx` |
| `CLAUDE_API_KEY` | Anthropic API key | `sk-ant-xxxxxxxxxx` |
| `WEBHOOK_URL` | Discord or Slack webhook URL | `https://discord.com/api/webhooks/...` |
| `WEBHOOK_TYPE` | Webhook platform (`discord` or `slack`) | `discord` |
| `LANGUAGE` | Summary language (`EN` or `FR`) | `EN` |

## How It Works

1. **Trigger**: Runs weekly on Friday at 5 PM.
2. **GitHub API**: Fetches commits, closed issues, and merged PRs from the past week.
3. **Claude AI**: Generates a narrative summary in your chosen language.
4. **Webhook**: Sends the formatted summary to your Discord/Slack channel.

## Screenshot

![Workflow Overview](screenshot.png)

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub personal access token with `repo` scope
- Anthropic API key (Claude)
- Discord or Slack webhook URL

## License

MIT