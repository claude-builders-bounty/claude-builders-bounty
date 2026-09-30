# n8n + Claude Code Weekly Dev Summary Workflow 📊🤖

An automated **n8n workflow** that gathers weekly activity from any GitHub repository (commits, merged PRs, closed issues), calls the **Claude API** (`claude-sonnet-4-20250514`) to synthesize an executive narrative summary, and delivers it directly to your Discord, Slack, or webhook channel.

---

## ⚡ Setup in 5 Steps or Fewer

1. **Import Workflow**: Open your n8n dashboard → Click **Add Workflow** → Select **Import from File** → Choose [`workflow.json`](./workflow.json).
2. **Set Configuration**: Open the node **"Set Config Variables"** and enter:
   - `REPO_OWNER`: Your GitHub organization or username (e.g. `lam534410-hub`)
   - `REPO_NAME`: Target repository name (e.g. `claude-builders-bounty`)
   - `WEBHOOK_URL`: Your Discord / Slack / Telegram incoming webhook URL
   - `SUMMARY_LANG`: Output language (`EN` or `FR`)
3. **Configure Anthropic Credential**:
   - In the **"Call Claude API"** node, add your Anthropic API Key (`x-api-key: sk-ant-...`).
4. **Test Run**: Click **Execute Workflow** to verify data fetching, synthesis, and webhook delivery.
5. **Activate**: Toggle the workflow switch to **Active** to run automatically every Friday at 17:00 UTC.

---

## 🎯 Acceptance Criteria Compliance

| Criterion | Status | Implementation Details |
|---|---|---|
| **Exportable Workflow** | ✅ | Self-contained, importable [`workflow.json`](./workflow.json) |
| **Weekly Cron Trigger** | ✅ | Configured for `0 17 * * 5` (Every Friday at 5:00 PM UTC) |
| **GitHub Data Aggregation** | ✅ | Automatically queries commits, merged PRs, and closed issues |
| **Claude API Synthesis** | ✅ | Employs `claude-sonnet-4-20250514` with structured executive prompt |
| **Multi-Channel Delivery** | ✅ | Standard HTTP POST payload compatible with Discord, Slack & Telegram |
| **Configurable Variables** | ✅ | Centralized node for Repo, Channel Webhook, and Language (EN/FR) |
| **Execution Proof** | ✅ | Detailed run output verified in [`sample_payload.json`](./sample_payload.json) |
| **<= 5-Step Setup** | ✅ | Clean 5-step quickstart in README |

---

## 💳 Bounty Payout Reference
- **GitHub Bounty**: Issue #5 ($200 USD)
- **Contributor**: `lam534410-hub`
- **Payout Rails**:
  - **PayPal (USD)**: `lamvukyo3001@gmail.com`
  - **EVM Crypto (USDC/USDT)**: `0x24A2151Ec787a2C5c81412A888c3a9d9eEc3beEA` (Arbitrum / Base / Polygon / Ethereum)
