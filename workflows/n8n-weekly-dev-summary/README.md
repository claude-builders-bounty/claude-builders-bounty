# Weekly GitHub Dev Summary with Claude

Import `weekly-dev-summary.workflow.json` into n8n to post a weekly narrative summary of a GitHub repository to Discord. The workflow runs every Friday at 17:00, fetches the last seven days of commits, closed issues, and merged pull requests from the GitHub REST API, asks `claude-sonnet-4-20250514` for an English or French summary, then sends it to a webhook.

## Configuration

Create these n8n variables before activating the workflow:

| Variable | Required | Example | Notes |
| --- | --- | --- | --- |
| `GITHUB_REPO` | Yes | `owner/repository` | Repository to summarize. |
| `GITHUB_TOKEN` | Yes | `github_pat_...` | Token with read access to the repository. |
| `ANTHROPIC_API_KEY` | Yes | `sk-ant-...` | Used by the Claude Messages API node. |
| `DESTINATION_WEBHOOK_URL` | Yes | `https://discord.com/api/webhooks/...` | Discord webhook destination channel. |
| `SUMMARY_LANGUAGE` | No | `EN` or `FR` | Defaults to `EN`. |

## Setup in five steps

1. In n8n, import `weekly-dev-summary.workflow.json`.
2. Add the five variables above under n8n variables.
3. Open the workflow and run it once with **Execute workflow** to verify GitHub, Claude, and Discord connectivity.
4. Confirm the Discord channel received the generated weekly summary.
5. Activate the workflow so the Friday 17:00 cron trigger runs automatically.

## Execution flow

`Weekly Friday Trigger` -> `Build Weekly Window` -> `Fetch Commits` -> `Fetch Closed Issues` -> `Fetch Merged Pull Requests` -> `Build Claude Request` -> `Claude Narrative Summary` -> `Prepare Discord Message` -> `Send Discord Webhook`

## Successful execution proof

The workflow export was imported successfully with n8n `2.21.4` using a fresh local n8n user folder:

```text
Importing 1 workflows...
Successfully imported 1 workflow.
```

End-to-end delivery requires real GitHub, Anthropic, and Discord credentials, which are intentionally configured through n8n variables instead of being embedded in the exported workflow.
