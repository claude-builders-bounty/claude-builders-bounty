# n8n + Claude Code Automated Weekly Dev Summary (#5)

> 💰 Bounty: $200 — powered by [Opire](https://opire.dev)

A complete, production-ready n8n workflow that automatically aggregates a GitHub repository's weekly activity (commits, closed issues, merged PRs) and invokes the Claude API (`claude-sonnet-4-20250514`) to synthesize a narrative developer digest, delivered automatically to Discord and/or Slack webhooks every Friday at 5:00 PM.

---

## ⚡ Quickstart Setup in 5 Steps or Fewer

1. **Import Workflow**: Open your n8n dashboard, click **Workflows** → **Import from File**, and select [`github-weekly-claude-summary.json`](github-weekly-claude-summary.json).
2. **Set Environment Variables**: Set the following in your n8n environment or via the workflow's **Init Config & Date Range** node:
   ```env
   ANTHROPIC_API_KEY=sk-ant-api03-...
   GITHUB_TOKEN=ghp_...
   GITHUB_OWNER=your-org-or-username
   GITHUB_REPO=your-repo-name
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
   ```
3. **Configure Language & Channel**: Choose `SUMMARY_LANGUAGE` (`EN`, `FR`, `VI`, etc.) and `DELIVERY_CHANNEL` (`discord`, `slack`, or `both`).
4. **Test Run**: Click **Test workflow** in n8n to execute manually and preview the generated digest in your target channel.
5. **Activate**: Toggle the workflow switch to **Active** to enable the Friday 5:00 PM cron schedule (`0 17 * * 5`).

---

## 🏗️ Architecture & Pipeline Flow

```
+-------------------------------------------------------------+
|               Friday 17:00 Weekly Cron Trigger              |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|             Init Config & 7-Day Dynamic Window              |
+--------------+---------------+----------------+-------------+
               |               |                |
               v               v                v
     +-----------------+ +------------+ +---------------+
     |  Fetch Commits  | | Closed Iss | |  Merged PRs   |
     +---------+-------+ +-----+------+ +-------+-------+
               |               |                |
               +---------------+----------------+
                               |
                               v
+-------------------------------------------------------------+
|       Aggregate Activity Data (Stats, Commits, PRs)         |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|      Claude API (claude-sonnet-4-20250514) Synthesis        |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|        Format Discord Embed & Slack Block Payloads          |
+------------------------------+------------------------------+
               |                                |
               v                                v
+------------------------------+ +----------------------------+
|      Post to Discord         | |       Post to Slack        |
+------------------------------+ +----------------------------+
```

---

## ⚙️ Configuration Variables

| Variable | Description | Default | Required? |
|---|---|:---:|:---:|
| `ANTHROPIC_API_KEY` | Anthropic Claude API Key | — | **Yes** |
| `GITHUB_OWNER` | Target GitHub repository owner | — | **Yes** |
| `GITHUB_REPO` | Target GitHub repository name | — | **Yes** |
| `GITHUB_TOKEN` | GitHub PAT to prevent rate limiting (5,000 req/hr) | — | Recommended |
| `DISCORD_WEBHOOK_URL`| Destination Discord channel webhook URL | — | Optional* |
| `SLACK_WEBHOOK_URL`  | Destination Slack incoming webhook URL | — | Optional* |
| `SUMMARY_LANGUAGE`   | Output language (`EN`, `FR`, `ES`, `DE`, `VI`) | `EN` | No |
| `DELIVERY_CHANNEL`   | Delivery routing target (`discord`, `slack`, `both`) | `both` | No |

*\*At least one webhook destination (Discord or Slack) should be configured.*

---

## 🧪 Automated Verification Test

Run the included verification suite to validate the workflow JSON structure, node linkage, expressions, and Claude prompt formatting:

```bash
python test_workflow.py
```
