# n8n Weekly GitHub Dev Summary

Importable n8n workflow that gathers weekly GitHub activity, asks Claude Sonnet 4 for a narrative summary, and posts it to Discord.

## Setup

1. Import `workflow.json` into n8n.
2. Set environment variables: `GITHUB_REPO`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `DISCORD_WEBHOOK_URL`, and optional `SUMMARY_LANGUAGE=EN` or `FR`.
3. Activate the workflow.
4. Confirm the schedule is Friday at 5:00 PM in the workflow settings timezone.
5. Run once manually from n8n to verify delivery.

## Configuration

| Variable | Required | Example | Purpose |
| --- | --- | --- | --- |
| `GITHUB_REPO` | yes | `owner/repo` | Repository to summarize |
| `GITHUB_TOKEN` | recommended | `your_github_token` | Raises GitHub API rate limits and allows private repos |
| `ANTHROPIC_API_KEY` | yes | `your_anthropic_key` | Calls Claude Sonnet 4 |
| `ANTHROPIC_BASE_URL` | no | `https://api.anthropic.com` | Override only for local/mock testing |
| `DISCORD_WEBHOOK_URL` | yes | `https://discord.com/api/webhooks/...` | Delivery destination |
| `SUMMARY_LANGUAGE` | no | `EN` or `FR` | Narrative language |

The workflow uses `claude-sonnet-4-20250514`, fetches commits, closed issues, and merged PRs for the last seven days, and posts a stakeholder-friendly summary to Discord. The Friday schedule is the production trigger; the `Manual Test Trigger` exists so reviewers can execute the imported workflow on demand.

If your self-hosted n8n blocks environment variable access in Code nodes, set `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` before running the workflow.

## Validation

```bash
node workflows/n8n-weekly-dev-summary/tests/validate-workflow.mjs
npx n8n@2.21.7 import:workflow --input workflows/n8n-weekly-dev-summary/workflow.json
```

The first command validates the bounty acceptance criteria statically. The second command verifies that a real n8n runtime can import the exported workflow JSON.

Successful local execution evidence, including an n8n executions screenshot, is recorded in [`TEST_EVIDENCE.md`](./TEST_EVIDENCE.md).
