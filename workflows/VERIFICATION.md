# Verification Notes

Local checks completed:

- Parsed `workflows/n8n-weekly-dev-summary.json` as valid JSON.
- Confirmed required node types are present:
  - `n8n-nodes-base.scheduleTrigger`
  - `n8n-nodes-base.httpRequest`
  - `n8n-nodes-base.code`
  - `n8n-nodes-base.set`
- Confirmed configurable variables are referenced:
  - `GITHUB_REPO`
  - `GITHUB_TOKEN`
  - `ANTHROPIC_API_KEY`
  - `DESTINATION_WEBHOOK_URL`
  - `SUMMARY_LANGUAGE`

Pending maintainer/user-side evidence:

- Import into a real n8n instance.
- Run a manual execution against a real repository.
- Attach a screenshot showing successful execution and webhook delivery.

This environment does not have an authenticated n8n instance, Anthropic API key, or destination webhook, so the live screenshot must be produced after import.
