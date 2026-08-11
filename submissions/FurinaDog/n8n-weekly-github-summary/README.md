# GitHub weekly narrative summary for n8n

This submission provides an importable n8n workflow that runs every Friday at
17:00, gathers commits, closed issues, and merged pull requests from one
GitHub repository, asks Claude for a concise narrative in English or French,
and posts the result to a Discord webhook.

## Setup

1. Import `workflow.json` into n8n.
2. Set these n8n environment variables: `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`,
   `GITHUB_REPO` (`owner/repository`), `DISCORD_WEBHOOK_URL`, and optional
   `SUMMARY_LANG` (`EN` or `FR`).
3. Run the workflow manually once and confirm the Discord message.
4. Activate the workflow after the manual run succeeds.

The GitHub token needs repository metadata/read access. The workflow uses the
Anthropic Messages API with `claude-sonnet-4-20250514`. The Discord webhook is
the delivery target selected for this submission.

## Design notes

- GitHub GraphQL fetches commits, closed issues, and merged pull requests in a
  single request for the previous seven days.
- The Code node validates required configuration and fails loudly on a
  partial GitHub response instead of sending an incomplete summary.
- The prompt asks Claude to separate shipped work, fixes, and notable risks,
  and to keep the result suitable for a weekly team update.

## Validation

Run the dependency-free validator from this directory:

```bash
python3 validate_workflow.py
```

It checks that the exported workflow is valid JSON, contains the required
nodes, uses the requested Claude model, and does not contain literal secrets.
An n8n instance is required for an end-to-end delivery check.
