# n8n Weekly GitHub Dev Summary

This workflow generates a weekly narrative summary of a GitHub repository using Claude and sends it to Slack or Discord through a webhook.

## What It Does

- Runs every Friday at 17:00.
- Fetches weekly GitHub activity: commits, closed issues, and merged PRs.
- Calls Claude with `claude-sonnet-4-20250514`.
- Produces a narrative summary in English or French.
- Delivers the summary to Slack or Discord via webhook.

## Setup In 5 Steps

1. Import `workflows/n8n-weekly-dev-summary.json` into n8n.
2. Set environment variables:

   ```bash
   N8N_BLOCK_ENV_ACCESS_IN_NODE=false
   GITHUB_REPO=owner/repo
   GITHUB_TOKEN=github_pat_or_token
   ANTHROPIC_API_KEY=sk-ant-...
   DESTINATION_WEBHOOK_URL=https://hooks.slack.com/services/... # or Discord webhook
   SUMMARY_LANGUAGE=EN # EN or FR
   ```

3. Open the workflow and run **Execute workflow** once manually.
4. Confirm the generated summary appears in your Slack or Discord channel.
5. Activate the workflow.

## Configuration

| Variable | Required | Description |
| --- | --- | --- |
| `GITHUB_REPO` | yes | Repository in `owner/repo` format. |
| `GITHUB_TOKEN` | yes | Token with public repo access, or private repo access if needed. |
| `ANTHROPIC_API_KEY` | yes | Claude API key. |
| `DESTINATION_WEBHOOK_URL` | no | Slack or Discord webhook URL. If empty, the workflow returns the summary without sending. |
| `SUMMARY_LANGUAGE` | no | `EN` or `FR`. Defaults to `EN`. |
| `N8N_BLOCK_ENV_ACCESS_IN_NODE` | yes | Set to `false` so n8n Code nodes can read the workflow environment variables. |

## Output

The delivered message includes:

- Executive summary.
- Important merged PRs.
- Notable closed issues.
- Development themes and risks.
- Suggested focus for next week.
- Metrics footer with commit, PR, and issue counts.

See `workflows/weekly-dev-summary/sample-output.md` for an example.

## Notes

- The workflow is inactive by default after import.
- The GitHub Search API is used for closed issues and merged PRs.
- The webhook payload includes both `text` and `content`, so the same node works for Slack and Discord.
