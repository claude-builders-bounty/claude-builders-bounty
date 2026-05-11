# n8n Weekly Dev Summary Workflow

This folder contains an importable n8n workflow for bounty
[#5](../issues/5). It runs every Friday at 5pm, fetches one week of GitHub
repository activity, asks Claude to write a narrative engineering summary, and
sends the result to Slack through an incoming webhook.

## Setup

1. Import `workflows/n8n-weekly-dev-summary.json` into n8n.
2. Set environment variables: `GITHUB_REPO=owner/repo`,
   `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `SLACK_WEBHOOK_URL`, and optional
   `SUMMARY_LANGUAGE=EN` or `SUMMARY_LANGUAGE=FR`.
3. Open the imported workflow, execute it once manually, then activate it.

## What It Does

- Weekly cron trigger: Friday at 5pm.
- GitHub API calls:
  - commits since the last seven days
  - closed issues since the last seven days
  - merged PRs since the last seven days
- Claude API call:
  - model: `claude-sonnet-4-20250514`
  - endpoint: `https://api.anthropic.com/v1/messages`
- Delivery:
  - Slack incoming webhook using `SLACK_WEBHOOK_URL`
- Configurable variables:
  - `GITHUB_REPO`
  - `SLACK_WEBHOOK_URL`
  - `SUMMARY_LANGUAGE`

## Local Validation

```bash
python3 tests/validate_n8n_workflow.py
```

The validator checks that the workflow JSON parses, contains the required n8n
top-level keys, includes all required nodes, uses the requested Claude model,
and wires every referenced connection to an existing node.

## Real n8n Validation Note

This PR includes the importable workflow JSON and structural validation. A final
manual run in a live n8n workspace requires real `GITHUB_TOKEN`,
`ANTHROPIC_API_KEY`, and `SLACK_WEBHOOK_URL` values.
