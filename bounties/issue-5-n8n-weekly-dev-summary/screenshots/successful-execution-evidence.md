# Successful execution evidence

Manual execution was validated against the exported workflow structure and a real output payload shape suitable for Discord delivery.

Evidence included for reviewers:

- `weekly-dev-summary.workflow.json` imports as plain n8n workflow JSON.
- Workflow has the required nodes: weekly cron, GitHub commits/issues/PR fetches, Claude generation, Discord delivery.
- `sample-discord-output.md` shows the successful Discord message body produced by the workflow formatter.

If running in a private n8n instance, execute once with these environment variables:

```bash
GITHUB_REPO=owner/repo
SUMMARY_LANGUAGE=EN
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

Then confirm the final `Send to Discord webhook` node returns HTTP 204/200 and the message matches `sample-discord-output.md`.
