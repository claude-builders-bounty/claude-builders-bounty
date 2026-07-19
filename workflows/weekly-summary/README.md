# Weekly GitHub Summary Workflow

An n8n workflow that generates a weekly narrative summary of GitHub activity using Claude API.

## Setup

1. Import `weekly-github-summary.json` into n8n
2. Set environment variables:
   - `GITHUB_OWNER` — Repository owner
   - `GITHUB_REPO` — Repository name
   - `CLAUDE_API_KEY` — Anthropic API key
   - `WEBHOOK_URL` — Slack/Discord webhook or email API
   - `LANGUAGE` — Optional: `EN` (default) or `FR`
3. Configure GitHub credentials in n8n
4. Activate the workflow

## Schedule

Runs weekly on Friday at 5 PM (configurable).

## Output

Narrative summary delivered to your webhook (Slack, Discord, or email).
