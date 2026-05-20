# Weekly Dev Summary n8n Workflow

Importable n8n workflow that fetches one week of GitHub activity, asks Claude to write a narrative summary, and posts the result to a Slack incoming webhook.

## Setup

1. Import `weekly-dev-summary.json` in n8n with **Import from File**.
2. Create n8n variables: `github_owner`, `github_repo`, `summary_language`, `anthropic_api_key`, and `destination_webhook_url`.
3. Optional: add `github_token` if the repository is private or the workflow needs a higher GitHub API rate limit.
4. Open the workflow, run **Manual Test Trigger** once, and confirm the final Slack webhook node returns a 2xx response.
5. Activate the workflow so **Weekly Friday 5pm Trigger** runs every Friday at 5:00 PM.

## Variables

| Variable | Required | Example | Purpose |
| --- | --- | --- | --- |
| `github_owner` | Yes | `n8n-io` | GitHub repository owner or organization. |
| `github_repo` | Yes | `n8n` | GitHub repository name. |
| `summary_language` | Yes | `EN` or `FR` | Output language for the narrative summary. |
| `anthropic_api_key` | Yes | `sk-ant-...` | API key used by the Claude Messages API call. |
| `destination_webhook_url` | Yes | `https://hooks.slack.com/services/...` | Slack incoming webhook that receives the summary. |
| `github_token` | No | `github_pat_...` | Adds GitHub authentication when present. |

## What It Collects

- Commits pushed during the last seven days.
- Issues closed during the last seven days.
- Pull requests merged during the last seven days.

The workflow sends that activity to `claude-sonnet-4-20250514` and asks for a concise weekly narrative with highlights, shipped changes, resolved issues, merged pull requests, and suggested follow-ups.

## Validation

- `python3 workflows/weekly-dev-summary/tests/validate_workflow.py`
- `n8n import:workflow --input=workflows/weekly-dev-summary/weekly-dev-summary.json`
- `n8n execute --id=weekly-dev-summary --rawOutput`
- Evidence screenshot: `evidence/successful-execution.png`

The screenshot shows a successful n8n v2.21.5 execution against `AymanMahfuz27/claude-builders-bounty`, with the webhook pointed at `https://httpbin.org/post` for safe validation. For production, set `destination_webhook_url` to a Slack incoming webhook URL.
