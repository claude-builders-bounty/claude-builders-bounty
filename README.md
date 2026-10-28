# Weekly GitHub Dev Summary n8n Workflow

Automatically generates a weekly narrative summary of a GitHub repository's activity using Claude API and delivers it via email or Discord/Slack webhook.

## Features

- **Weekly Trigger**: Runs every Friday at 5pm via cron schedule
- **GitHub Data**: Fetches commits, closed issues, and merged PRs from the past week
- **AI Summary**: Uses Claude Sonnet 4 (`claude-sonnet-4-20250514`) to generate narrative summaries
- **Flexible Delivery**: Send via email OR Discord/Slack webhook
- **Configurable**: Set GitHub repo, destination, and language (EN/FR)

## Setup Instructions (5 steps or fewer)

### Step 1: Import Workflow
1. Open your n8n instance
2. Go to Workflows > Import from File
3. Select `weekly-dev-summary-workflow.json`

### Step 2: Configure Credentials
Set up the following credentials in n8n:
- **GitHub API** - For fetching repository data
- **Anthropic API** - For Claude API access
- **SMTP/Email** (optional) - For email delivery

### Step 3: Set Variables
Configure these workflow variables:
- `githubRepo` - Repository in format `owner/repo` (e.g., `facebook/react`)
- `language` - `EN` or `FR` for summary language
- `destinationEmail` - Email address for delivery (if using email)
- `webhookUrl` - Discord/Slack webhook URL (if using webhook)

### Step 4: Test the Workflow
1. Click "Execute Workflow" manually to test
2. Check your email or webhook for the summary
3. Take a screenshot of successful execution

### Step 5: Activate
Enable the workflow to run automatically every Friday at 5pm.

## Resources

- [n8n Documentation](https://docs.n8n.io)
- [Claude API Documentation](https://docs.anthropic.com)
- [GitHub API Documentation](https://docs.github.com/en/rest)

## Notes

- The workflow fetches merged PRs from the last 100 closed PRs
- Claude API key required with access to `claude-sonnet-4-20250514`
- For Discord webhooks, use the webhook URL from your channel settings
- For Slack webhooks, use incoming webhook URL
