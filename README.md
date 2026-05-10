# GitHub Weekly Dev Summary — n8n + Claude Code

**Bounty Issue:** [#5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)

An n8n workflow that runs every Friday at 5 PM, fetches a GitHub repo's activity for the past 7 days (commits, closed issues, merged PRs), generates a narrative summary using Claude Sonnet 4, and delivers it via Discord webhook.

---

## Setup — 5 Steps

### Step 1 — Import Workflow
Download `n8n-workflow.json` from this PR. In your n8n instance, go to **Settings → Import from File** and select the file.

### Step 2 — Add Credentials

**GitHub Personal Access Token**
- Go to [github.com/settings/tokens](https://github.com/settings/tokens)
- Create a classic token with `repo` scope
- In n8n, create a **Header Auth** credential named `GitHub` with header `Authorization: Bearer YOUR_TOKEN`

**Anthropic API Key**
- Get a key from [console.anthropic.com](https://console.anthropic.com)
- In n8n, each HTTP Request node that calls Claude will use **Query Auth** with your API key as the `x-api-key` parameter

### Step 3 — Configure the `Config` Node
Open the **Config** node and fill in your values:

| Variable | Description |
|---|---|
| `REPO_OWNER` | GitHub org or username (e.g. `my-org`) |
| `REPO_NAME` | Repository name (e.g. `my-repo`) |
| `GITHUB_TOKEN` | Your GitHub PAT |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `DISCORD_WEBHOOK` | Your Discord webhook URL |
| `LANGUAGE` | `EN` (default) or `FR` for French output |

### Step 4 — Configure HTTP Auth on Claude Node
The **Claude Generate Summary** node uses **Query Auth** with your Anthropic key. Verify the `anthropic-version` query param is set to `2023-06-01`.

### Step 5 — Test & Activate
Click **Execute Workflow** to run it immediately. Once you see the summary appear in Discord, toggle the switch to **Active** — it will now run every Friday at 5:00 PM automatically.

---

## How It Works

```
[Schedule: Fri 5PM]
       ↓
[Config — repo, webhook, language]
       ↓
[Calculate date range: last 7 days]
       ↓
[Fetch Commits (7d)] → [Fetch Closed Issues (7d)] → [Fetch Merged PRs (7d)]
       ↓
[Aggregate GitHub Data — filter & normalize]
       ↓
[Claude Sonnet 4 — generate narrative summary]
       ↓
[Send to Discord]
```

## Acceptance Criteria — All Met

- ✅ Exportable `.json` — import directly into n8n
- ✅ Trigger: `0 17 * * 5` — every Friday at 5:00 PM
- ✅ Fetches: commits, closed issues, merged PRs (7-day window)
- ✅ Claude API: model `claude-sonnet-4-20250514`
- ✅ Delivery: Discord webhook
- ✅ Configurable: `REPO_OWNER`, `REPO_NAME`, `DISCORD_WEBHOOK`, `LANGUAGE`
- ✅ Multilingual: EN and FR supported via `LANGUAGE` config

## Customization

To use **Slack** instead of Discord, replace the **Send to Discord** node with an HTTP Request node posting to your Slack webhook URL with body `{"text": "..."}`.

---

*Built as a bounty submission for [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty).*