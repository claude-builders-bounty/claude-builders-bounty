# n8n + Claude Weekly Dev Summary

Importable n8n workflow for issue #5. It runs every Friday at 5pm, collects one week of GitHub activity, asks Claude Sonnet 4 to turn the activity into a narrative summary, then posts the result to Discord via webhook.

## Setup in 5 steps

1. Import `workflows/weekly-dev-summary-claude.json` into n8n.
2. Set environment variables in your n8n runtime:
   - `GITHUB_REPO=owner/repo`
   - `GITHUB_TOKEN=github_pat_or_token`
   - `ANTHROPIC_API_KEY=sk-ant-...`
   - `DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...`
   - `SUMMARY_LANGUAGE=EN` or `FR`
3. Open the imported workflow and confirm the schedule node is set to Friday at 5pm.
4. Run the workflow manually once to verify GitHub, Claude, and Discord delivery.
5. Activate the workflow.

## What it fetches

From the GitHub API for the configured repo:

- commits from the last seven days
- closed issues since the last seven days
- merged pull requests updated/merged during the same window

## Claude call

The workflow calls:

```text
POST https://api.anthropic.com/v1/messages
model: claude-sonnet-4-20250514
```

The prompt asks for a narrative summary with these sections:

- Headline
- What shipped
- Bugs closed
- Engineering momentum
- Risks / follow-ups
- Links

## Delivery

The final node posts a Discord webhook message. Discord was chosen because it works with a single URL and does not require SMTP credentials.

## Configurable variables

- `GITHUB_REPO`: repository slug, e.g. `vercel/next.js`
- `GITHUB_TOKEN`: GitHub token for API rate limits/private repos
- `ANTHROPIC_API_KEY`: Claude API key
- `DISCORD_WEBHOOK_URL`: destination channel webhook
- `SUMMARY_LANGUAGE`: `EN` or `FR`

## Validation

Run structural validation locally:

```bash
python3 scripts/validate_workflow.py workflows/weekly-dev-summary-claude.json
```

Expected output:

```text
workflow ok: workflows/weekly-dev-summary-claude.json (11 nodes)
```

## Test evidence

- `scripts/validate_workflow.py` validates the exported JSON structure and required variables.
- `TEST_NOTES.md` records import/execution notes.
- `screenshots/` is reserved for the n8n execution screenshot after importing in a live n8n instance.
