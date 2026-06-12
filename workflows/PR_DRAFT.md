# PR Draft: Add n8n Weekly GitHub Dev Summary Workflow

Closes #5.

## Summary

- Adds an importable n8n workflow that runs every Friday at 5pm.
- Fetches weekly GitHub commits, closed issues, and merged PRs.
- Calls Claude Messages API with `claude-sonnet-4-20250514`.
- Sends the narrative summary to a Slack-compatible or Discord-compatible webhook.
- Documents setup in 5 steps and includes a workflow smoke validator.

## Acceptance Criteria

- Exportable n8n workflow: `workflows/n8n-weekly-dev-summary.json`
- Weekly cron trigger: Friday at 5pm
- GitHub API activity:
  - commits
  - closed issues
  - merged PRs
- Claude API model: `claude-sonnet-4-20250514`
- Delivery: Slack-compatible or Discord-compatible webhook
- Configurable variables:
  - `GITHUB_REPO`
  - `DESTINATION_WEBHOOK_URL`
  - `SUMMARY_LANGUAGE`
- README: `workflows/README.md`, 5 setup steps

## Verification

```bash
python3 workflows/validate_workflow.py
```

Observed:

```text
workflow validation passed
```

## Screenshot Note

The bounty requests a screenshot from a real n8n execution. I could not truthfully include that without an authenticated n8n instance, Anthropic key, and destination webhook. Before submitting the PR, import the workflow into n8n, run it once, and attach the successful execution screenshot plus webhook delivery screenshot.

## Local Submit Steps

```bash
git checkout bounty-5-weekly-dev-summary
git add README.md workflows/n8n-weekly-dev-summary.json workflows/README.md workflows/VERIFICATION.md workflows/validate_workflow.py
git commit -m "Add n8n weekly dev summary workflow"
git push <your-fork> bounty-5-weekly-dev-summary
```

## Claim

After opening the PR, comment on issue #5:

```text
/opire try

Submitted PR: <PR URL>

This adds an importable n8n workflow for weekly GitHub activity summaries using Claude Sonnet 4 and webhook delivery. The PR includes setup docs, validator output, and a real n8n execution screenshot.
```
