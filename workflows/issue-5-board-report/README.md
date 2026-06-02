# n8n Weekly GitHub Board Report

An importable n8n workflow for bounty #5. It runs every Friday at 5pm, collects the last week of GitHub commits, closed issues, and merged PRs, asks Claude `claude-sonnet-4-20250514` for a concise board-style narrative, and posts the result to Discord.

## 5-step setup

1. Import `weekly-board-report.workflow.json` into n8n.
2. Set environment variables: `GITHUB_REPO=owner/repo`, `GITHUB_TOKEN=...`, `ANTHROPIC_API_KEY=...`, `DISCORD_WEBHOOK_URL=...`, and optional `SUMMARY_LANGUAGE=EN` or `FR`.
3. Run **Manual Test Trigger** once to verify the GitHub, Claude, and Discord calls.
4. Activate the workflow; **Friday 5pm Schedule** uses cron `0 17 * * 5` in the workflow timezone.
5. Check Discord for the weekly report and n8n execution data for the audit JSON.

## Config

| Variable | Required | Description |
| --- | --- | --- |
| `GITHUB_REPO` | yes | Repository in `owner/repo` format. |
| `GITHUB_TOKEN` | yes | GitHub token with read access to the repository. |
| `ANTHROPIC_API_KEY` | yes | Claude API key for Messages API. |
| `DISCORD_WEBHOOK_URL` | yes | Destination Discord webhook. |
| `SUMMARY_LANGUAGE` | no | `EN` or `FR`; defaults to `EN`. |
| `LOOKBACK_DAYS` | no | Defaults to `7`; capped from 1 to 31. |
| `GITHUB_API_BASE_URL` | no | Defaults to `https://api.github.com`; useful for tests or GitHub Enterprise. |
| `ANTHROPIC_API_BASE_URL` | no | Defaults to `https://api.anthropic.com`; useful for tests. |

## What makes this version different

- Produces a leadership-ready board report instead of a raw activity dump.
- Includes an **Executive Pulse**, **Risk Radar**, **Contributor Spotlight**, and **Audit Trail**.
- Keeps traceable counts and sampled source activity in n8n execution data.
- Uses a manual trigger for real-instance testing without waiting for the weekly cron.

## Validation

Validation artifacts are included in this folder:

- `validate-workflow.mjs` parses the JSON, checks required nodes and cron/model configuration, and compiles embedded Code-node JavaScript.
- `mock-execution-server.mjs` provides local GitHub, Anthropic, and Discord-compatible endpoints for a real n8n dry run without secrets.
- `simulate-workflow.mjs` exercises the same data path outside n8n for quick smoke testing.
- `screenshots/successful-execution.png` shows the successful n8n CLI execution against the mock endpoints.

Real n8n CLI validation command used:

```bash
N8N_USER_FOLDER=/tmp/issue5-n8n-user \
N8N_BLOCK_ENV_ACCESS_IN_NODE=false \
GITHUB_REPO=example/board-report \
GITHUB_TOKEN=ghp_mock \
ANTHROPIC_API_KEY=sk-ant-mock \
DISCORD_WEBHOOK_URL=http://127.0.0.1:8877/discord \
GITHUB_API_BASE_URL=http://127.0.0.1:8877 \
ANTHROPIC_API_BASE_URL=http://127.0.0.1:8877 \
SUMMARY_LANGUAGE=EN \
npx -y n8n@2.23.2 execute --id issue-5-board-report
```

The run finished with `status: "success"` and `lastNodeExecuted: "Send Discord Board Report"`.
