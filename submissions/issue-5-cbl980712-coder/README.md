# Automated Weekly Dev Summary

Submission for `claude-builders-bounty/claude-builders-bounty` issue 5.

This n8n workflow runs every Friday at 5pm, fetches weekly repository activity from GitHub, asks Claude to turn the raw activity into a concise developer summary, and posts the result to Discord.

## Files

- `workflows/weekly-dev-summary.json`: importable n8n workflow.

## What It Does

1. Runs every Friday at 17:00.
2. Reads repository config from environment variables.
3. Fetches activity from GitHub:
   - commits from the last 7 days
   - merged pull requests from the last 7 days
   - closed issues from the last 7 days
4. Builds an EN or FR structured prompt for Claude.
5. Calls the Anthropic Messages API using `claude-sonnet-4-20250514`.
6. Posts the weekly summary to Discord.

## Required Environment Variables

```bash
GITHUB_OWNER=your-org-or-user
GITHUB_REPO=your-repo
ANTHROPIC_API_KEY=sk-ant-...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
SUMMARY_LANGUAGE=EN
```

Set `SUMMARY_LANGUAGE=FR` for French output.

## Required n8n Credential

Create an n8n `HTTP Header Auth` credential named `GitHub Token`:

- Header name: `Authorization`
- Header value: `Bearer YOUR_GITHUB_TOKEN`

The workflow JSON uses a placeholder credential id:

```text
__REPLACE_WITH_N8N_CREDENTIAL_ID__
```

After importing, select your local `GitHub Token` credential in each GitHub HTTP Request node.

## Setup In 5 Steps

1. Open n8n.
2. Import `workflows/weekly-dev-summary.json`.
3. Set `GITHUB_OWNER`, `GITHUB_REPO`, `ANTHROPIC_API_KEY`, `DISCORD_WEBHOOK_URL`, and optional `SUMMARY_LANGUAGE`.
4. Attach your `GitHub Token` HTTP Header Auth credential to the three GitHub request nodes.
5. Run once manually, confirm the Discord message, then activate the workflow.

## Expected Discord Output

The Discord message includes:

- repository name
- executive summary
- merged or active PR notes
- notable commits
- issues needing attention
- suggested next-week priorities

## Notes

- The workflow keeps the GitHub token in n8n credentials rather than in the JSON.
- The Anthropic and Discord values are read from environment variables to keep the workflow portable.
- The Claude prompt asks for concise Markdown and requires uncertainty to be stated when activity is sparse.
- The workflow uses HTTP Request nodes for portability and to avoid requiring provider-specific n8n community nodes.
- I could not include a real n8n execution screenshot from this machine without the user's n8n instance, API keys, and Discord webhook.

