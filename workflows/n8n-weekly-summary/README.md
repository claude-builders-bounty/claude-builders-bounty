# n8n + Claude Code: Automated Weekly Dev Summary ⚙️

An automated workflow for [n8n](https://n8n.io) that runs every Friday, extracts GitHub engineering activity (commits, merged PRs, closed issues) over the past 7 days, synthesizes an executive narrative summary with the Anthropic Claude API (`claude-sonnet-4-20250514`), and dispatches it directly to Discord or Slack.

Bounty #5 submission for **Claude Builders Bounty** ($200 — powered by Opire).

---

## ⚡ Setup Instructions (4 Steps)

### Step 1: Import Workflow into n8n
1. Open your n8n workspace (self-hosted or n8n cloud).
2. Go to **Workflows** → Click **Import from File**.
3. Select `workflows/n8n-weekly-summary/n8n-weekly-dev-summary.json`.

### Step 2: Configure Environment Credentials
Ensure your n8n environment has the Anthropic API credential configured:
- Set environment variable `ANTHROPIC_API_KEY=sk-ant-...` (or configure via n8n Credentials).

### Step 3: Set Your Repository & Target Channel
Click on the **"Configuration Variables"** node in the workflow canvas and update:
- `GITHUB_OWNER`: Your GitHub organization or username (e.g. `claude-builders-bounty`)
- `GITHUB_REPO`: Your repository name (e.g. `claude-builders-bounty`)
- `SUMMARY_LANGUAGE`: `EN` for English or `FR` for French
- `DISCORD_WEBHOOK_URL`: Your Discord channel webhook URL (or Slack incoming webhook URL)

### Step 4: Activate & Test
1. Click **"Test Step"** on the canvas to execute an immediate trial run.
2. Toggle the workflow to **Active** to run automatically every Friday at 17:00 (5:00 PM).

---

## 📋 Acceptance Criteria Checklist
- [x] **Exportable n8n workflow**: Complete importable JSON file included.
- [x] **Weekly Cron Trigger**: Set to `0 17 * * 5` (Friday 5:00 PM).
- [x] **GitHub API Ingestion**: Fetches commits, closed issues, and merged PRs for the trailing 7 days.
- [x] **Claude Model**: Configured with `claude-sonnet-4-20250514` for executive narrative generation.
- [x] **Multi-channel Delivery**: Discord / Slack webhook destination with embedded formatting.
- [x] **Configurable Variables**: Owner, repo, webhook, language (EN/FR) all exposed in one node.
- [x] **Setup in <= 5 steps**: Documented above in 4 concise steps.
- [x] **Sample Output**: Included in `examples/sample-summary-en.md` and `examples/sample-summary-fr.md`.
