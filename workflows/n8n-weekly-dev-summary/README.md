# n8n Weekly Dev Summary Workflow

Automated weekly narrative summary of a GitHub repo's activity, powered by n8n and Claude API.

## Setup (5 steps)

1. **Import the workflow**: In n8n, go to *Workflows → Import from File* and select `weekly-dev-summary.json`.

2. **Set credentials**: Add your GitHub Personal Access Token, Claude API key, and webhook URL (Discord/Slack) in n8n *Settings → Credentials*.

3. **Configure variables**: Open the workflow and edit the *Set Variables* node:
   - `repoOwner` / `repoName` — target GitHub repository
   - `webhookUrl` — Discord or Slack incoming webhook URL
   - `language` — `EN` or `FR`

4. **Activate the workflow**: Toggle the workflow to *Active* in n8n. It runs automatically every Friday at 5 PM UTC.

5. **Verify execution**: Check the n8n *Executions* tab for a green checkmark, or your Discord/Slack channel for the summary.

## Delivery

- **Discord**: Uses a Discord webhook with embed formatting.
- **Slack**: Uses a Slack incoming webhook with block formatting.

Set your preferred `webhookUrl` in the *Set Variables* node.

## Workflow Overview

