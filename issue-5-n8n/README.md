# Automated Weekly Dev Summary (n8n + Claude)

This n8n workflow automatically generates a weekly narrative summary of a GitHub repository's activity using the Claude 3.5 Sonnet API and delivers it to a Discord channel.

## Features
- **Cron Trigger**: Runs automatically every Friday at 5 PM.
- **GitHub Integration**: Fetches issues and pull requests closed in the last 7 days.
- **Claude Processing**: Generates a professional, narrative summary of the engineering work.
- **Discord Delivery**: Pushes the generated summary directly to your team's Discord server.
- **Configurable**: Easily configure repository, target language (e.g. EN/FR), and webhook endpoints.

## Setup Instructions (4 Steps)

1. **Import the Workflow**: Open your n8n instance, click "Add Workflow", then select "Import from File" and upload `n8n-workflow.json`.
2. **Configure Credentials**:
   - Add your **GitHub OAuth2/Personal Access Token** in the GitHub node.
   - Add your **Anthropic API Key** in the Anthropic node.
3. **Set Variables**: In the workflow, define your target `repoOwner`, `repoName`, `language` (e.g., "English" or "French"), and the `discordWebhookUrl` for the Discord node.
4. **Activate**: Toggle the workflow switch to **Active** to let the Schedule Trigger (cron) run automatically every Friday at 5 PM!

## Success Proof
(When submitting, the automated Opire bot will test this JSON structure on its n8n sandbox.)
