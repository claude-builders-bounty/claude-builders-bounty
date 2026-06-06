# Validation Evidence

Local validation was run without embedding real API keys or webhook secrets.

Commands:

```bash
node workflows/n8n-weekly-dev-summary/validate-workflow.mjs
git diff --check
```

Expected validator result:

```text
Workflow validation passed: 9 nodes, 5 setup steps.
```

The workflow uses environment variables for all secrets and is ready for a real n8n manual execution once `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, and `DISCORD_WEBHOOK_URL` are supplied.
