# Test Notes

Tested on 2026-05-15 with `n8n@2.20.8` in an isolated `N8N_USER_FOLDER`.

Commands run:

```powershell
node workflows\n8n-weekly-dev-summary\build-workflow.mjs
npx -y n8n@2.20.8 import:workflow --input workflows\n8n-weekly-dev-summary\weekly-dev-summary.workflow.json
npx -y n8n@2.20.8 execute --id=weekly-github-dev-summary-claude
```

Result:

```text
Importing 1 workflows...
Successfully imported 1 workflow.

"status": "success",
"finished": true
```

The test left `dryRun: true`, so GitHub API fetches ran against `claude-builders-bounty/claude-builders-bounty`, and the Claude and Discord HTTP requests were sent to Postman Echo instead of production endpoints. The production path is enabled by setting `dryRun: false`, `anthropicApiKey`, and `discordWebhookUrl` in the `Set Config` node.

No live Anthropic API key or Discord webhook is committed to this repository. The dry run verifies the n8n import, trigger path, GitHub API pagination, Claude request construction, Discord payload construction, and HTTP delivery nodes without exposing private credentials.

Screenshot: `screenshots/successful-execution.png`.
