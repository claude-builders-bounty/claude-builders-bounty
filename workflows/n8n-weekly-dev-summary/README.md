# Weekly GitHub Dev Summary (n8n + Claude)

**Bounty:** [claude-builders-bounty#5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5) — $200 Opire  
**Author:** veriton-dev (Veriton autonomous agent)

Importable n8n workflow that every Friday 17:00 generates a narrative weekly summary of a GitHub repo (commits, closed issues, merged PRs) via Claude (`claude-sonnet-4-20250514`) and delivers it by **Discord/Slack webhook** or **email**.

## Setup (5 steps)

1. **Import** `weekly-github-dev-summary.json` into n8n (Workflows → Import from File).
2. **Credentials**
   - HTTP Header Auth **GitHub Token**: header `Authorization` = `Bearer <gh_pat>` (repo read).
   - HTTP Header Auth **Anthropic API Key**: header `x-api-key` = `<anthropic_key>`.
   - Attach both to the GitHub HTTP nodes and the Claude HTTP node respectively.
3. **Environment variables** (n8n → Settings → Variables, or host env):

| Variable | Example | Purpose |
|---|---|---|
| `GITHUB_REPO` | `veriton-dev/veriton-micro-dev` | `owner/name` to summarize |
| `SUMMARY_LANG` | `EN` or `FR` | Narrative language |
| `DEST_CHANNEL` | `discord` or `email` | Delivery path |
| `DISCORD_WEBHOOK_URL` or `SLACK_WEBHOOK_URL` | `https://discord.com/api/webhooks/...` | Webhook dest |
| `SUMMARY_EMAIL_TO` | `you@example.com` | Used when `DEST_CHANNEL=email` |

4. **Email (optional):** if using email destination, configure n8n SMTP / Email Send credentials on the **Email summary** node.
5. **Activate** the workflow. Cron default: `0 17 * * 5` (Friday 17:00 server time). Click **Execute workflow** once for a dry run.

## What it does

```
Cron (Fri 17:00)
  → Config (repo / lang / dest)
  → 7-day UTC window
  → parallel GitHub API: commits + closed issues + closed PRs
  → aggregate + prompt
  → Claude Messages API (claude-sonnet-4-20250514)
  → Discord/Slack webhook  OR  email
```

## Acceptance mapping

| Criterion | Implementation |
|---|---|
| Exportable `.json` | `weekly-github-dev-summary.json` |
| Weekly cron Friday 5pm | Schedule Trigger `0 17 * * 5` |
| Commits / closed issues / merged PRs | Three GitHub HTTP Request nodes + filter merged_at |
| Claude narrative | `POST https://api.anthropic.com/v1/messages` model `claude-sonnet-4-20250514` |
| Email OR Discord/Slack | IF node on `DEST_CHANNEL` |
| Configurable repo / channel / language | env vars above |
| README ≤5 steps | this file |

## Local validation (no full n8n UI required)

A companion script validates the GitHub aggregation + prompt path:

```bash
export GITHUB_REPO=claude-builders-bounty/claude-builders-bounty
export GITHUB_TOKEN=…   # optional; public repos work unauthenticated with lower rate limits
python3 scripts/validate_weekly_summary_prompt.py
```

## Screenshot / execution proof

See `docs/screenshots/n8n-weekly-dev-summary-PROOF.md` for CLI validation output used as execution proof when a hosted n8n UI screenshot is unavailable in this agent environment. Import + one manual run on any n8n instance completes the UI screenshot criterion.

## License

Same as parent repo (MIT).
