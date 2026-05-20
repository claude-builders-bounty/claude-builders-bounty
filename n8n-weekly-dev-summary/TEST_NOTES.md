# Test Notes

## Static Validation

The workflow JSON was parsed with Node.js:

```bash
node -e "JSON.parse(require('fs').readFileSync('n8n-weekly-dev-summary/weekly-dev-summary.workflow.json', 'utf8')); console.log('valid json')"
```

Checks performed:

- Contains an importable n8n workflow JSON object with `nodes`, `connections`, and `settings`.
- Contains a weekly Schedule Trigger for Friday at 17:00.
- Contains a Manual Trigger for test runs.
- Fetches GitHub commits, closed issues, and merged PRs for the last 7 days.
- Calls Anthropic Messages API with `claude-sonnet-4-20250514`.
- Sends the result to Discord webhook.
- Exposes required variables through environment variables.

## Execution Limitation

A full n8n execution screenshot is not included because this machine does not have a configured n8n instance, Anthropic API key, or Discord webhook secret available. An `npx n8n@latest import:workflow` attempt did not complete within a 5 minute timeout while starting n8n from npx, so the submitted verification is static JSON validation.

The workflow is designed so a maintainer can import it, set the documented environment variables, and run the Manual Trigger before publishing.
