# n8n weekly GitHub → Claude → Discord summary

**Bounty:** #5 — $200 (Opire)

Importable n8n workflow that every **Friday 17:00** pulls a week of GitHub activity, asks **Claude** (`claude-sonnet-4-20250514`) for a narrative summary, and posts to a **Discord webhook**.

## Setup (5 steps)

1. Import `weekly-dev-summary.workflow.json` into n8n (**Workflows → Import**).
2. Create **HTTP Header Auth** credential: header `Authorization` = `Bearer <GITHUB_PAT>`.
3. Set environment variables (n8n host or workflow static data):
   - `GITHUB_REPO` = `owner/name`
   - `ANTHROPIC_API_KEY` = Claude API key
   - `DISCORD_WEBHOOK_URL` = Discord channel webhook
   - `SUMMARY_LANG` = `EN` or `FR`
4. Attach the GitHub header credential to the three GitHub HTTP nodes.
5. Activate the workflow (or **Execute workflow** once for a dry run).

## Configurable variables

| Variable | Purpose |
|----------|---------|
| `GITHUB_REPO` | Target repository |
| `DISCORD_WEBHOOK_URL` | Delivery destination |
| `SUMMARY_LANG` | `EN` / `FR` narrative language |
| Cron | Default `0 17 * * 5` (Friday 17:00) |

## Data sources

- Commits since 7 days (`/repos/{repo}/commits?since=`)
- Closed issues this week (Search API)
- Merged PRs this week (Search API)

## Test evidence

- `samples/execution-dry-run.md` — dry-run notes + mock activity payload shape used when validating the merge/Claude prompt offline.
- Full live n8n screenshot depends on your instance secrets; after step 5, capture **Executions → success** and attach to the PR if required by maintainers.

## Alternative delivery

Swap the final HTTP node URL for a Slack incoming webhook or use n8n **Email** node with SMTP credentials.
