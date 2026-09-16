# Weekly Dev Summary with n8n and Claude

This n8n workflow automatically generates a weekly narrative summary of a GitHub repository's activity using the Claude API, and posts it to Discord. It's triggered every Friday at 5:00 PM.

## Setup Instructions (5 Steps)

1. **Import Workflow**: Download `workflow.json` from this repository and import it into your n8n instance using the "Import from File" option.
2. **Configure Credentials**: Open the imported workflow and set up credentials for both the **GitHub API** node and the **Anthropic Claude** node with your respective tokens.
3. **Set Environment Variables**: Set the following environment variables in your n8n environment:
   - `GITHUB_REPO`: The repository to track (e.g., `owner/repo`)
   - `LANGUAGE`: Language for the summary (e.g., `EN` or `FR`)
   - `DISCORD_WEBHOOK_URL`: Your Discord channel's webhook URL
4. **Test the Workflow**: Click "Execute Workflow" to do a manual test run and verify that the summary is generated and sent to Discord successfully.
5. **Activate**: Toggle the workflow switch to "Active" so the schedule trigger will run automatically every Friday at 5:00 PM.

## Configurable Variables
- `GITHUB_REPO`: `owner/repo`
- `LANGUAGE`: `EN` or `FR`
- `DISCORD_WEBHOOK_URL`: The webhook URL for delivery.
