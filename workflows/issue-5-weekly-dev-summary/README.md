# Weekly GitHub Activity Summary for n8n

This workflow generates a weekly narrative summary for a GitHub repository with Claude and posts it to Discord. It uses the Anthropic Messages API model `claude-sonnet-4-6`; Anthropic lists the issue's originally specified `claude-sonnet-4-20250514` model as retired and recommends `claude-sonnet-4-6` as its replacement ([model deprecations](https://docs.anthropic.com/en/docs/about-claude/model-deprecations)).

## Setup

1. Import `weekly-github-claude-summary.workflow.json` into n8n.
2. Set `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`, restart n8n, then set `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`, `ANTHROPIC_API_KEY`, `WEEKLY_SUMMARY_DISCORD_WEBHOOK_URL`, and optional `GITHUB_TOKEN` and `SUMMARY_LANGUAGE` (`EN` or `FR`).
3. Open the workflow, confirm the Friday 5pm schedule, and activate it.
4. Run the workflow manually once from the Schedule Trigger node.
5. Confirm Discord receives the summary, then leave the workflow active for weekly runs.

## Configuration

| Variable | Required | Example | Purpose |
| --- | --- | --- | --- |
| `GITHUB_REPO_OWNER` | Yes | `anthropics` | GitHub owner or organization. |
| `GITHUB_REPO_NAME` | Yes | `claude-code` | GitHub repository name. |
| `ANTHROPIC_API_KEY` | Yes | `sk-ant-...` | Claude API key used by the Anthropic Messages API. |
| `WEEKLY_SUMMARY_DISCORD_WEBHOOK_URL` | Yes | `https://discord.com/api/webhooks/...` | Discord webhook destination. |
| `SUMMARY_LANGUAGE` | No | `EN` or `FR` | Summary language. Defaults to `EN`. |
| `GITHUB_TOKEN` | No | `ghp_...` | Recommended for private repositories and higher GitHub API rate limits. |

## What it does

- Runs every Friday at 5pm.
- Fetches commits, recently closed issues, and recently merged PRs from the GitHub API for the last 7 days using n8n HTTP Request nodes.
- Executes each GitHub fetch node once, follows up to 10 API pages, and still produces a summary for a quiet week with no matching activity.
- Retries transient GitHub failures three times, then fails the workflow instead of generating a plausible-looking summary from partial activity. Reaching the 1,000-item pagination ceiling also fails closed.
- Sends those events to the active `claude-sonnet-4-6` model with a narrative summary prompt.
- Treats repository activity as untrusted data and tells Claude never to follow instructions embedded in commit messages, issue or PR titles, author names, or URLs.
- Posts the final summary to Discord. Combines text blocks in order and stops with an explicit error if Claude returns no usable text, instead of sending a placeholder.
- Disables Discord mention parsing so quoted repository or generated text cannot unexpectedly notify users, roles, or everyone.
- Trims unusually long Claude output before delivery so the Discord webhook stays below its message-size limit.

## Validation

For the remaining live acceptance check, use the separate
[owner-managed sandbox checklist](OWNER-SANDBOX.md). Owners retain their keys and
approve test spending themselves; no credentials belong in the PR. This does
not change the five-step setup above or claim a successful live execution.

The workflow JSON was validated locally with:

```bash
python workflows/issue-5-weekly-dev-summary/validate_workflow.py
```

Expected output is documented in `VERIFICATION.md`. The GitHub API requests are implemented with HTTP Request nodes because n8n Code nodes are for data preparation/transformation, not external HTTP calls. A live n8n execution screenshot still requires real `ANTHROPIC_API_KEY` and Discord webhook values in the target n8n instance.

The same validator and a deterministic greenfield smoke test run automatically in GitHub Actions for every change to this workflow.

GitHub Actions also evaluates both HTTP JSON body expressions with the actual
`n8n-workflow@2.32.1` resolver shipped with n8n `2.32.6`. These offline checks
verify that prompt and message data resolve into JSON objects without losing
quotes, newlines, Unicode, backslashes or expression-looking repository text.
See `VERIFICATION.md` for the isolated local command. They make no Anthropic or
Discord requests and do not replace the required successful live execution.
