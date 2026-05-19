# Weekly GitHub Activity Summary with Claude

Submission for issue #5. The workflow runs every Friday at 5pm, fetches weekly GitHub activity, asks Claude Sonnet 4 to write a narrative update, and posts the result to Slack.

## Files

- `weekly-dev-summary.workflow.json` - importable n8n workflow.
- `code-nodes/` - readable copies of the Code node logic embedded in the workflow.
- `generate-workflow.mjs` - local generator used to keep readable Code node files in sync with the workflow export.
- `REAL_EVIDENCE.md` - approval-gated runbook for producing real Anthropic/Slack evidence and the real n8n screenshot.
- `check-acceptance.mjs` - local acceptance-coverage check for the issue #5 requirements.
- `validate-mock-execution.mjs` - local validation harness that imports and runs the workflow with mocked Claude and Slack endpoints.
- `validate-real-execution.mjs` - approval-gated validation harness for real Anthropic and Slack endpoints using environment-provided credentials.
- `evidence/acceptance-check-result.json` - latest local acceptance-coverage check result.
- `evidence/mock-execution-result.json` - sanitized evidence from the latest successful mock n8n execution.
- `evidence/mock-n8n-execution-ui.png` - screenshot of the successful local n8n execution using mocked Claude and Slack endpoints.
- `PR_DESCRIPTION.md` - PR-ready submission notes for issue #5.
- `example-summary.md` - sample Slack-ready output format.

## Setup

1. Import `weekly-dev-summary.workflow.json` into n8n.
2. Open `Configure Summary` and set `githubOwner`, `githubRepo`, `summaryLanguage` (`EN` or `FR`), `lookbackDays`, `anthropicApiKey`, `slackWebhookUrl`, and optional `slackChannel`.
3. If the repository is private or rate limited, add a GitHub `Authorization: Bearer ...` header to the three GitHub HTTP Request nodes.
4. Run `Manual Test Trigger` and confirm the Slack message plus the n8n execution output.
5. Activate the workflow so `Weekly Friday 5pm` sends the summary automatically.

## Notes

- The Claude API call uses `claude-sonnet-4-20250514`.
- GitHub data includes commits, closed issues, and merged pull requests for the configured lookback window.
- Slack incoming webhook delivery is used as the documented destination.
- `summaryLanguage = "FR"` switches the generated summary to French.
- HTTP calls are handled by n8n HTTP Request nodes; Code nodes only configure and transform data.
- GitHub HTTP nodes preserve empty arrays so quiet weeks still produce a summary instead of stopping the workflow.
- `check-acceptance.mjs --require-real-evidence` can be used after real endpoint evidence is captured to enforce the remaining screenshot gate and validate screenshot PNG dimensions.
- `validate-real-execution.mjs` can generate sanitized real-run evidence from `ANTHROPIC_API_KEY` and `SLACK_WEBHOOK_URL` without committing credentials.
