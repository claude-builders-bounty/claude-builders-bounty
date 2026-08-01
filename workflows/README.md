# n8n Weekly Dev Summary

Import `n8n-weekly-dev-summary.json` into n8n to send a Friday 5pm
development summary for a GitHub repository.

## Setup

1. Import `workflows/n8n-weekly-dev-summary.json` into n8n.
2. Configure environment variables:
   - `GITHUB_REPO`, for example `owner/repo`
   - `GITHUB_TOKEN`
   - `ANTHROPIC_API_KEY`
   - `SUMMARY_EMAIL_TO`
   - `SUMMARY_LANGUAGE`, either `EN` or `FR`
3. Configure the n8n Email Send credential for your SMTP provider and activate
   the workflow.
4. Run the workflow once manually to verify the GitHub fetch, Claude summary,
   and email delivery.
5. Leave it active for the weekly Friday 5pm schedule.

The workflow fetches commits, closed issues, and merged pull requests from the
last seven days, asks `claude-sonnet-4-20250514` for a narrative summary, then
sends the generated text by email.

## Validation

Run the static workflow checks:

```bash
python3 scripts/validate_n8n_workflow.py
```

Run the checks plus a live GitHub API dry run without calling Claude or sending
email:

```bash
python3 scripts/validate_n8n_workflow.py --live-repo n8n-io/n8n
```

The live dry run fetches commits, closed issues, and merged pull requests for
the previous seven days, then verifies that the workflow can construct the
Claude Messages request for `claude-sonnet-4-20250514`.
