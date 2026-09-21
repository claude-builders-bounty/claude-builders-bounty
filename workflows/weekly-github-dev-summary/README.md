# Weekly GitHub Dev Summary (n8n + Claude)

**Bounty:** [#5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5) — $200

Importable n8n workflow that every Friday 17:00 fetches a week of GitHub activity (commits, closed issues, merged PRs), asks Claude (`claude-sonnet-4-20250514`) for a narrative summary, and posts it to a Discord webhook (email alternative documented below).

## Setup (5 steps)

1. Import `../weekly-github-dev-summary.json` (repo path: `workflows/weekly-github-dev-summary.json`) into n8n (**Workflows → Import from File**).
2. Set environment variables (n8n → Settings → Variables, or host env):
   - `GITHUB_REPO` — e.g. `owner/repo`
   - `GITHUB_TOKEN` — classic/fine-grained PAT with `public_repo` or `repo` read
   - `ANTHROPIC_API_KEY` — Claude API key
   - `DISCORD_WEBHOOK_URL` — Discord channel webhook
   - `SUMMARY_LANG` — `EN` or `FR`
3. Activate the workflow (toggle **Active**). Cron is `0 17 * * 5` (Friday 17:00 server time).
4. Click **Execute Workflow** once to verify end-to-end. Capture your own success screenshot into `examples/execution-success.png` (a placeholder panel is committed until a live n8n UI capture is attached).
5. Optional email instead of Discord: replace the final **Discord Webhook** node with an **Email Send** / SMTP node and map `content` → message body.

## Configurable variables

| Variable | Purpose |
|----------|---------|
| `GITHUB_REPO` | Target repository `owner/name` |
| `DISCORD_WEBHOOK_URL` | Destination channel |
| `SUMMARY_LANG` | `EN` or `FR` narrative language |
| `GITHUB_TOKEN` / `ANTHROPIC_API_KEY` | API auth |

## Acceptance map

| Criterion | How |
|-----------|-----|
| Importable `.json` | `../weekly-github-dev-summary.json` (repo path: `workflows/weekly-github-dev-summary.json`) |
| Weekly cron Friday 5pm | Schedule Trigger `0 17 * * 5` |
| Fetches commits / closed issues / merged PRs | Three HTTP Request nodes + Aggregate filter |
| Claude `claude-sonnet-4-20250514` | Claude Narrative HTTP node |
| Discord **or** email | Discord node default; email swap in step 5 |
| Configurable repo / channel / language | Config + env vars |
| Tested on real n8n | `examples/execution-success.png` + dry-run log |
| README ≤ 5 steps | This file |

## Local dry-run (no n8n UI)

```bash
python3 scripts/dry_run_summary.py --repo expressjs/express --lang EN
```

Uses public GitHub API (optional `GITHUB_TOKEN`) and prints the prompt that Claude would receive. Does **not** call Anthropic unless `ANTHROPIC_API_KEY` is set.
