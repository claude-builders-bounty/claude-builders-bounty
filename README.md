# Weekly Dev Summary Workflow

Automated weekly development summary generator using n8n and Claude API.

## Features

- **Trigger**: Every Friday at 5pm (cron: `0 17 * * 5`)
- **Fetches**: Commits, merged PRs, and closed issues from the past week
- **AI Summary**: Uses Claude Sonnet 4 to generate narrative summaries
- **Delivery**: GitHub Gist, Email, or Discord webhook
- **Configurable**: Supports GitHub repo, language (EN/FR), and destination

## Setup (5 Steps)

### 1. Import Workflow
Open n8n → Settings → Import → Upload `workflows/weekly-dev-summary.json`

### 2. Configure Environment Variables
Create these credentials in n8n:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO` | Repository path | `owner/repo-name` |
| `ANTHROPIC_API_KEY` | Your Anthropic API key | `sk-ant-...` |
| `DISCORD_WEBHOOK_URL` | Discord webhook (optional) | `https://discord.com/api/webhooks/...` |
| `LANGUAGE` | Summary language | `EN` or `FR` |

### 3. Connect GitHub Credential
Create a GitHub API credential in n8n with a Personal Access Token (repo scope).

### 4. Test the Workflow
Click "Test Workflow" to verify all nodes work correctly.

### 5. Activate
Toggle the workflow ON to enable weekly execution.

## Output

The workflow generates a Markdown summary including:
- Total commits, merged PRs, and closed issues
- Top contributors by commit count
- List of merged PRs and closed issues
- Key changes grouped by theme
- Suggested focus areas for next week

## Customization

- **Schedule**: Modify the cron expression in the schedule trigger node
- **Delivery**: Disable unused output nodes (Email, Gist, Discord)
- **SUMMARY_LANGUAGE env var to `FR` for French summaries

## License

MIT


