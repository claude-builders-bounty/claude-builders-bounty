# n8n Weekly Dev Summary Workflow

Automated weekly narrative summary of GitHub repo activity using Claude API.

## Features

- Weekly cron trigger (Friday 5pm)
- Fetches commits, closed issues, merged PRs from the past week
- Generates narrative summary using Claude (claude-sonnet-4-20250514)
- Delivers via Discord webhook
- Configurable repo, language, and destination

## Setup (5 steps)

1. **Import workflow**: In n8n, go to Workflows → Import → paste `weekly-dev-summary.json`

2. **Set environment variables** (Settings → Variables):
   - `GITHUB_REPO`: `owner/repo` (e.g., `facebook/react`)
   - `ANTHROPIC_API_KEY`: Your Anthropic API key
   - `DISCORD_WEBHOOK_URL`: Your Discord webhook URL
   - `SUMMARY_LANGUAGE`: `EN` or `FR` (default: EN)

3. **Create GitHub credential**:
   - Credentials → Add → Header Auth
   - Name: `GitHub Token`
   - Header Name: `Authorization`
   - Header Value: `token YOUR_GITHUB_TOKEN`

4. **Activate workflow**: Toggle the workflow to Active

5. **Test**: Click "Execute Workflow" to run immediately

## Configuration Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_REPO` | Yes | - | Repository in `owner/repo` format |
| `ANTHROPIC_API_KEY` | Yes | - | Anthropic API key |
| `DISCORD_WEBHOOK_URL` | Yes | - | Discord webhook for delivery |
| `SUMMARY_LANGUAGE` | No | `EN` | Summary language (`EN` or `FR`) |

## Delivery Options

### Discord (Default)
Already configured. Just set `DISCORD_WEBHOOK_URL`.

### Slack
Replace the Discord node with Slack node:
- Use Slack Incoming Webhook
- Set `SLACK_WEBHOOK_URL` environment variable

### Email
Replace Discord node with Email node:
- Configure SMTP credentials
- Set recipient in node settings

## Workflow Nodes

1. **Weekly Trigger**: Cron schedule (Friday 5pm)
2. **Fetch Commits**: GitHub API - commits from last 7 days
3. **Fetch Closed Issues**: GitHub API - recently closed issues
4. **Fetch Merged PRs**: GitHub API - recently merged PRs
5. **Merge Data**: Combine all GitHub data
6. **Process Data**: Extract relevant fields, calculate stats
7. **Generate Summary**: Claude API call with structured prompt
8. **Extract Summary**: Parse Claude response
9. **Send to Discord**: Post formatted message

## Sample Output

> **📊 Weekly Dev Summary: facebook/react**
>
> ## This Week in React
>
> It's been a productive week for the React team! Here's what happened:
>
> ### Highlights
> - **12 commits** pushed to main
> - **5 issues** closed
> - **3 PRs** merged
>
> ### Notable Changes
> The team focused on performance improvements this week, with several commits optimizing the reconciler...

## License

MIT
