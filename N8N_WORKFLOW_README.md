# n8n + Claude Code Weekly Dev Summary Workflow

Automated weekly narrative summary of GitHub repository activity, powered by Claude API.

## Setup

1. Import `weekly-dev-summary.json` into your n8n instance (Settings → Import from File)
2. Configure credentials: Add GitHub API credential (`github-creds`) and Anthropic API credential (`anthropic-creds`)
3. Set workflow variables in the "Weekly Cron Trigger" node: `githubOwner`, `githubRepo`, `language` (EN/FR), `destinationEmail`
4. Activate the workflow — runs every Friday at 5pm UTC by default
5. Test manually via "Execute Workflow" button to verify email delivery

## How It Works

- **Trigger**: Weekly cron schedule (configurable)
- **Data Collection**: Fetches commits, closed issues, and merged PRs from GitHub API for the past 7 days
- **AI Summary**: Sends structured activity data to Claude (`claude-sonnet-4-20250514`) for narrative generation
- **Delivery**: Sends formatted HTML email summary to configured destination
- **Configurable**: Repository, language (EN/FR), and email destination are all set via workflow variables

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub API token with repo read access
- Anthropic API key with Claude access
- SMTP credentials for email delivery (or swap Send Email node for Discord/Slack webhook)

## Customization

- Change cron expression in "Weekly Cron Trigger" node for different schedule
- Swap "Send Email Summary" node for Discord/Slack webhook node if preferred
- Adjust Claude prompt in "Claude Generate Summary" node for different summary style
- Modify `since` date calculation in GitHub nodes for different time window
