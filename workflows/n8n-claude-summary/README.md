# n8n Weekly Dev Summary Workflow

An automated n8n workflow that fetches GitHub repository activity (commits, closed issues, merged PRs) for the past 7 days, syntheizes a narrative summary using Claude 3.5 Sonnet, and pushes it to a Discord or Slack webhook.

## Setup Instructions

1. **Import Workflow**: Open your n8n workspace, click "Add new workflow", then select `Import from file` and upload `n8n-weekly-summary.json`.
2. **Configure Triggers**: Click on the `Schedule Trigger` node. Add the following parameters to the node's JSON context:
   - `repo`: The repository slug (e.g., `owner/repo`)
   - `webhook_url`: Your Discord/Slack Webhook URL
   - `language`: The language of the summary (e.g., `EN` or `FR`)
3. **Configure Credentials**:
   - For GitHub Nodes: Create a `Header Auth` credential (`Authorization: Bearer YOUR_GITHUB_TOKEN`) to avoid rate limits.
   - For Claude Node: Create a `Header Auth` credential (`x-api-key: YOUR_ANTHROPIC_KEY`, along with `anthropic-version: 2023-06-01`).
4. **Activate**: Toggle the workflow switch to **Active** (Top Right).

By default, the cron runs every Friday at 17:00. This is structurally complete and validated against the Anthropic and GitHub APIs.
