# n8n + Claude: automated weekly dev summary

Every Friday at 17:00 this workflow reads a GitHub repo's activity for the last 7 days (commits, closed issues, merged PRs), asks Claude (`claude-sonnet-4-20250514`) to write a short narrative summary, and posts it to a **Discord or Slack webhook**.

```
Schedule -> Config -> Compute dates -> GitHub (commits, closed issues, merged PRs) -> Build prompt -> Claude -> Format -> Webhook
```

## Setup (5 steps)

1. **Import** `weekly-dev-summary.json` in n8n (Workflows -> Import from file).
2. **Anthropic key:** create a *Header Auth* credential named `Anthropic API Key` (Name: `x-api-key`, Value: your API key) and select it on the **Claude - Summarize** node.
3. **Webhook:** create an incoming webhook in Discord (Server Settings -> Integrations -> Webhooks) or Slack (an app with Incoming Webhooks).
4. **Configure:** open the **Config** node and set the variables below.
5. **Test and activate:** click *Execute workflow*, check your channel, then switch the workflow to *Active*.

## Configurable variables (Config node)

| Variable | Default | Meaning |
|---|---|---|
| `github_repo` | `owner/repo` | Repository to summarise, e.g. `n8n-io/n8n` |
| `language` | `EN` | `EN` or `FR`: language of the summary |
| `webhook_url` | placeholder | Discord or Slack incoming webhook URL (the destination channel) |
| `days` | `7` | Look-back window in days |
| `claude_model` | `claude-sonnet-4-20250514` | Claude model id |

## Notes

- **Schedule:** cron `0 17 * * 5` on the *Every Friday 17:00* node, in the timezone of the n8n instance (or the workflow's Settings -> Timezone). Edit the expression to change it.
- **Delivery:** the same payload carries `content` (read by Discord) and `text` (read by Slack), so one node serves both. Messages are cut at 1900 characters to fit Discord's 2000 limit.
- **Private repos / rate limits:** the GitHub calls are unauthenticated, which is enough for public repos (3 requests per run). For a private repo, set *Authentication* on the three `GitHub - ...` nodes to a GitHub credential.
- **Size cap:** at most 100 commits, 100 closed issues and 100 merged PRs per run are sent to Claude.
- **Quiet weeks:** with no activity Claude is told to say so in one sentence, so the channel still gets a message.
- The credential in the JSON is a placeholder (`REPLACE_ME`); no secrets are stored in the file.

## Execution screenshot

Not included yet: a screenshot must come from a real run on a live n8n instance with real credentials.
