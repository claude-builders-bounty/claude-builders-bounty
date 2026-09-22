# n8n Weekly Dev Summary Workflow

Automatically generates a weekly narrative summary of GitHub repo activity using Claude API.

## Setup (5 steps)

1. Import the workflow JSON into your n8n instance
2. Set environment variables: GITHUB_TOKEN, ANTHROPIC_API_KEY
3. Configure workflow variables: GITHUB_REPO, WEBHOOK_URL
4. Set cron trigger to Friday 5pm
5. Test with a manual execution

## Files

- workflows/weekly-dev-summary.json - Importable n8n workflow
