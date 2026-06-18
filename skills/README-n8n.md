# Weekly Dev Summary Workflow (n8n + Claude)

An exportable n8n workflow that generates a weekly narrative summary of repository activity using Claude 3 Sonnet.

## Setup
1. Import `weekly_dev_summary_workflow.json` into your n8n instance.
2. Configure credentials for GitHub and Anthropic.
3. Set your `repo_owner`, `repo_name`, and Discord/Slack `webhook_url`.

## Features
- Weekly cron trigger (Friday 5 PM).
- Narrative summary generation via Claude API.
- Multi-channel delivery support.
