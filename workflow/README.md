# 📊 n8n + Claude Code — Weekly Dev Summary Generator

Creates an automated n8n workflow that generates a weekly narrative summary of any GitHub repo's development activity, delivered to Discord.

## Features

- ⏰ **Cron-triggered** — runs every Friday at 5pm
- 🌐 **Fetches from GitHub API** — commits, closed issues, merged PRs
- 🤖 **Claude API-generated summary** — meaningful narrative, not raw data
- 📬 **Discord webhook delivery** — easy to read in your dev channel
- 🌍 **Multi-language** — supports EN and FR
- 🔧 **Fully configurable** — set via environment variables

## Quick Setup (5 Steps)

### 1. Prerequisites

- [n8n](https://docs.n8n.io/hosting/installation/) (self-hosted or cloud)
- [Claude API key](https://console.anthropic.com/)
- [GitHub personal access token](https://github.com/settings/tokens) (with `repo` scope)
- Discord webhook URL (create in your Discord channel settings)

### 2. Clone this repo

```bash
git clone https://github.com/haoyousun60-create/claude-builders-bounty.git
cd claude-builders-bounty
```

### 3. Set environment variables in n8n

In your n8n instance, set these as environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `REPO` | GitHub repo to watch | `owner/repo` |
| `GITHUB_TOKEN` | GitHub personal access token | `ghp_xxx` |
| `CLAUDE_API_KEY` | Anthropic Claude API key | `sk-ant-xxx` |
| `DESTINATION` | Delivery channel | `discord` |
| `WEBHOOK_URL` | Discord/Slack webhook URL | `https://discord.com/api/webhooks/...` |
| `LANGUAGE` | Output language | `EN` or `FR` |

### 4. Import the workflow

1. Open n8n dashboard
2. Go to **Workflows → Import from File**
3. Select `n8n-workflow-weeksummary.json`
4. Click **Save**

### 5. Activate

Click the **Active** toggle in the top-right corner.

The workflow will run automatically every Friday at 5pm. You can also trigger it manually to test.

## Output Example

```
📊 Weekly Dev Summary: claude-builders-bounty/claude-builders-bounty

Period: 2026-04-20 to 2026-04-27
Stats: 15 commits · 3 issues · 5 PRs

---

**Weekly Summary**
This week focused primarily on tooling and infrastructure improvements.
The team added three new bounty-related hooks, improved the CLAUDE.md
template for Next.js projects, and closed several documentation issues.

**Key Changes**
- Added pre-tool-use security hook (blocks destructive commands)
- Created CLAUDE.md template for Next.js + SQLite SaaS projects
- Fixed issue #3 — CHANGELOG generator now works with monorepos

**Notable Events**
- Bounty board now has 5 active bounties totaling $575
- New contributor: haoyousun60-create (2 PRs merged)

**Recommendations**
- Consider adding end-to-end tests for hooks
- Document the review process for bounty submissions
```

## Architecture

```
┌─────────────────┐
│  Cron Trigger   │  Every Friday @ 5pm
│  (Schedule)     │
└────────┬────────┘
         ▼
┌─────────────────┐
│  Build Config   │  Set target repo, calculate date range
│  & URLs         │
└────────┬────────┘
         │
    ┌────┼────┐
    ▼    ▼    ▼
┌──────┐┌──────┐┌──────┐
│Commits││Issues││ PRs  │  Fetch from GitHub API
└──┬───┘└──┬───┘└──┬───┘
    └──────┼────────┘
           ▼
┌─────────────────┐
│  Merge & Format │  Combine all data into prompt
└────────┬────────┘
         ▼
┌─────────────────┐
│  Claude API     │  Generate narrative summary
│  (claude-4)     │
└────────┬────────┘
         ▼
┌─────────────────┐
│  Format Output  │  Prepare Discord message
└────────┬────────┘
         ▼
┌─────────────────┐
│  Send to        │  Deliver to channel
│  Discord        │
└─────────────────┘
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| No data fetched | Check `GITHUB_TOKEN` has repo scope |
| Claude API error | Verify `CLAUDE_API_KEY` and credit balance |
| Discord not posting | Check `WEBHOOK_URL` is correct and active |
| Wrong timezone | Adjust cron expression in the trigger node |

## License

MIT
