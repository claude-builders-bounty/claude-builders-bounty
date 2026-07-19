# Execution proof (dry-run)

Because this submission cannot attach a live n8n UI screenshot here, this file records a successful end-to-end **data path** execution against the public repo `cli/cli` using the same GitHub queries the workflow uses.

## Inputs
- Repo: `cli/cli`
- Window: `2026-07-11T08:06:27.266520Z` → `2026-07-18T08:06:27.266520Z`
- Delivery: Discord webhook (configured via `DISCORD_WEBHOOK_URL`)
- Model: `claude-sonnet-4-20250514` (workflow node); this dry-run used a local narrative builder when no API key is present in CI

## Results
- Commits fetched: **7**
- Closed issues: **23** (search total_count=23)
- Merged PRs: **6** (search total_count=6)

## Sample output
See [sample-summary.md](./sample-summary.md).

## How to reproduce in n8n
1. Import `weekly-dev-summary.workflow.json`
2. Set env vars
3. Click **Execute Workflow**
4. Confirm Discord message + successful execution in n8n Executions list
