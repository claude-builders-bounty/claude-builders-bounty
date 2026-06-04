# Dry Run Output

Command:

```bash
node workflows/n8n-weekly-dev-summary/validate-workflow.mjs
```

Observed:

```json
{
  "ok": true,
  "workflow": "Weekly GitHub Dev Summary with Claude",
  "nodes": 8,
  "requiredNodes": [
    "Weekly Friday Trigger",
    "Fetch Commits",
    "Fetch Closed Issues",
    "Fetch Closed PRs",
    "Call Claude Sonnet 4",
    "Send Discord Webhook"
  ],
  "checks": {
    "importableJson": true,
    "weeklyCron": true,
    "githubCommits": true,
    "closedIssues": true,
    "mergedPRs": true,
    "claudeModel": true,
    "discordWebhook": true,
    "configurableVariables": true,
    "claudeEndpoint": true
  }
}
```

Note: Full live n8n execution requires a reviewer-provided `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, and Discord webhook URL. The workflow is exported as importable JSON and keeps secrets in environment variables.
