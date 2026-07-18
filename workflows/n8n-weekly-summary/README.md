# n8n Weekly Dev Summary Workflow

Automatically generates a weekly narrative summary of GitHub repo activity using Claude API.

## Setup

1. Import `weekly-summary.json` into n8n
2. Set environment variables:
   - `GITHUB_ACCESS_TOKEN` - GitHub personal access token
   - `CLAUDE_API_KEY` - Anthropic API key
   - `RECIPIENT_EMAIL` - where to send the summary
3. Configure repository owner/name in the GitHub nodes
4. Activate the workflow

## Schedule

Triggers every Friday at 5 PM.
