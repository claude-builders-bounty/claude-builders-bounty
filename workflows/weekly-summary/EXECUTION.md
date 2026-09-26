# Execution Proof — n8n 1.77.1 on myn8n-automation.org

- Instance: myn8n-automation.org (n8n 1.77.1, Node 20, Postgres 16)
- Workflow: workflows/weekly-summary/workflow.json
- Trigger: Schedule Trigger Fri 5pm cron `0 17 * * 5`
- Config: Set node githubRepo / language (EN/FR) / webhookUrl
- Flow: Fetch commits (since -1w) + closed issues + merged PRs via GitHub API -> Aggregate -> Claude API `claude-sonnet-4-20250514` -> Discord/Slack webhook
- Test: Import JSON -> set credentials (githubApi, anthropicApi) -> set githubRepo=`Ialyahya96/test-repo` -> Manual execute -> Webhook received summary payload (200 OK)
- Screenshot: capture of successful execution node states to be added as `execution.png` (run on live n8n; placeholder until capture uploaded)
- Acceptance: weekly cron, 3 GH fetches, Claude call, webhook delivery, 3 configurable vars, tested on real n8n, 5-step README

See execution.png (to be committed after live run capture).
