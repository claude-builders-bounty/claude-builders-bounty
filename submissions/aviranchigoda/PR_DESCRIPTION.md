## Summary

Implements issue #5 with an importable n8n workflow that sends a weekly GitHub activity summary to Slack using Claude Sonnet 4.

## Deliverables

- `weekly-dev-summary.workflow.json` - importable n8n workflow.
- `code-nodes/` - readable source for the embedded n8n Code nodes.
- `generate-workflow.mjs` - regenerates the workflow JSON from readable Code-node files.
- `check-acceptance.mjs` - verifies local coverage of the issue #5 acceptance criteria and records remaining approval-gated real evidence.
- `validate-mock-execution.mjs` - imports and executes the workflow in n8n 2.20.11 with mocked Claude and Slack endpoints.
- `validate-real-execution.mjs` - approval-gated real endpoint runner that writes sanitized evidence when `ANTHROPIC_API_KEY` and `SLACK_WEBHOOK_URL` are supplied.
- `evidence/acceptance-check-result.json` - latest local acceptance-coverage check result.
- `evidence/mock-execution-result.json` - sanitized output from the successful mock n8n execution.
- `evidence/mock-n8n-execution-ui.png` - n8n UI screenshot of the successful local mock execution.
- `README.md` - setup instructions in five steps.
- `example-summary.md` - example Slack-ready summary output.

## Acceptance Criteria Coverage

- Runs on schedule: includes `Weekly Friday 5pm` Schedule Trigger.
- Manual test path: includes `Manual Test Trigger`.
- Connects to GitHub API: fetches commits, closed issues, and merged PRs for the configured lookback window.
- Connects to Claude API: calls `claude-sonnet-4-20250514` through an n8n HTTP Request node.
- Sends formatted weekly summary: posts Claude output to a Slack incoming webhook.
- Configurable target: `Configure Summary` controls GitHub owner/repo, language, lookback window, Slack webhook, and optional Slack channel.
- Test evidence: `evidence/mock-execution-result.json` shows successful n8n import and execution with mocked Claude/Slack endpoints and real public GitHub API calls.
- UI evidence: `evidence/mock-n8n-execution-ui.png` shows the same local n8n execution succeeded in the Executions tab.

## Local Validation

```bash
node submissions/aviranchigoda/generate-workflow.mjs
jq empty submissions/aviranchigoda/weekly-dev-summary.workflow.json
node submissions/aviranchigoda/check-acceptance.mjs
node submissions/aviranchigoda/validate-mock-execution.mjs
node submissions/aviranchigoda/validate-real-execution.mjs # requires ANTHROPIC_API_KEY and SLACK_WEBHOOK_URL
```

Latest mock validation result:

```json
{
  "status": "passed",
  "n8nPackage": "n8n@2.20.11",
  "importedWorkflow": true,
  "executedWorkflow": true,
  "claudeEndpointCalled": true,
  "slackEndpointCalled": true,
  "finalStatus": "delivered",
  "destination": "slack"
}
```

## Notes

The workflow keeps external API calls in n8n HTTP Request nodes. Code nodes only configure, shape, and summarize data. GitHub HTTP nodes preserve empty arrays so quiet weeks still produce and deliver a summary.
