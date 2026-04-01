# Weekly Dev Summary — n8n Workflow

Automatically generates a weekly narrative summary of a GitHub repository's activity using the Claude API and delivers it to Discord or Slack every Friday at 5 PM.

## Workflow Diagram

```
[Weekly Cron] → [Set Config] ──┬→ [Fetch Commits] ──┐
                                ├→ [Fetch Issues]  ──┤→ [Build Prompt] → [Claude API] → [Extract Summary] → [Send Summary]
                                └→ [Fetch PRs]     ──┘
```

## Setup (5 steps)

**Step 1 — Import the workflow**

In n8n: *Workflows → Import from file* → select `weekly-dev-summary.json`.

**Step 2 — Set environment variables**

Add these to your n8n instance (Settings → Environment Variables, or `.env` file if self-hosted):

| Variable | Description |
|---|---|
| `GITHUB_TOKEN` | GitHub personal access token (needs `repo` scope for private repos, no scope needed for public) |
| `CLAUDE_API_KEY` | Anthropic API key from [console.anthropic.com](https://console.anthropic.com) |

**Step 3 — Configure the Set Config node**

Open the **Set Config** node and update the values for your repo:

| Field | Default | Description |
|---|---|---|
| `repo_owner` | `n8n-io` | GitHub org or username |
| `repo_name` | `n8n` | Repository name |
| `language` | `EN` | Summary language: `EN` or `FR` |
| `webhook_url` | *(empty)* | Discord or Slack webhook URL (see Step 4) |
| `since_days` | `7` | How many days back to fetch activity |

**Step 4 — Get your webhook URL**

*Discord:* Server Settings → Integrations → Webhooks → New Webhook → Copy Webhook URL

*Slack:* Install the [Incoming Webhooks](https://slack.com/apps/A0F7XDUAZ-incoming-webhooks) app → Add to Workspace → Copy Webhook URL

Paste the URL into the `webhook_url` field in Set Config. The payload includes both `content` (Discord) and `text` (Slack) keys so the same URL format works for either platform.

**Step 5 — Activate the workflow**

Toggle the workflow active in the top-right corner of the n8n editor. It will run every Friday at 17:00 UTC.

To test immediately: open the workflow and click **Test workflow**.

---

## Example Output

```
📊 **Weekly Dev Summary — n8n-io/n8n**

This week saw 43 commits focused primarily on performance improvements to the
workflow execution engine and bug fixes in the HTTP Request node. Three major
features landed: improved error handling in Code nodes, OAuth2 PKCE support,
and a new Supabase integration. The team closed 12 issues and merged 8 PRs.

**Highlights:**
- feat: add PKCE support to OAuth2 credentials (#8821)
- fix: HTTP Request node ignores neverError option for 4xx (#8819)
- feat: Supabase node v2 with realtime subscriptions (#8803)
- fix: Code node loses context between executions (#8791)

📈 *43 commits · 12 issues closed · 8 PRs merged*
```

---

## Notes

- **No credentials stored in the workflow** — all secrets use `$env.VARIABLE_NAME` so they never appear in exported JSON.
- **GitHub API rate limits:** The workflow fetches up to 100 items per endpoint per run. Unauthenticated requests are limited to 60/hour; a `GITHUB_TOKEN` raises this to 5,000/hour.
- **Discord vs Slack:** The webhook payload includes both `content` and `text` fields. Discord reads `content`; Slack reads `text`. Both keys carry identical text so the same payload works for either.
- **Language options:** Set `language` to `EN` (English) or `FR` (French) in Set Config. Claude adapts the narrative language accordingly.
