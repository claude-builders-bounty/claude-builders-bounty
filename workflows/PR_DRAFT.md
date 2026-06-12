# PR Draft: Add n8n Weekly GitHub Dev Summary Workflow

Closes #5.

## Summary

- Adds an importable n8n workflow that runs every Friday at 5pm.
- Fetches weekly GitHub commits, closed issues, and merged PRs.
- Calls Claude Messages API with `claude-sonnet-4-20250514`.
- Sends the narrative summary to a Slack-compatible or Discord-compatible webhook.
- Documents setup in 5 steps and includes a workflow smoke validator.
- Includes local real n8n smoke execution screenshots and webhook delivery evidence.

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

## n8n Smoke Evidence

Evidence is included under `workflows/evidence/`:

- `n8n-executions-proof.png` - local n8n executions page showing Success, execution ID 2, runtime 1.688s.
- `n8n-execution-detail-proof.png` - execution detail page showing `Succeeded in 1.688s | ID#2`.
- `webhook-delivery-proof.png` - local webhook delivery page showing the received summary payload.
- `webhook-deliveries.json` - delivery JSON with metadata `repo=claude-builders-bounty/claude-builders-bounty`, `language=EN`, `commits=1`, `closedIssues=1`, `mergedPrs=1`.
- `n8n-execute-proof-output.json` - n8n CLI output showing business nodes succeeded and webhook delivery returned `{ ok: true, deliveries: 4 }`.

Boundary: this is local real n8n 1.97.1 smoke execution evidence with local mock GitHub, Claude, and webhook endpoints. It should not be read as a production Anthropic API call. The submitted workflow uses a Schedule Trigger; the smoke proof copy swaps only the trigger to Execute Workflow Trigger so n8n CLI can run it, while preserving the downstream GitHub fetch, Claude Messages POST, formatting, and webhook delivery chain.

## Local Submit Steps

```bash
git checkout bounty-5-weekly-dev-summary
git add README.md workflows/n8n-weekly-dev-summary.json workflows/README.md workflows/VERIFICATION.md workflows/validate_workflow.py workflows/evidence
git commit -m "Add n8n weekly dev summary workflow"
git push <your-fork> bounty-5-weekly-dev-summary
```

## Claim

After opening the PR, comment on issue #5:

```text
/opire try

Submitted PR: <PR URL>

This adds an importable n8n workflow for weekly GitHub activity summaries using Claude Sonnet 4 and webhook delivery. The PR includes setup docs, validator output, and local real n8n smoke execution + webhook delivery evidence.
```
