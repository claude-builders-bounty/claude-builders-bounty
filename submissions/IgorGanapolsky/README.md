# n8n Weekly Dev Summary Workflow

This workflow automatically generates a narrative summary of your GitHub repository activity every Friday at 5 PM using the Claude API.

## Setup Instructions (5 Steps)

1. **Import Workflow**: Import the `github-weekly-summary.json` file into your n8n instance.
2. **Configure Variables**: Open the "Set Variables" node (or add a Set node) and provide your:
   - `GITHUB_REPO_OWNER`
   - `GITHUB_REPO_NAME`
   - `WEBHOOK_URL` (Discord or Slack)
   - `LANGUAGE` (EN or FR)
3. **Connect Credentials**: Ensure your **GitHub** and **Anthropic** (Claude) credentials are connected to their respective nodes.
4. **Test Run**: Click "Execute Workflow" to verify the narrative generation and delivery.
5. **Activate**: Toggle the workflow to "Active" to enable the weekly Friday schedule.

## Features
- Narrative summary of commits and closed issues.
- Weekly automated heartbeat.
- Multi-language support (EN/FR).
- Pluggable delivery via Discord or Slack webhooks.
