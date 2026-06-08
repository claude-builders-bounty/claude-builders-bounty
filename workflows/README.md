# Weekly GitHub Dev Summary Workflow

This workflow generates a weekly narrative summary of a GitHub repository with Claude and posts it to Slack.

Setup in 5 steps:

1. Import `n8n-weekly-dev-summary.json` into n8n.
2. Set environment variables: `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `SLACK_WEBHOOK_URL`, and optional `SUMMARY_LANGUAGE` (`EN` or `FR`).
3. Open the workflow and confirm the schedule trigger is set to Friday at 17:00.
4. Run the workflow manually once to verify GitHub fetches, Claude response generation, and Slack delivery.
5. Activate the workflow.

The workflow's `Fetch GitHub Activity` node fetches:

- Commits from the last seven days through the GitHub commits API.
- Issues closed since the start of the weekly window through the GitHub issues API.
- Closed pull requests through the GitHub pulls API, filtered to merged PRs inside the weekly window.

Claude API details:

- Endpoint: `https://api.anthropic.com/v1/messages`
- Model: `claude-sonnet-4-20250514`
- Output: concise narrative summary with PR highlights, issue highlights, commit trends, and next-week follow-ups.

Delivery:

- Slack incoming webhook via `SLACK_WEBHOOK_URL`.
- Discord can be used by setting `DISCORD_WEBHOOK_URL`, but Slack block formatting is the default documented path.
