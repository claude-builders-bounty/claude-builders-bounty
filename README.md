# Weekly GitHub Dev Summary — n8n Workflow

A complete n8n workflow that generates a weekly narrative summary of a GitHub repo's
activity, using the Claude API, and delivers it to Discord or Slack.

## 💰 Bounty: $200

Part of [claude-builders-bounty/claude-builders-bounty#5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5).

---

## ⚡ Setup (5 steps)

1. **Import** `weekly-dev-summary.json` into n8n
2. **Set credentials** in n8n (GitHub token + Anthropic API key)
3. **Set env vars:** `GITHUB_OWNER`, `GITHUB_REPO`, `ANTHROPIC_API_KEY`, `LANGUAGE` (EN/FR), `DISCORD_WEBHOOK` or `SLACK_WEBHOOK`
4. **Activate** the workflow
5. **Test** with manual execution — check the output

That's it. The workflow runs every Friday at 5pm.

## 🔧 Nodes

| Node | Purpose
|------|---------
| **Weekly Trigger** | Fires every Friday at 17:00 (cron: `0 17 * * 5`) |
| **Fetch Commits** | GitHub API: commits from the past 7 days |
| **Fetch Closed Issues** | GitHub API: issues closed in the past 7 days |
| **Fetch Merged PRs** | GitHub API: PRs merged in the past 7 days |
| **Merge Data** | Combines all fetched data into one text payload |
| **Generate Summary** | Calls Claude Sonnet to produce narrative summary |
| **Send to Discord/Slack** | Posts the summary via webhook |

## 📄 Output Format

```markdown
📋 Weekly Dev Summary

### Highlights
...

### Key Changes
...

### Next Week Focus
...
```

## 📁 Files

- `weekly-dev-summary.json` — Exportable n8n workflow (ready to import)
