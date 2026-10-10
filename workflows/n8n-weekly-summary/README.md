# Automated Weekly Dev Summary Workflow (n8n + Claude API)

> Production-ready [n8n](https://n8n.io) workflow that periodically aggregates weekly GitHub activity (commits, merged PRs, closed issues), generates an executive narrative summary via the **Anthropic Claude API**, and dispatches the digest to Discord or Slack.

Fixes #5 ($200 Bounty)

---

## ⚡ Quickstart Setup in 4 Steps

### Step 1: Import the Workflow into n8n
1. Open your n8n dashboard.
2. Click **Add workflow** > **Import from File...**
3. Select [`weekly-dev-summary.json`](./weekly-dev-summary.json).

### Step 2: Set Anthropic API Credential
Set your `ANTHROPIC_API_KEY` in n8n environment variables or credential manager:
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

### Step 3: Configure Target Repository & Destination
In the **Workflow Configuration** node, customize the values:
- `GITHUB_REPO`: Target repository in `owner/repo` format (e.g. `facebook/react` or `claude-builders-bounty/claude-builders-bounty`).
- `LANGUAGE`: `EN` (English) or `FR` (French).
- `DESTINATION_TYPE`: `discord` or `slack`.
- `WEBHOOK_URL`: Your Discord or Slack incoming webhook URL.

### Step 4: Activate & Test
1. Click **Test step** or **Execute workflow** to verify immediate execution.
2. Toggle the workflow to **Active** to run automatically every **Friday at 5:00 PM** (`0 17 * * 5`).

---

## 🛠️ Architecture & Data Flow

```text
[Weekly Cron: Fri 5pm]
         │
         ▼
[Workflow Configuration] (Repo, Language: EN/FR, Webhook URL)
         │
         ▼
[Calculate Date Range] (Lookback 7 days ISO timestamps)
   ┌─────┴───────────────────────┐
   ▼                             ▼                             ▼
[GitHub Commits]          [Merged PRs]                  [Closed Issues]
   └─────┬───────────────────────┘
         ▼
[Aggregate & Build Prompt] (Formats Markdown digest + multilingual prompt)
         │
         ▼
[Claude API (Claude 3.5 Sonnet)] (Generates executive narrative summary)
         │
         ▼
[Format Webhook Payload] (Discord Rich Embeds or Slack Block Kit)
         │
         ▼
[Dispatch to Webhook Channel]
```

---

## 📋 Configurable Variables

| Variable | Description | Allowed Values | Default |
| :--- | :--- | :--- | :--- |
| `GITHUB_REPO` | Target GitHub repository | `owner/repo` | `claude-builders-bounty/claude-builders-bounty` |
| `LANGUAGE` | Output language of narrative | `EN`, `FR` | `EN` |
| `DESTINATION_TYPE`| Webhook platform | `discord`, `slack` | `discord` |
| `WEBHOOK_URL` | Incoming webhook target | `https://...` | User Webhook URL |
| `LOOKBACK_DAYS` | Days of activity to aggregate | Number (1–30) | `7` |

---

## 📄 Sample Generated Narrative Summary (Discord Output)

```markdown
🚀 Executive Headline:
Sprint 42 delivered massive performance gains and finalized the v2 architecture migration.

🌟 Key Highlights & Major Accomplishments:
- Completed the core database refactoring, reducing latency by 45%.
- Closed 14 community issues and merged 8 pull requests.

🛠️ Pull Requests Delivered:
- PR #104: Add multi-region read replicas
- PR #102: Migrate auth session handler to Redis

🐛 Bugs Resolved:
- Issue #89: Fix race condition in concurrent webhook handler
- Issue #84: Prevent memory leak in long-lived SSE connections

🔮 Looking Ahead:
Next week focuses on public beta launch and billing integrations.
```
