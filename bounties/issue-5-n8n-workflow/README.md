# Weekly GitHub Dev Summary — n8n + Claude Workflow

> **Bounty:** [issue #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5) · $200 via Opire

An importable n8n workflow that automatically generates a **weekly narrative summary** of any GitHub repository's activity using the Claude API, delivered to Discord every Friday at 5 PM.

---

## Setup in 5 steps

### 1. Import the workflow

In your n8n instance, go to **Workflows → Import from file** and select `workflow.json`.

> 💡 Need n8n? Run it locally with Docker:
> ```bash
> docker run -it --rm -p 5678:5678 n8nio/n8n
> ```
> Then open `http://localhost:5678`

---

### 2. Configure the `Config` node

Open the **Config** node and update the 5 variables:

| Variable | Description | Example |
|---|---|---|
| `GITHUB_REPO` | Target repository (owner/repo) | `vercel/next.js` |
| `LANGUAGE` | Summary language | `EN` or `FR` |
| `DISCORD_WEBHOOK_URL` | Discord incoming webhook URL | `https://discord.com/api/webhooks/...` |
| `GITHUB_TOKEN` | GitHub personal access token (read:repo scope) | `ghp_xxx...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-xxx...` |

**Get a Discord webhook:** Server Settings → Integrations → Webhooks → New Webhook → Copy URL

**Get a GitHub token:** [github.com/settings/tokens](https://github.com/settings/tokens) — scope: `repo` (read-only)

---

### 3. Set the cron trigger

The **Schedule Trigger** is pre-configured for **Friday at 17:00**. To change it, open the node and adjust the day/hour.

---

### 4. Activate the workflow

Toggle the workflow **Active** switch (top right in n8n). It will now run automatically every Friday at 5 PM.

---

### 5. Test manually

Click **Execute Workflow** to run it immediately and verify your configuration. Check Discord for the summary embed.

---

## Workflow architecture

```
Schedule Trigger (Friday 17h)
        │
        ▼
   Config (Set Variables)
        │
        ▼
Fetch GitHub Data (Code node)
 ├── GET /repos/{repo}/commits?since=7d
 ├── GET /repos/{repo}/issues?state=closed&since=7d
 └── GET /repos/{repo}/pulls?state=closed (filtered: merged in 7d)
        │
        ▼
Call Claude API (HTTP Request)
 └── POST https://api.anthropic.com/v1/messages
     model: claude-sonnet-4-20250514
        │
        ▼
Format Discord Message (Code node)
 └── Builds Discord embed with summary + stats
        │
        ▼
Send to Discord (HTTP Request)
 └── POST to Discord webhook URL
```

---

## Discord output

The bot sends a rich embed with:
- 📝 Narrative summary (300–500 words, in EN or FR)
- 📦 Commit count
- 🔧 Issues closed count
- 🔀 PRs merged count
- 📅 Week period covered

---

## Notes

- **GitHub API rate limits:** 5,000 req/hour for authenticated requests (fine for weekly runs)
- **Claude model:** `claude-sonnet-4-20250514` — change in the `Fetch GitHub Data` code node if needed
- **Slack instead of Discord?** Replace the `Send to Discord` HTTP node URL with your Slack webhook and update the payload format in `Format Discord Message` to use Slack's block kit format
- **Language:** Set `LANGUAGE` to `EN` (default) or `FR` — the prompt instruction switches automatically
