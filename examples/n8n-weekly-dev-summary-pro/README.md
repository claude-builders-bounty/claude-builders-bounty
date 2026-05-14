# 📅 n8n Weekly Dev Summary — Multi-Repo + Claude AI

> **Bounty #5** · Automated weekly developer summary using n8n + `claude-sonnet-4-20250514`

An importable n8n workflow that fires every Monday at 9 AM, collects the past 7 days of GitHub activity across **multiple repositories**, generates a rich narrative summary with Claude, and delivers it to **Slack**, **Discord**, and/or as a **GitHub Issue**.

---

## ✨ What Makes This Different

| Feature | Basic submissions | This workflow |
|---|---|---|
| Multi-repo support | ❌ | ✅ Comma-separated list |
| Team member breakdown | ❌ | ✅ Per-contributor stats |
| Metrics section | ❌ | ✅ Commits, PRs, issues, lines ±, contributors |
| Delivery options | 1 | ✅ Slack + Discord + GitHub Issue |
| Smart routing | ❌ | ✅ Auto-routes based on which webhooks are set |
| Language support | EN only | ✅ EN / FR / any via `SUMMARY_LANGUAGE` |
| Schedule | Fri 5pm | ✅ Mon 9am (configurable) |

---

## 🚀 Setup (5 Steps)

### 1. Import the workflow

In n8n: **Workflows → Import from file** → select `workflow.json`

### 2. Set environment variables

In n8n: **Settings → Variables** (or your `.env` / deployment config):

```env
# Required
GITHUB_REPOS=owner/repo1,owner/repo2    # comma-separated multi-repo list
ANTHROPIC_API_KEY=sk-ant-...

# Delivery — set at least one:
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Optional
SUMMARY_LANGUAGE=EN          # EN or FR (default: EN)
```

### 3. Add credentials in n8n

- **GitHub credential** (Personal Access Token, scopes: `repo`, `read:org`)  
  → used by "Get Commits", "Get Merged PRs", "Get Closed Issues", "Post as GitHub Issue" nodes
- **Anthropic API Key** as an HTTP Header Auth credential named `Anthropic API Key`  
  → Header name: `x-api-key`, value: your Anthropic key

### 4. Activate the workflow

Toggle **Active** in the top-right of the workflow editor.  
The schedule trigger fires every **Monday at 09:00 UTC**.

### 5. Test manually

Click **Execute Workflow** to run a one-off execution and review the output in each node's output panel.

---

## 🔁 Workflow Architecture

```
Every Monday 9am
        │
        ▼
Build Date Windows          ← computes since/until, expands GITHUB_REPOS list
   │    │    │
   ▼    ▼    ▼
Get     Get     Get          ← GitHub REST API (parallel fetch)
Commits PRs     Issues
   │    │    │
   └────┴────┘
        │
        ▼
Aggregate & Build Metrics    ← team breakdown, line counts, contributor stats
        │
        ▼
Generate Summary (Claude)    ← claude-sonnet-4-20250514, structured 5-section prompt
        │
        ▼
Format Summary
        │
        ▼
Route Delivery (IF node)
  ┌─────┴─────┐
  ▼           ▼
Slack      Discord
  └─────┬─────┘
        ▼
Post as GitHub Issue         ← always posts; labelled "weekly-summary"
```

---

## 📋 Sample Output

```markdown
# 📅 Weekly Dev Summary: `anthropics/anthropic-sdk-python`
**Period:** 2026-05-07 → 2026-05-14

## 📊 Weekly Metrics
- 🔨 **47 commits** across 8 contributors
- 🔀 **12 PRs merged** (+2,341 / -890 lines)
- ✅ **9 issues closed**
- 👥 **8 active contributors**

## 👥 Team Highlights
| Contributor | Commits | PRs | Issues |
|---|---|---|---|
| @alice | 14 | 4 | 2 |
| @bob | 11 | 3 | 1 |
| @carol | 9 | 2 | 3 |

🌟 **@alice** led the week with 14 commits and 4 merged PRs, driving the new
streaming response refactor to completion.

## 🚀 Key Deliverables
- **#421** — `Add streaming response support` (@alice) — long-awaited feature
- **#418** — `Fix token counting for vision inputs` (@bob) — bug fix
- **#415** — `Upgrade httpx to 0.27.x` (@carol) — dependency update

## 📝 Narrative
This was a milestone week for `anthropic-sdk-python`. The streaming refactor
that @alice has been championing for three sprints finally landed, unlocking
real-time token-by-token delivery for all SDK consumers. Bob's fix for vision
token counting closes a subtle but customer-facing billing discrepancy.

On the infrastructure side, Carol's httpx upgrade completes the security patch
backlog. The team shipped 47 commits with strong test coverage — CI green across
all 9 supported Python versions.

## 🔮 What's Next
- Vision tool-use integration (#430) is in review
- Python 3.13 compatibility testing (#435) opens
- Streaming retry logic edge cases flagged in #428
```

---

## ⚙️ Customising the Schedule

The trigger uses a cron expression. Change `0 9 * * 1` in the **Every Monday 9am** node to any schedule:

| Schedule | Cron |
|---|---|
| Friday 5pm | `0 17 * * 5` |
| Daily 8am | `0 8 * * *` |
| Monday 9am (default) | `0 9 * * 1` |

---

## 🔧 Environment Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `GITHUB_REPOS` | ✅ | — | `owner/repo` or comma-separated list |
| `ANTHROPIC_API_KEY` | ✅ | — | Anthropic API key |
| `SLACK_WEBHOOK_URL` | one of | — | Slack incoming webhook URL |
| `DISCORD_WEBHOOK_URL` | one of | — | Discord webhook URL |
| `SUMMARY_LANGUAGE` | ❌ | `EN` | Language for the Claude summary (`EN`/`FR`) |
