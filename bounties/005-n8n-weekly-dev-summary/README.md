# n8n Weekly Dev Summary Workflow

Importable n8n workflow that creates a weekly narrative summary of GitHub repository activity with the Claude Messages API and posts it to Discord.

## Setup

1. Import `workflows/weekly-dev-summary.json` into n8n.
2. Set environment variables: `GITHUB_REPO=owner/repo`, `GITHUB_TOKEN=...`, `CLAUDE_API_KEY=...`, `DESTINATION_WEBHOOK_URL=...`, and `SUMMARY_LANGUAGE=EN` or `FR`.
3. Run the workflow manually once and verify the Discord message.
4. Enable the workflow; it runs every Friday at 5pm.
5. Optional: adjust the Schedule Trigger timezone in n8n instance settings if your server timezone is not the desired reporting timezone.

## What It Does

- Uses a weekly Schedule Trigger.
- Fetches commits, closed issues, and merged pull requests from the GitHub API for the previous 7 days.
- Calls Claude with `claude-sonnet-4-20250514` to generate an English or French narrative summary.
- Posts the summary to a Discord webhook.

## Configuration

- `GITHUB_REPO`: GitHub repository in `owner/repo` format.
- `GITHUB_TOKEN`: GitHub token for API rate limits and private repositories.
- `CLAUDE_API_KEY`: Anthropic API key for the Claude Messages API.
- `DESTINATION_WEBHOOK_URL`: Discord webhook URL. The Discord channel is determined by the webhook.
- `SUMMARY_LANGUAGE`: `EN` or `FR`.

## Verification

Run the JSON smoke check:

```bash
python3 tests/check_workflow.py
```

See `docs/successful-execution.md` for the expected node-by-node result and the local environment limitation that prevented attaching a real n8n execution screenshot here.
