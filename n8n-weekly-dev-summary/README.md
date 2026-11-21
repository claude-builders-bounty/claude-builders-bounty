# Weekly Dev Summary — n8n + Claude API

Every Friday at 17:00, pull the week's commits, closed issues, and
merged PRs from a GitHub repo, ask Claude for a narrative summary, and
post it to a Discord channel.

## Setup (5 steps)

1. Import `workflow.json` into n8n (Workflows → Import from File).
2. Open the **Config** node and set `github_repo` (`owner/repo`),
   `discord_webhook_url`, `anthropic_api_key`, and `language`
   (`EN` or `FR`).
3. Optionally change `anthropic_base_url` (defaults to the Anthropic
   API).
4. Activate the workflow.
5. Done — a summary posts every Friday 17:00; run once manually to
   verify.

## What it does

- **Friday 5pm Trigger** — cron `0 17 * * 5`
- **Fetch Commits / Closed Issues / Closed PRs** — GitHub REST,
  last-7-days windows (`since` for commits+issues, `merged_at`
  filtering for PRs)
- **Build Prompt** — aggregates the three feeds into one prompt;
  switches narrative language on `language` (EN/FR)
- **Claude Summary** — `POST /v1/messages` with
  `claude-sonnet-4-20250514`
- **Post to Discord** — delivers the narrative to the configured
  webhook (swap for Slack/email by replacing this node)

## Configuration

| Variable | Where | Notes |
|----------|-------|-------|
| `github_repo` | Config node | `owner/repo`, any public repo |
| `discord_webhook_url` | Config node | Discord channel webhook |
| `language` | Config node | `EN` or `FR` |
| `anthropic_api_key` | Config node | Anthropic API key |
| `anthropic_base_url` | Config node | API base, defaults to Anthropic |

`execution.png` shows a successful end-to-end run.
