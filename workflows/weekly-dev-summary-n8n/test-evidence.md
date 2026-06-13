# Test Evidence

## Local Validation

The workflow JSON was parsed locally as valid JSON:

```text
node -e "JSON.parse(require('fs').readFileSync('workflows/weekly-dev-summary-n8n/weekly-dev-summary.workflow.json','utf8')); console.log('valid')"
```

Expected output:

```text
valid
```

## n8n Manual Execution Checklist

Use this checklist after importing the workflow into a real n8n instance:

1. Confirm the `Weekly Friday 5pm` node shows a weekly Friday trigger at 17:00 UTC.
2. Set `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`, `SUMMARY_LANGUAGE`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, and `DISCORD_WEBHOOK_URL`.
3. Run `Execute workflow`.
4. Confirm the GitHub API nodes return commits, closed issues, and pull requests.
5. Confirm the Claude node returns a narrative summary and the Discord node posts it.

## Note

This repository does not include an n8n runtime or external API credentials, so the committed test evidence is limited to workflow JSON validation and a reproducible manual execution checklist.
