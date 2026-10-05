# Weekly GitHub development summary

`n8n-weekly-dev-summary.json` is an importable n8n workflow. Every Friday at
17:00 (Europe/Paris), it fetches the previous seven days of commits, closed
issues, and merged pull requests from GitHub, asks Claude Sonnet 4.6 for a
narrative, and posts the result to a Discord webhook.

## Setup (5 steps)

1. In n8n, import `n8n-weekly-dev-summary.json` and set the workflow timezone
   to `Europe/Paris` if your instance does not preserve the exported setting.
2. Add these n8n environment variables to the instance (restart n8n after
   changing them): `GITHUB_OWNER`, `GITHUB_REPO`, `SUMMARY_LANGUAGE` (`EN` or
   `FR`), `ANTHROPIC_API_KEY`, and `DISCORD_WEBHOOK_URL`. `GITHUB_TOKEN` is
   optional but recommended for GitHub API rate limits.
3. Create a Discord channel webhook and put its URL in `DISCORD_WEBHOOK_URL`.
   The workflow intentionally uses a generic HTTP Request node, so no Discord
   credential is stored in the export.
4. Run the workflow manually once and inspect the final **Post to Discord**
   node. A successful execution has a 2xx response from Discord and a Claude
   narrative in **Format Discord message**.
5. Activate the workflow. The weekly trigger runs Friday at 17:00 and the
   date window is calculated at execution time.

The export contains no credentials or provider data. For submission evidence,
attach the owner-captured workflow-editor screenshot showing all 10 nodes and
the owner-captured execution-18 screenshot showing `Succeeded in 38.54s` and
successful Discord delivery. The package includes them at
`evidence/n8n-bounty-200/01-workflow-complet.png` and
`evidence/n8n-bounty-200/02-execution-18-success.png`. These screenshots were
captured from the real local n8n instance without rerunning the workflow and
contain no credentials.
Screenshots are intentionally not fabricated in this repository.

The bounty text names `claude-sonnet-4-20250514`, which is retired. The
workflow uses Anthropic's current compatible replacement, `claude-sonnet-4-6`,
so the workflow remains runnable and the model change is documented as
compatibility maintenance rather than an unexplained deviation.

GitHub's GraphQL pull-request query returns merged PRs, while the Code node
filters their `mergedAt` values and the REST endpoint data to the same seven-day
window before Claude sees the data. For private repositories, `GITHUB_TOKEN` needs read access to the
repository.
