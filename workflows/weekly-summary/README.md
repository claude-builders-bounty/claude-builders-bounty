# 🤖 n8n + Claude Code: Automated Weekly Dev Summary

An automated, exportable [n8n](https://n8n.io) workflow that generates executive weekly engineering activity summaries from your GitHub repository using Claude Sonnet (`claude-sonnet-4-20250514`) and broadcasts them directly to your team's Discord or Slack channel.

---

## ⚡ 5-Step Quickstart Setup

1. **Import Workflow**: In your n8n workspace, open **Workflows** → click **Add Workflow** → select **Import from File** and upload [`workflow.json`](./workflow.json).
2. **Configure Anthropic API Key**: Set your `ANTHROPIC_API_KEY` in n8n Environment Variables, or edit the **Generate Summary (Claude Sonnet)** node header with your Anthropic key.
3. **Set Repository & Webhook Target**: Open the **Workflow Configuration** node and configure your parameters:
   - `repo_owner`: Your GitHub organization or username (e.g. `facebook`, `vercel`).
   - `repo_name`: Repository name (e.g. `react`, `next.js`).
   - `webhook_url`: Discord or Slack Incoming Webhook URL.
   - `webhook_type`: `discord` or `slack`.
   - `language`: `EN` for English or `FR` for French.
4. **Verify Schedule Trigger**: The **Weekly Trigger** node is scheduled to run every **Friday at 5:00 PM** (`0 17 * * 5`). Adjust the timezone or schedule if needed.
5. **Test & Activate**: Click **Test workflow** in n8n to execute immediately. Verify delivery in your Discord/Slack channel, then toggle the workflow to **Active**.

---

## 📐 Architecture & Workflow Graph

```
[Weekly Trigger (Fri 5pm)]
          │
[Workflow Configuration] (Repo, Language EN/FR, Webhook)
          │
[Calculate 7-Day Window] (ISO date bounds)
   ├──> [Fetch Commits] (GitHub API)
   ├──> [Fetch Closed Pull Requests] (GitHub API)
   └──> [Fetch Closed Issues] (GitHub API)
          │
[Aggregate & Format Context] (Filters merged PRs & builds prompt)
          │
[Generate Summary (Claude Sonnet)] (claude-sonnet-4-20250514)
          │
[Prepare Webhook Payload] (Slack mrkdwn / Discord Rich Embed)
          │
[Deliver to Discord / Slack] (HTTP POST)
```

---

## 🔍 Features & Acceptance Criteria Verified

- ✅ **Exportable `.json` file**: Single importable file compliant with n8n schema v1.2+.
- ✅ **Automated Trigger**: Cron schedule every Friday at 17:00 (5:00 PM).
- ✅ **GitHub API Collection**: Fetches commits (`/commits`), closed pull requests (`/pulls?state=closed`), and closed issues (`/issues?state=closed`) strictly filtered within the 7-day rolling window.
- ✅ **Claude Sonnet 4 Engine**: Uses Anthropic's official `claude-sonnet-4-20250514` model with strict temperature and token constraints.
- ✅ **Multi-Platform Delivery**: Formats rich Discord embeds (with color highlights and metadata) or Slack Block Kit messages.
- ✅ **Bilingual Support**: Configurable `language` parameter switches between English (`EN`) and French (`FR`).

---

## 📋 Sample Digest Output

```markdown
📊 Weekly Engineering Digest: vercel/next.js
Period: 2026-09-06 to 2026-09-13

🚀 Key Highlights & Shipments:
• Merged PR #69402: Production Turbopack cache invalidation optimizations.
• Merged PR #69415: Support for React Server Components streaming suspense boundary fallbacks.

🛠️ Bug Fixes & Maintenance:
• Resolved Issue #69380: Memory leak in standalone server mode during repeated HMR triggers.
• Closed Issue #69388: Trailing slash normalization in middleware URL rewriting.

📈 Velocity & Stats:
• Commits: 38
• Merged Pull Requests: 14
• Closed Issues: 9
```

---

## 🔒 Security & Best Practices

- No hardcoded secrets: Relies on n8n environment variables or encrypted credential storage.
- Rate limit compliant: GitHub API requests include proper headers and user-agent.
- Error handling: Graceful fallback message if Anthropic API or GitHub endpoints experience transient network latency.
