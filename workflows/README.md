# Weekly GitHub Summary with Claude — n8n Workflow

Automatically generates a narrative weekly summary of a GitHub repository's activity (commits, closed issues, merged PRs) using the Claude API, and delivers it via Discord webhook.

## Features

- **Trigger**: Weekly cron (Friday at 5pm)
- **Fetches**: Commits, closed issues, merged PRs via GitHub REST API
- **Generates**: Narrative summary via `claude-sonnet-4-20250514`
- **Delivers**: Summary to Discord webhook (configurable)
- **Configurable**: GitHub repo, Discord webhook URL, language (EN/FR)

---

## Setup (5 Steps)

### Step 1 — Import the workflow
1. Open your n8n instance
2. Click **"Import from File"** → select `workflows/n8n-weekly-github-summary.json`

### Step 2 — Configure environment variables
In n8n **Settings → Variables**, add these environment variables:

| Variable | Value | Description |
|---|---|---|
| `GITHUB_REPO` | `owner/repo` | Target GitHub repository (e.g. `diygod/RSSHub`) |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Your Anthropic API key |
| `DELIVERY_WEBHOOK_URL` | Discord webhook URL | Where to send the summary |
| `LANGUAGE` | `EN` or `FR` | Summary language (default: EN) |

### Step 3 — Add GitHub credentials (optional)
If you need higher rate limits, create a GitHub Personal Access Token:
1. GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
2. Grant `repo:status`, `public_repo` scopes
3. Add it as a header in each GitHub HTTP Request node: `Authorization: Bearer YOUR_TOKEN`

### Step 4 — Set the schedule
The workflow triggers every **Friday at 5:00 PM UTC**. To change, edit the Schedule Trigger node.

### Step 5 — Activate and test
1. Click **"Activate"** in n8n
2. Click **"Test workflow"** to run it immediately
3. Check your Discord channel for the summary

---

## Sample Output

```
📊 Weekly Summary for DIYgod/RSSHub (2026-05-07 → 2026-05-13)

This week was productive! The repository saw 23 commits, 5 closed issues, and 3 merged pull requests.

Highlights:
• 23 commits pushed, including major refactors to the router system
• #1234 — Fixed YouTube RSS extraction (closed by @diygod)
• #1235 — Added Bilibili live support (closed by @mo-jinran)  
• #212 — Merge pull request for Reddit RSS fix (merged by @diygod, +342 -89)

The team continues to ship quality updates every week. Great work! 🚀
```

---

## Customization

- **Change delivery**: Replace the "Send to Discord" node with an Email node (SMTP) or Slack webhook
- **Multi-repo**: Duplicate the workflow and change `GITHUB_REPO` for each repo
- **Daily summaries**: Change the Schedule Trigger to run daily instead

---

## License

MIT
