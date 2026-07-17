# Weekly GitHub Dev Summary (n8n + Claude)

Opire bounty: automated weekly narrative of a GitHub repo using Claude.

## What you get
- Importable n8n workflow: `weekly-dev-summary.json`
- Weekly cron: **Friday 17:00** (`0 17 * * 5`)
- Fetches **commits**, **closed issues**, **merged PRs** for the last 7 days
- Calls Claude `claude-sonnet-4-20250514` for a narrative summary
- Delivers via **Discord webhook** (swap the last node for SMTP/email if you prefer)
- Config via env: repo, language EN/FR, webhook URL

## Setup (5 steps)
1. Import `weekly-dev-summary.json` into n8n (Workflows → Import from File).
2. Set environment variables (n8n Settings → Variables or host env):
   - `GITHUB_TOKEN` — PAT with repo/public_repo read
   - `GITHUB_OWNER` — org/user (example: `octocat`)
   - `GITHUB_REPO` — repository name
   - `ANTHROPIC_API_KEY` — Anthropic API key
   - `DISCORD_WEBHOOK_URL` — Discord channel webhook
   - `SUMMARY_LANG` — `EN` or `FR` (optional, default EN)
3. Open the workflow → **Execute workflow** once (or wait for Friday 5pm).
4. Confirm Discord receives the summary; check n8n Executions for green checkmarks.
5. Activate the workflow so the cron keeps running.

## Delivery choice
Default delivery is **Discord webhook**. To use email instead, replace the final **Discord Webhook** HTTP node with n8n **Email Send (SMTP)** and map `summary` into the body.

## Configurable variables
| Variable | Purpose |
|----------|---------|
| `GITHUB_OWNER` / `GITHUB_REPO` | Target repository |
| `SUMMARY_LANG` | `EN` or `FR` narrative language |
| `DISCORD_WEBHOOK_URL` | Destination channel |
| `GITHUB_TOKEN` / `ANTHROPIC_API_KEY` | Credentials |

## Offline dry-run
`dry_run_prompt.py` in this folder builds the same GitHub→prompt shape without n8n (validates repo access + AC data path).

## Test evidence
See `TEST_EVIDENCE.md`.
