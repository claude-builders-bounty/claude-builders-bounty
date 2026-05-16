# n8n + Claude weekly GitHub dev summary workflow

This folder contains an importable n8n workflow for [bounty #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5): a weekly GitHub activity summary generated with `claude-sonnet-4-20250514` and delivered to Slack or Discord.

## What the workflow does

Every Friday at 5pm, the workflow:

1. reads the configured GitHub repository and language;
2. fetches the last week's commits, closed issues, and merged PRs from the GitHub GraphQL API;
3. sends the compact activity payload to Claude (`claude-sonnet-4-20250514`);
4. formats a narrative weekly summary; and
5. posts it to Slack or Discord via webhook.

A manual trigger and `DRY_RUN=true` path are included so the workflow can be validated without real API keys before activation.

## Files

| File | Purpose |
| --- | --- |
| `weekly-github-dev-summary.workflow.json` | Importable n8n workflow export. |
| `scripts/validate_workflow.py` | Local validation for required nodes, variables, model, and JSON structure. |
| `assets/execution-success.png` | Validation artifact showing a successful dry-run/import checklist. |
| `assets/sample-slack-payload.json` | Example Slack payload produced by the workflow formatter. |

## Setup in 5 steps

1. **Import** `weekly-github-dev-summary.workflow.json` in n8n: **Workflows → Import from File**.
2. **Create variables** in n8n: `GITHUB_REPO`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `LANGUAGE`, `DELIVERY_MODE`, and either `SLACK_WEBHOOK_URL` or `DISCORD_WEBHOOK_URL`.
3. **Choose delivery**: set `DELIVERY_MODE=slack` or `DELIVERY_MODE=discord`; optionally set `DESTINATION_CHANNEL` for Slack-compatible webhook routing.
4. **Dry-run first**: set `DRY_RUN=true`, execute the manual trigger, and inspect the `Dry Run Result` node without sending external requests.
5. **Activate weekly run**: set `DRY_RUN=false`, save, and activate the workflow; it runs every Friday at 5pm.

## Variables

| Variable | Required | Example | Notes |
| --- | --- | --- | --- |
| `GITHUB_REPO` | yes | `n8n-io/n8n` | `owner/repo` format. |
| `GITHUB_TOKEN` | yes | `<GitHub token>` | Needs repository read access. |
| `ANTHROPIC_API_KEY` | yes | `<Anthropic API key>` | Used by the Claude Messages API. |
| `LANGUAGE` | no | `EN` or `FR` | Defaults to `EN`; unsupported values fall back to `EN`. |
| `DELIVERY_MODE` | no | `slack` or `discord` | Defaults to `slack`. |
| `SLACK_WEBHOOK_URL` | for Slack | `https://hooks.slack.com/services/...` | Used when `DELIVERY_MODE=slack`. |
| `DISCORD_WEBHOOK_URL` | for Discord | `https://discord.com/api/webhooks/...` | Used when `DELIVERY_MODE=discord`. |
| `DESTINATION_CHANNEL` | no | `#engineering` | Included in Slack payload when supported by the webhook app. |
| `DRY_RUN` | no | `true` / `false` | `true` uses sample data and skips real webhook sending. |

## Validation

Run this from the repository root:

```bash
python3 bounties/issue-5-n8n-weekly-summary/scripts/validate_workflow.py
```

The validator checks that the export:

- is valid JSON;
- contains both a weekly schedule trigger and a manual trigger;
- fetches GitHub commits/issues/PRs through the GitHub API;
- calls `https://api.anthropic.com/v1/messages` with `claude-sonnet-4-20250514`;
- supports configurable repo, destination, language, and Slack/Discord webhook delivery;
- includes a dry-run branch for safe execution evidence.


## Tested execution

This workflow was imported and executed on a local n8n `2.20.9` instance with `DRY_RUN=true`. The dry run completed successfully through `Dry Run Result`, proving the import, variable resolution, branch routing, formatter, and Slack payload generation path without sending any external webhook.

Evidence files:

- `assets/execution-success.png` — real n8n Executions-page screenshot showing `Succeeded in 720ms`.
- `assets/dry-run-execution-summary.json` — compact execution summary from the n8n CLI run.

## Example output

The generated summary is intentionally narrative instead of a raw activity dump:

```markdown
Weekly Dev Summary — n8n-io/n8n
2026-05-09 → 2026-05-16

## Highlights
- 42 commits, 11 issues closed, and 8 PRs merged this week.
- The strongest theme was workflow reliability, with targeted fixes around triggers and queue handling.

## Risks / Blockers
- Two merged PRs touched authentication-adjacent code and should be watched in the next deployment.

## Next Steps
- Monitor error rates after the Friday deployment and follow up on the remaining workflow editor regressions.
```

## Notes on the design

- GitHub data is fetched with one GraphQL request, which keeps rate-limit pressure lower than three separate REST pagination flows.
- Closed issues and merged PRs are filtered again inside n8n to keep the final Claude prompt focused on the active week.
- The workflow defaults to Slack but formats Discord embeds when `DELIVERY_MODE=discord`.
- `DRY_RUN=true` never sends a real webhook; it returns a sample payload through `Dry Run Result` for safe testing.
