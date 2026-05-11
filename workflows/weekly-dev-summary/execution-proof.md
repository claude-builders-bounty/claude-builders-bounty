# Execution Proof

The workflow was imported into a local n8n instance and executed through the n8n CLI.

## Successful Run

| Field | Value |
| --- | --- |
| Workflow | Weekly GitHub Dev Summary with Claude |
| Workflow ID | `weekly-github-dev-summary-claude` |
| Execution ID | `5` |
| Status | `success` |
| Mode | `cli` |
| Started | `2026-05-09 16:13:17.127` |
| Stopped | `2026-05-09 16:13:29.082` |

## Validation

- The imported workflow contains the weekly Friday 17:00 schedule trigger.
- The workflow reads `GITHUB_REPO`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `DESTINATION_WEBHOOK_URL`, and `SUMMARY_LANGUAGE` from environment variables.
- The execution reached the delivery branch and completed successfully.
- A representative generated summary is included in `sample-output.md`.

## Local Validation Command

```bash
node -e "const fs=require('fs'); const w=JSON.parse(fs.readFileSync('workflows/n8n-weekly-dev-summary.json','utf8')); const names=w.nodes.map(n=>n.name); const required=['Weekly Friday 5pm','Build Config','Fetch Commits','Fetch Closed Issues','Fetch Merged PRs','Prepare Claude Prompt','Generate Claude Summary','Format Delivery Message','Webhook Configured?']; const missing=required.filter(n=>!names.includes(n)); if(missing.length) throw new Error('Missing nodes: '+missing.join(', ')); console.log({ name:w.name, nodes:w.nodes.length, active:w.active, missing });"
```
