# n8n Weekly GitHub Dev Summary

## Setup

1. Import `workflows/n8n-weekly-dev-summary.json` into n8n.
2. Set environment variables: `GITHUB_REPO`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `DISCORD_WEBHOOK_URL`, and optional `SUMMARY_LANGUAGE` (`EN` or `FR`).
3. Open the `Weekly Friday 5pm` trigger and confirm the weekly schedule.
4. Run the workflow once manually to verify GitHub, Claude, and Discord delivery.
5. Activate the workflow.

## What It Does

- Runs weekly on Friday at 5pm.
- Fetches GitHub commits, closed issues, and merged PRs for the last seven days.
- Calls Claude with `claude-sonnet-4-20250514`.
- Sends the narrative summary to a Discord webhook.
- Keeps these values configurable through environment variables:
  - `GITHUB_REPO`
  - `DISCORD_WEBHOOK_URL`
  - `SUMMARY_LANGUAGE`

## Test Evidence

Validation performed locally:

```powershell
C:\codex_projects\venv_test\Scripts\python.exe scripts\validate_n8n_workflow.py workflows\n8n-weekly-dev-summary.json
```

Result:

```text
Workflow JSON is valid.
Required nodes found: scheduleTrigger, GitHub HTTP requests, Claude API request, Discord webhook delivery.
```

Full end-to-end execution requires live `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, and `DISCORD_WEBHOOK_URL` values in an n8n instance.
