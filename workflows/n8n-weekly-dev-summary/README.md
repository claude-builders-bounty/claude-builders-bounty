# n8n Weekly Dev Summary

Importable n8n workflow that generates a weekly narrative summary of GitHub repository activity with Claude and sends it to a Discord webhook.

## Setup

1. Import `weekly-dev-summary.json` into n8n.
2. Configure these workflow variables: `GITHUB_REPO`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `DISCORD_WEBHOOK_URL`, and `SUMMARY_LANGUAGE`.
3. Set `GITHUB_REPO` to `owner/repo` and `SUMMARY_LANGUAGE` to `EN` or `FR`.
4. Run the workflow manually once and confirm the Discord message lands.
5. Activate the workflow for the Friday 17:00 cron trigger.

## What It Fetches

- Commits from the last 7 days.
- Closed issues from the last 7 days.
- Closed PRs from the last 7 days, filtered to merged PRs before summarization.

## Validation

Run:

```bash
python3 validate_workflow.py
python3 -m json.tool weekly-dev-summary.json >/dev/null
```

The JSON is structurally validated for the expected cron, GitHub, Claude, and Discord nodes. A real n8n execution still requires valid credentials and a Discord webhook.

