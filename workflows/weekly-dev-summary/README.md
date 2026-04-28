# Weekly GitHub Activity Summary (n8n + Claude) 📊

An n8n workflow that automatically generates a narrative weekly summary of a GitHub repository's activity using Claude AI and delivers it via Discord/Slack webhook.

## Features
- **Automated**: Runs weekly via cron trigger.
- **Data-Driven**: Fetches commits and closed issues from the past 7 days.
- **AI-Powered**: Uses Claude (`claude-sonnet-4-20250514`) to write a professional narrative.
- **Configurable**: Easily set your repo, destination, and language (EN/FR).

## Setup Instructions

1. **Import Workflow**: Download `workflow.json` and import it into your n8n instance.
2. **Configure Credentials**:
    - Add your **GitHub Personal Access Token** to the GitHub nodes.
    - Add your **Anthropic API Key** to the Anthropic node.
3. **Set Variables**:
    - Open the `Config` node and update the `owner`, `repo`, `language`, and `destination_webhook` values.
4. **Activate**: Toggle the workflow to "Active".

## Delivery
The workflow is configured to send the summary as a POST request to a Discord or Slack webhook. Ensure the payload format matches your destination's requirements (default is Discord `content` field).
