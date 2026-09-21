# Verification — weekly GitHub → Claude → Discord (Bounty #5)

**PR:** https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4406  
**Issue:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5  
**Checked:** 2026-09-22 Asia/Taipei overnight patrol

## What was verified locally (no secrets)

| Check | Result |
|-------|--------|
| Workflow JSON present | `workflows/weekly-github-dev-summary.json` |
| README ≤5 setup steps | `workflows/weekly-github-dev-summary/README.md` |
| Dry-run script | `python3 workflows/weekly-github-dev-summary/scripts/dry_run_summary.py --repo expressjs/express --lang EN` |
| Sample EN/FR outputs | under `examples/` |
| Cron Friday 17:00 | Schedule `0 17 * * 5` documented in README |

## Dry-run notes

The dry-run uses the public GitHub API and prints the Claude prompt. It does **not** call Anthropic or Discord unless the operator sets `ANTHROPIC_API_KEY` / `DISCORD_WEBHOOK_URL` on their own n8n host. Secrets must never be pasted into the issue or PR.

## Remaining operator step (optional screenshot)

Acceptance asks for a real n8n **Execute Workflow** capture. Replace `examples/execution-success.png` with a live UI screenshot when an n8n instance is available. Until then the committed placeholder + dry-run log document the offline path.

## Claim path

On the issue, `/opire try` was already posted by masaki12214. Payment is Stripe via Opire **only after maintainer merge** — not automatic on PR open.
