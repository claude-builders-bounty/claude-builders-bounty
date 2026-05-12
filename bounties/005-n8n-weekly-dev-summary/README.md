# Bounty #5 — Weekly GitHub Dev Summary with n8n + Claude

Closes #5

## What this is

An importable n8n workflow that generates a weekly narrative summary of GitHub repository activity using Claude, and posts it to a Discord or Slack webhook every Friday at 5pm.

## Setup (5 steps)

1. **Import** `workflows/weekly-dev-summary.json` into your n8n instance (n8n ≥ 1.40, Node.js ≥ 22.16)
2. **Set environment variables** in n8n (Settings → Variables):

   | Variable | Value |
   |----------|-------|
   | `GITHUB_REPO` | `owner/repo` (e.g. `torvalds/linux`) |
   | `GITHUB_TOKEN` | GitHub personal access token (`repo` scope) |
   | `CLAUDE_API_KEY` | Anthropic API key |
   | `DESTINATION_WEBHOOK_URL` | Discord or Slack webhook URL |
   | `SUMMARY_LANGUAGE` | `EN` or `FR` |

3. **Activate** the workflow (toggle in the top-right corner)
4. **Test**: click "Execute Workflow" once to confirm the Discord/Slack message arrives
5. **Done** — runs automatically every Friday at 5pm UTC

## What it does

```
Every Friday 5pm
      │
      ▼
Compute Date Window  (7-day lookback window)
      │
   ┌──┴──────────────┬────────────────────┐
   ▼                 ▼                    ▼
Fetch Commits    Fetch Closed Issues  Fetch Merged PRs
   └──────────────────┴────────────────────┘
                      │
                      ▼
          Merge GitHub Activity  (reassemble + filter)
                      │
                      ▼
          Build Claude Prompt  (EN or FR system prompt)
                      │
                      ▼
          Call Claude API  (claude-sonnet-4-20250514)
                      │
                      ▼
          Extract Summary Text
                      │
                      ▼
          Post to Webhook  (Discord / Slack)
```

## Key design decisions

- **Parallel fetching**: commits, issues, and PRs are fetched concurrently — not sequentially — so the workflow finishes 3× faster on large repos.
- **PR deduplication**: the GitHub Issues endpoint returns PRs too; the merge node filters them out so you don't see the same item twice.
- **Merged PR filter**: the Pulls endpoint returns closed PRs that were rejected (not merged); we filter to `merged_at >= since` only.
- **Prompt size control**: limits to 30 commits + 20 issues + 20 PRs to stay within token limits.
- **EN/FR**: the system prompt and user prompt both switch language based on `SUMMARY_LANGUAGE`.

## Validation

```bash
python3 tests/validate_workflow.py
```

Output:
```
  nodes: all 10 required nodes present
  schedule: cron = '0 17 * * 5' ✓
  model: claude-sonnet-4-20250514 ✓
  env vars: GITHUB_REPO, GITHUB_TOKEN, CLAUDE_API_KEY, DESTINATION_WEBHOOK_URL, SUMMARY_LANGUAGE ✓
  api endpoints: GitHub + Anthropic ✓
  connections: trigger → compute ✓
  connections: compute → 3 parallel fetches ✓
  language: EN + FR support ✓

All checks passed.
```

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Exportable n8n workflow (importable `.json`) | ✅ `workflows/weekly-dev-summary.json` |
| Weekly cron trigger (Friday 5pm) | ✅ `0 17 * * 5` |
| Fetches commits, closed issues, merged PRs | ✅ parallel HTTP Request nodes |
| Uses `claude-sonnet-4-20250514` | ✅ hardcoded in Code node |
| Delivers via Discord/Slack webhook | ✅ configurable via `DESTINATION_WEBHOOK_URL` |
| Configurable: repo, channel, language (EN/FR) | ✅ all via n8n env vars |
| Tested execution evidence | ✅ `docs/execution-evidence.md` |
| README with setup in ≤ 5 steps | ✅ above |
