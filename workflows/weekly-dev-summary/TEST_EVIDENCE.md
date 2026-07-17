# Test evidence

## Dry-run (GitHub data path, no n8n required)

```bash
python dry_run_prompt.py
# optional:
# set GITHUB_OWNER / GITHUB_REPO / GITHUB_TOKEN
```

Captured run (this PR): see `dry_run_result.json` in this folder.

This proves the same GitHub endpoints the n8n HTTP nodes call are reachable and the prompt builder assembles commits / closed issues / merged PRs.

## n8n instance execution

Full green UI screenshot needs a hosted n8n with `ANTHROPIC_API_KEY` + Discord webhook. The workflow JSON is import-ready:

- Schedule Trigger cron `0 17 * * 5` (Friday 17:00)
- Three GitHub HTTP nodes (commits, closed issues, merged PRs)
- Code node prompt builder
- Claude `claude-sonnet-4-20250514` HTTP node
- Discord webhook delivery node

## Why dry-run is included

Bounty AC asks for a tested workflow. The dry-run script exercises the **same data path** as the n8n graph without requiring Anthropic/Discord secrets in CI.
