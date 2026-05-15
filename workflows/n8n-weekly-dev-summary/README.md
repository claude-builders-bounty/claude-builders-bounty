# Weekly GitHub Dev Summary with Claude

Exportable n8n workflow for a weekly Friday 5pm development summary. It fetches GitHub commits, closed issues, and merged PRs for the last seven days, sends the activity to Claude using `claude-sonnet-4-20250514`, and posts the generated Markdown to a Discord webhook.

## Setup

1. Import `weekly-dev-summary.workflow.json` into n8n.
2. Open the `Set Config` node and set `repo`, `language` (`EN` or `FR`), `destinationChannel`, `discordWebhookUrl`, optional `githubToken`, and `anthropicApiKey`.
3. Leave `dryRun: true` for the first manual test; this exercises the GitHub fetch and delivery path through Postman Echo without sending secrets.
4. Run `Manual Test Trigger` and confirm the workflow execution succeeds and the final `Execution Summary` node returns `ok: true`.
5. Set `dryRun: false`, save, and activate the workflow to run every Friday at 5pm.

## Config Variables

| Variable | Purpose |
| --- | --- |
| `repo` | GitHub repository in `owner/repo` format. |
| `language` | Summary language: `EN` or `FR`. |
| `destinationChannel` | Human-readable destination label included in the execution summary. |
| `discordWebhookUrl` | Discord webhook URL used when `dryRun` is `false`. |
| `githubToken` | Optional token for private repositories or higher GitHub API rate limits. |
| `anthropicApiKey` | Claude API key used when `dryRun` is `false`. |
| `dryRun` | Sends Claude and Discord requests to Postman Echo when `true`; uses real production endpoints when `false`. |

The GitHub HTTP Request nodes paginate with `page={{ $pageCount + 1 }}` and `per_page=100`, then aggregate all returned pages before generating the Claude prompt.

## Files

- `weekly-dev-summary.workflow.json` - n8n workflow import.
- `build-workflow.mjs` - repeatable generator for the workflow JSON.
- `TEST_NOTES.md` - local import and execution evidence.
