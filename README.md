# Weekly GitHub Summary — n8n Workflow

Automated weekly narrative summary of GitHub repository activity using Claude API.

## Setup (5 Steps)

1. **Import Workflow**: In n8n, go to Workflows → Import from File → select `Weekly_GitHub_Summary.json`
2. **Configure Credentials**: Add HTTP Header Auth credential named "GitHub Token" with your GitHub PAT (needs `repo` scope)
3. **Add Anthropic Credential**: Add OpenAI-compatible credential named "Anthropic API" with base URL `https://api.anthropic.com/v1` and your Anthropic API key
4. **Set Environment Variables**: In n8n Settings → Environment Variables, add:
   - `GITHUB_REPO` = `owner/repo-name`
   - `WEBHOOK_URL` = Discord/Slack webhook URL
   - `SUMMARY_LANGUAGE` = `EN` or `FR`
5. **Activate**: Toggle the workflow ON. It runs every Friday at 5pm UTC.

## Delivery

Summaries are sent via Discord/Slack webhook. To use email instead, replace the "Send to Discord/Slack" node with an Email Send node and configure SMTP credentials.

## Model

Uses `claude-sonnet-4-20250514` via Anthropic's OpenAI-compatible endpoint.

## Testing

Click "Execute Workflow" manually in n8n to test immediately. Ensure all credentials are valid and environment variables are set.
