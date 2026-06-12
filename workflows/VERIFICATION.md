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
- Run a manual execution against a real repository or smoke endpoints.
- Attach a screenshot showing successful execution and webhook delivery.

## Local Real n8n Smoke Evidence

Evidence has been added under `workflows/evidence/`:

- `n8n-executions-proof.png` shows the local n8n executions page with workflow `Weekly GitHub Dev Summary with Claude - Local Execute Proof`, execution ID 2, status Success, and runtime 1.688s.
- `n8n-execution-detail-proof.png` shows the execution detail page with `Jun 13 00:31:16` and `Succeeded in 1.688s | ID#2`.
- `webhook-delivery-proof.png` shows the local webhook delivery page receiving the final summary payload.
- `webhook-deliveries.json` records the delivered payload; the final delivery metadata includes `repo=claude-builders-bounty/claude-builders-bounty`, `language=EN`, `commits=1`, `closedIssues=1`, and `mergedPrs=1`.
- `n8n-execute-proof-output.json` records the n8n CLI execution output, with business nodes succeeding and webhook delivery returning `{ ok: true, deliveries: 4 }`.

Boundary: this is local real n8n 1.97.1 smoke execution evidence with mocked GitHub, Claude, and webhook endpoints. It should not be represented as a production Anthropic API call. The submitted workflow uses a Schedule Trigger; the CLI smoke proof copy replaces only that trigger with Execute Workflow Trigger because n8n CLI cannot directly execute a schedule trigger. The downstream GitHub fetch, Claude Messages POST, formatting, and webhook delivery chain remains equivalent for smoke verification.
