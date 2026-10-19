# n8n Weekly Dev Summary

## Setup (5 steps)
1. Import `workflow.json` into n8n.
2. Set credentials: GitHub (token), Anthropic (x-api-key via httpHeaderAuth), Slack webhook.
3. Set variables: `repoOwner`, `repoName`, `slackChannel`, `language` (EN/FR).
4. Activate the workflow; it runs every Friday 5pm.
5. Verify first execution in n8n executions tab.

## Notes
- Tested on n8n self-hosted; screenshot not included in this PR.
- Delivery via Slack; can be swapped for email node.
