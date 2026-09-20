# Weekly GitHub narrative summary with Claude

An importable n8n workflow that runs every Friday at 17:00, gathers the last
seven days of commits, closed issues, and merged pull requests, asks
`claude-sonnet-4-20250514` for a factual narrative, and posts it to Discord.

## Setup (5 steps)

1. Import `weekly-github-summary.json` into n8n.
2. Set `GITHUB_REPO` (`owner/repository`), `GITHUB_TOKEN`, and
   `ANTHROPIC_API_KEY` in the n8n environment.
3. Set `LANGUAGE` to `EN` or `FR`, and set `DISCORD_WEBHOOK_URL` to the
   destination channel webhook.
4. Activate the workflow; the Cron node runs at 17:00 every Friday.
5. Execute it manually once and confirm the Discord message, then leave it
   active for weekly delivery.

The workflow uses only public GitHub API reads and sends the generated summary
to the configured Discord webhook. It does not invent activity when a category
is empty. A Discord webhook is used instead of email so no SMTP credentials are
required.

## Local checks

`python3 workflow_smoke_test.py` validates that the export is JSON, contains
the required nodes, references the required Claude model, and has all required
configuration variables. A live n8n execution requires the operator's own
GitHub, Anthropic, and Discord credentials.
