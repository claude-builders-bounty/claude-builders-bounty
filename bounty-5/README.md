# n8n weekly GitHub development summary

Setup in five steps:

1. Import `weekly-dev-summary.json` into n8n.
2. Set environment variables `GITHUB_REPO=owner/repo`, `GITHUB_TOKEN`, and `ANTHROPIC_API_KEY`.
3. Set `SLACK_WEBHOOK_URL`; optionally set `SUMMARY_LANGUAGE=EN` or `FR`.
4. Set `CLAUDE_MODEL`. The bounty text names `claude-sonnet-4-20250514`; the workflow keeps that as its fallback for acceptance compatibility, but that model is retired in 2026, so a current Anthropic model must be supplied for a live run.
5. Execute once manually, inspect the Slack message, then activate the workflow. It runs Fridays at 17:00 in the workflow timezone.

The workflow fetches the previous seven days of GitHub commits, closed issues, and closed PRs, filters PRs to ones actually merged inside the window, asks Claude for a factual EN/FR narrative, and posts the result to Slack.

## Validation note

`validate_workflow.py` verifies the exported JSON structure, required nodes, cron expression, API endpoints, variables, and model fallback. This execution environment does not contain n8n or Anthropic credentials, so **no real n8n execution or screenshot is claimed here**.
