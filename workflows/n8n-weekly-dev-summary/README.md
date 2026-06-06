# n8n Weekly GitHub Activity Summary

Importable n8n workflow that collects weekly GitHub activity, asks Claude Sonnet 4 for a narrative summary, and delivers it to Discord.

## Setup In 5 Steps

1. Import `workflow.json` into n8n.
2. Set environment variables: `GITHUB_REPO=owner/repo`, `GITHUB_TOKEN=...`, `ANTHROPIC_API_KEY=...`, `DISCORD_WEBHOOK_URL=...`, `SUMMARY_LANGUAGE=EN` or `FR`.
3. Open the workflow and confirm the Friday 5pm cron trigger.
4. Run the workflow manually once to verify GitHub fetches, Claude generation, and Discord delivery.
5. Activate the workflow.

## What It Does

- Runs every Friday at 5pm.
- Fetches commits from the last 7 days.
- Fetches closed issues from the last 7 days.
- Fetches closed PRs and keeps only PRs merged during the last 7 days.
- Calls Claude API with `claude-sonnet-4-20250514`.
- Sends the generated narrative summary to Discord.
- Supports English and French through `SUMMARY_LANGUAGE=EN` or `SUMMARY_LANGUAGE=FR`.

## Validation

Run:

```bash
node workflows/n8n-weekly-dev-summary/validate-workflow.mjs
```

The validator checks JSON import shape, required node types, cron trigger, GitHub endpoints, Claude model, Discord delivery, configurable variables, and README step count.

## Local Evidence

This submission includes local validation evidence in `validation-evidence.md`. A live n8n screenshot still requires real `ANTHROPIC_API_KEY` and `DISCORD_WEBHOOK_URL` values, so the workflow is structured to run without embedded secrets.
