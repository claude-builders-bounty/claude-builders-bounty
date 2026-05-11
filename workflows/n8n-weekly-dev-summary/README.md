# n8n Weekly Dev Summary

This implements bounty #5 with an importable n8n workflow that summarizes weekly GitHub repository activity using the Claude API and posts the result to Discord.

## Setup

1. Import `weekly-dev-summary.json` into n8n.
2. Add a GitHub credential named by the HTTP Request nodes and set `ANTHROPIC_API_KEY` in the n8n environment.
3. Update the `Config` node with `repoOwner`, `repoName`, `destinationWebhookUrl`, and `language` (`EN` or `FR`).
4. Run the workflow manually once to verify the Discord delivery.
5. Activate the workflow for the Friday 5pm weekly schedule.

## What It Does

- Triggers every Friday at 5pm.
- Fetches commits, closed issues, and closed pull requests from the GitHub API for the last 7 days.
- Filters pull requests to merged PRs in the weekly window.
- Calls Claude API model `claude-sonnet-4-20250514` to write a narrative summary.
- Posts the generated summary to a Discord webhook.

## Configurable Variables

- `repoOwner`: GitHub repository owner.
- `repoName`: GitHub repository name.
- `destinationWebhookUrl`: Discord webhook URL.
- `language`: `EN` or `FR`.

## Verification

The JSON has been syntax-checked with:

```bash
python -m json.tool workflows/n8n-weekly-dev-summary/weekly-dev-summary.json
```

I could not capture a real n8n execution screenshot in this environment because no n8n instance is installed here. The workflow is structured for direct import and manual execution in n8n.
