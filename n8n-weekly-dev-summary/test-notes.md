# Test Notes

Validated the workflow JSON with `jq`.

Expected manual run path in n8n:

1. Cron/manual trigger starts the flow.
2. The setup node computes the 7-day ISO timestamp window and reads repo variables.
3. GitHub HTTP nodes fetch commits, closed issues, and merged pull requests.
4. The prompt node builds a compact activity payload.
5. Claude generates a narrative summary with `claude-sonnet-4-20250514`.
6. Slack webhook receives the generated text.

The workflow is credentialized through environment variables and n8n workflow variables so it can be imported without editing node internals.
