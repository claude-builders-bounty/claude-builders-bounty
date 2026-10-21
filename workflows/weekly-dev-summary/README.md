# Weekly Dev Narrative Summary Workflow (n8n + Claude Code)

Production-ready, exportable n8n workflow that automatically compiles a weekly narrative engineering summary from GitHub activity using the official Claude API (`claude-sonnet-4-20250514`).

---

## ⚡ Key Features
- **Cron Trigger:** Fires every Friday at 5:00 PM local time.
- **GitHub API Collector:** Fetches merged pull requests, closed issues, and recent commits over the past 7 days (`since = now - 7d`).
- **Claude Sonnet Narrative Engine:** Synthesizes raw commits/PRs into an executive Markdown briefing (Highlights, Fixes, Velocity, Next Focus).
- **Multi-Channel Dispatch:** Webhook delivery to Discord or Slack (with full Markdown formatting).
- **Configurable:** Repository (`OWNER/REPO`), Delivery Webhook, and Language (`EN` or `FR`).

---

## 🚀 5-Step Setup Instructions

1. **Import Workflow into n8n:**
   - In your n8n workspace, click **Add Workflow** -> **Import from File...**
   - Select `workflows/weekly-dev-summary/weekly_dev_summary_n8n.json`.

2. **Configure GitHub Credentials:**
   - Create a Header Auth Credential with:
     - Name: `Authorization`
     - Value: `Bearer <YOUR_GITHUB_PERSONAL_ACCESS_TOKEN>`

3. **Configure Claude API Credentials:**
   - Create a Header Auth Credential for Anthropic API:
     - Name: `x-api-key`
     - Value: `<YOUR_ANTHROPIC_API_KEY>`

4. **Set Repository & Webhook Variables:**
   - Open the **Set Config Variables** node and set:
     - `GITHUB_OWNER`: your GitHub org/username
     - `GITHUB_REPO`: your repository name
     - `DELIVERY_WEBHOOK_URL`: your Discord / Slack incoming webhook URL
     - `LANGUAGE`: `EN` or `FR`

5. **Activate the Workflow:**
   - Toggle the workflow switch to **Active** (runs every Friday at 5:00 PM).
   - Click **Test step** to trigger an immediate test summary.

---

## 📊 Sample Output
```markdown
# 🚀 Weekly Engineering Narrative: owner/repo
## 🌟 Key Highlights & Major Shipments
- Shipped zero-capital flash loan executor on Base L2 across Uniswap V3 and Aerodrome V2 (#43).
- Integrated pre-tool-use hook safety filter preventing destructive bash mutations.

## 🐛 Bug Fixes & Stability Improvements
- Resolved Postgres 63-byte identifier collision in inherited readability query.
- Corrected Pinecone connection test handling for accounts with zero active indexes.

## 📈 Subsystem Velocity & Community Contributors
- 12 PRs merged this week across core runtime and documentation subsystems.
- Special thanks to active contributors @PINYOPATTANAWASANPORN and team!

## 🔮 Next Week Focus
- On-chain flash loan gas telemetry tuning and multi-asset routing.
```
