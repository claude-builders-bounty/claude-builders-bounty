# Weekly Dev Summary n8n Workflow

Automatically generate and deliver a weekly narrative summary of a GitHub repository's activity using the Claude API (`claude-sonnet-4-20250514`).

## Setup Instructions

1. **Import Workflow:** Open your n8n instance, click "Add Workflow", and select "Import from File" to load `workflow.json`.
2. **Configure Variables:** Double-click the "Config Variables" node and set your `github_repo` (e.g., `claude-builders-bounty/claude-builders-bounty`), `language` (e.g., `EN` or `FR`), and your Discord/Slack `webhook_url`.
3. **Set API Key:** Open the "Claude API Call" node, navigate to the Headers section, and replace `YOUR_ANTHROPIC_API_KEY_HERE` with your actual Anthropic API key.
4. **Activate Trigger:** Adjust the "Schedule Trigger" node if needed (defaults to Fridays at 5 PM), and toggle the workflow to "Active".
5. **Execute:** Click "Execute Workflow" at the bottom of the screen to manually test the integration and verify delivery.
