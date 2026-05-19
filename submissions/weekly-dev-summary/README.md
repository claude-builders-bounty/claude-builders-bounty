# 📊 Weekly Dev Summary — n8n Workflow

Automated weekly GitHub activity summary powered by Claude API.

## ⚡ Quick Start (3 steps)

```bash
# 1. Import into n8n
#    n8n → Import → Select workflow.json

# 2. Set environment variables (in n8n or .env)
export GITHUB_TOKEN="ghp_..."
export ANTHROPIC_API_KEY="sk-ant-..."
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

# 3. Edit the "Set Date Range" node → change `repo` to your repo
```

## 🔄 How It Works

```
Cron (Fri 5pm)
  → Set Date Range (last 7 days)
  → Fetch Commits / Issues / PRs from GitHub API
  → Merge into single payload
  → Build Claude prompt with activity data
  → Claude API (sonnet-4) generates narrative summary
  → Format and deliver via Discord webhook
```

## 📋 Output Format

```markdown
## Weekly Dev Summary — 2026-05-12 → 2026-05-19

### Highlights
This week focused on dependency upgrades and CI improvements...

### By the Numbers
- Commits: 34
- Issues Closed: 5
- PRs Merged: 8

### Key Changes
- Upgraded all Linux binaries to Python 3.14
- Fixed YouTube PO token sanitization
- Renamed requirements files for cleaner dependency graph

### Community
Welcomed 2 new contributors...
```

## 🔧 Customization

| Node | What to change |
|------|---------------|
| `Set Date Range` | `repo` → your GitHub repo |
| `Deliver (Discord)` | URL → your Slack/Email/Discord webhook |
| `Weekly Cron` | Rule → preferred day/time |

For email delivery: replace Discord node with n8n Email node (SMTP).

## 📂 Files

| File | Description |
|------|-------------|
| `workflow.json` | Importable n8n workflow (10 nodes) |
