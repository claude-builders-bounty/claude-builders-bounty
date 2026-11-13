# Weekly GitHub Dev Summary → Claude → Slack/Discord

An n8n workflow that, every Friday at 5pm, pulls a repo's past-week **commits, merged PRs, and closed
issues** from the GitHub API, asks **Claude (`claude-sonnet-4-20250514`)** to write a narrative weekly
summary (English or French), and posts it to **Slack or Discord**.

Configurable: repo (`owner`/`repo`), destination (webhook), and `language` (`en`/`fr`).

## Setup (5 steps)

1. **Import** `weekly-dev-summary.json` into n8n (Workflows → Import from File).
2. **Add secrets** as environment variables on your n8n instance, then restart:
   - `GITHUB_TOKEN` — a GitHub token with read access to the repo
   - `SLACK_WEBHOOK_URL` — an incoming webhook (Slack) or a Discord webhook URL
   Create an **HTTP Header Auth** credential named `Anthropic x-api-key` (Header name `x-api-key`,
   value = your Anthropic API key) and select it on the **Claude Summary** node.
3. **Edit the `Config` node**: set `owner`, `repo`, and `language` (`en` or `fr`).
4. **(Optional) Adjust the schedule** on the trigger node — default cron is `0 17 * * 5` (Fri 5pm).
5. **Test**: click **Execute Workflow** once to confirm a summary posts, then toggle **Active**.

## Notes
- Discord: the webhook accepts `{ "content": "..." }` — if using Discord, change the body key in the
  **Post to Slack/Discord** node from `text` to `content`.
- The GitHub fetch runs in a single Code node (no per-item fan-out) and caps lists at 40 items each to
  keep the Claude prompt tight.
- For heavy repos, add a paginated fetch or narrow the window; the structure is ready for it.

Built by an automation specialist — myn8n-automation.org
