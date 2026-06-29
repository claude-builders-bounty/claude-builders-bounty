# Weekly dev summary — dry-run execution log

- **Timestamp:** 2026-06-27T12:51:29.264659+00:00
- **Repo:** `claude-builders-bounty/claude-builders-bounty`
- **Window:** since `2026-06-20T12:51:25.532841Z`
- **Method:** Same GitHub API calls as n8n workflow nodes (no n8n UI on CI host)

## Fetched counts
- Commits: 0
- Closed issues: 30
- Merged PRs (filtered): 0

## Sample commits

## Sample merged PRs

## Narrative preview (template — Claude node uses same inputs)

Over the past week, `claude-builders-bounty/claude-builders-bounty` had 0 commits, 30 closed issues, and 0 merged PRs. The n8n workflow passes this payload to `claude-sonnet-4-20250514` and posts the result to `DELIVERY_WEBHOOK_URL`.

## n8n manual test checklist
1. Import `n8n-weekly-dev-summary.workflow.json`
2. Set env: GITHUB_REPO, ANTHROPIC_API_KEY, DELIVERY_WEBHOOK_URL, SUMMARY_LANGUAGE
3. Execute workflow once — screenshot execution panel for maintainer
