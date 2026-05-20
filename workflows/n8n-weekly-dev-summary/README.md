# n8n Weekly GitHub Dev Summary

Importable n8n workflow for bounty #5. It runs every Friday at 5pm, gathers a GitHub repository's weekly commits, closed issues, and merged pull requests, asks Claude Sonnet 4 for a narrative summary, and posts the result to a Discord webhook.

## Setup in 5 Steps

1. Import `weekly-dev-summary.workflow.json` into n8n.
2. Set environment variables: `GITHUB_OWNER`, `GITHUB_REPO`, `SUMMARY_LANGUAGE` (`EN` or `FR`), `SUMMARY_WEBHOOK_URL`, `ANTHROPIC_API_KEY`, and optionally `GITHUB_TOKEN`.
3. Open the workflow and confirm the `Weekly Friday 5pm Trigger` schedule is correct for your timezone.
4. Click **Test workflow** once and verify the GitHub API, Claude API, and webhook nodes all succeed.
5. Activate the workflow.

The workflow also includes `CLI Verification Trigger` so `n8n execute --id <workflow-id>` can run the full chain during local verification. The production schedule remains `Weekly Friday 5pm Trigger`.

## Configuration

| Variable | Required | Purpose |
| --- | --- | --- |
| `GITHUB_OWNER` | No | GitHub organization or user. Defaults to `claude-builders-bounty`. |
| `GITHUB_REPO` | No | GitHub repository. Defaults to `claude-builders-bounty`. |
| `SUMMARY_LANGUAGE` | No | `EN` or `FR`. Defaults to `EN`. |
| `SUMMARY_WEBHOOK_URL` | Yes | Discord incoming webhook URL. |
| `ANTHROPIC_API_KEY` | Yes | Claude API key used by the Anthropic Messages API call. |
| `GITHUB_TOKEN` | No | GitHub token for higher rate limits or private repos. |
| `ANTHROPIC_BASE_URL` | No | Optional local verification override. Defaults to `https://api.anthropic.com/v1/messages`. |

## What the Workflow Does

- Uses a weekly cron schedule: `0 17 * * 5`.
- Calls GitHub REST API endpoints for commits, closed issues, and closed pull requests.
- Filters issues to exclude pull requests and filters merged pull requests by `merged_at`.
- Calls `https://api.anthropic.com/v1/messages` with `claude-sonnet-4-20250514`.
- Posts a compact weekly narrative to the configured webhook.

## Verification

Static validation:

```bash
python tests/test_n8n_weekly_dev_summary_workflow.py
```

Verified local n8n run:

- Imported with `n8n import:workflow`.
- Executed with `n8n execute --id <workflow-id>` using n8n `1.94.1` under Node `22`.
- Used mock Anthropic and Discord endpoints only for local proof, with `ANTHROPIC_BASE_URL=http://127.0.0.1:8765/v1/messages` and `SUMMARY_WEBHOOK_URL=http://127.0.0.1:8765/webhook`.
- Evidence is stored in `evidence/n8n-cli-execution-summary.txt` and `evidence/n8n-success-screenshot.png`.

Real n8n validation target:

1. Import the JSON into n8n.
2. Set the variables above.
3. Run **Test workflow**.
4. Save a screenshot showing all nodes succeeded in the n8n execution view.
