# Weekly Dev Summary — n8n Workflow 🤖

> Automated weekly GitHub development summaries using Claude API.
> Runs every Friday at 5pm, fetches the week's activity, and generates an AI-powered narrative summary.

---

## What This Workflow Does

1. **⏰ Triggers automatically** every Friday at 5pm (UTC)
2. **📡 Fetches GitHub data** — commits, closed issues, and merged PRs from the past week
3. **🧠 Generates a summary** using Claude API (claude-sonnet-4-20250514)
4. **📋 Produces a structured report** with:
   - 🏆 Highlight of the week
   - 🔑 Key changes
   - 🌟 Contributor shoutouts
   - 📋 Upcoming priorities
   - 📊 Weekly stats

---

## How to Import

### Prerequisites

- **n8n** installed (self-hosted or n8n.cloud)
- A **GitHub Personal Access Token** with `repo` scope
- An **Anthropic Claude API key**

### Step 1: Import the Workflow

1. Open your n8n instance
2. Click **"Import from File"** (or go to Workflows → Add Workflow → Import)
3. Select the `weekly-dev-summary.json` file
4. The workflow will appear with all 10 nodes connected

### Step 2: Configure the Workflow

Open the **"Calculate Week Range"** node (2nd node from top) and edit these values:

```javascript
const config = {
  owner: 'YOUR_GITHUB_ORG',       // ← change this
  repo: 'YOUR_REPO_NAME',         // ← change this
  githubToken: process.env.GITHUB_TOKEN || 'ghp_xxxxxxxxxxxx',
  claudeApiKey: process.env.CLAUDE_API_KEY || 'sk-ant-xxxxxxxxxxxx',
  githubApiBase: 'https://api.github.com'
};
```

> 💡 **Recommended**: Use environment variables (`GITHUB_TOKEN`, `CLAUDE_API_KEY`) instead of hardcoding tokens. You can also set them as n8n Credentials or edit the HTTP Request nodes directly.

### Step 3: Update Repository URLs (Optional)

The HTTP Request nodes point to `claude-builders-bounty/claude-builders-bounty` by default. Either:

- Edit the config in "Calculate Week Range" (recommended — the URLs use `$()` references), or
- Manually update the URL fields in all 3 HTTP Request nodes

### Step 4: Test the Workflow

1. Click **"Execute Workflow"** to run it manually
2. Check each node's output to verify:
   - Commits are being fetched
   - Issues are being fetched
   - PRs are being fetched
   - Claude summary is generated
3. Review the final output in the **"Format Final Output"** node

### Step 5: Activate the Schedule

1. Toggle the **"Active"** switch (top-right corner)
2. The workflow will now run automatically every Friday at 5pm UTC

---

## Workflow Architecture

```
┌─────────────────────┐
│  Cron Trigger       │  Friday 5pm (0 17 * * 5)
│  (Schedule)         │
└────────┬────────────┘
         │
┌────────▼────────────┐
│  Calculate Week     │  Computes Mon–Fri date range + stores config
│  Range (Code)       │
└────────┬────────────┘
         │
┌────────▼────────────┐
│  Fetch Commits      │  GET /repos/{owner}/{repo}/commits?since=&until=
│  (HTTP Request)     │
└────────┬────────────┘
         │
┌────────▼────────────┐
│  Process Commits    │  Formats commit data (sha, message, author, date)
│  (Code)             │
└────────┬────────────┘
         │
┌────────▼────────────┐
│  Fetch Closed Issues│  GET /repos/{owner}/{repo}/issues?state=closed
│  (HTTP Request)     │
└────────┬────────────┘
         │
┌────────▼────────────┐
│  Process Issues     │  Filters out PRs, formats issue data
│  (Code)             │
└────────┬────────────┘
         │
┌────────▼────────────┐
│  Fetch Merged PRs   │  GET /repos/{owner}/{repo}/pulls?state=closed
│  (HTTP Request)     │
└────────┬────────────┘
         │
┌────────▼────────────┐
│  Aggregate All Data │  Combines all data, builds Claude prompt
│  (Code)             │
└────────┬────────────┘
         │
┌────────▼────────────┐
│  Generate Summary   │  POST https://api.anthropic.com/v1/messages
│  (HTTP Request)     │  Model: claude-sonnet-4-20250514
└────────┬────────────┘
         │
┌────────▼────────────┐
│  Format Final Output│  Parses Claude response into structured JSON
│  (Code)             │
└─────────────────────┘
```

---

## Output Format

The final node outputs a JSON object:

```json
{
  "repo": "owner/repo",
  "weekLabel": "2025-05-12 to 2025-05-16",
  "generatedAt": "2025-05-16T17:00:00.000Z",
  "stats": {
    "commitsCount": 42,
    "issuesCount": 7,
    "prsCount": 5,
    "contributorsCount": 8
  },
  "summary": "# Weekly Dev Summary\n\n🏆 Highlight of the Week\n...",
  "usage": {
    "input_tokens": 1500,
    "output_tokens": 600
  },
  "model": "claude-sonnet-4-20250514"
}
```

---

## Customization

### Change the schedule
Edit the **"Weekly Friday 5pm Trigger"** node's cron expression:
- `0 17 * * 5` = Friday 5pm UTC
- `0 9 * * 1` = Monday 9am UTC
- Use [crontab.guru](https://crontab.guru) to build expressions

### Change the date range
Edit the **"Calculate Week Range"** node. By default it captures Monday 00:00 to current time. To capture the full week (Mon–Sun), modify the `until` calculation.

### Add notifications
Connect the final output to an **Email**, **Slack**, **Discord**, or **Telegram** node to automatically send the summary after generation.

### Use a different Claude model
Edit the `model` field in the **"Aggregate All Data"** node. Supported models:
- `claude-sonnet-4-20250514` (default)
- `claude-3-opus-20240229`
- `claude-3-5-sonnet-20241022`

---

## Troubleshooting

| Problem | Solution |
|----------|----------|
| "Bad credentials" on GitHub API | Verify your PAT has `repo` scope and hasn't expired |
| "401 Unauthorized" on Claude API | Check your API key starts with `sk-ant-` and has credits |
| Empty commits/issues/PRs | Verify the date range — ensure there was activity that week |
| Workflow doesn't trigger | Toggle Active switch ON; check n8n's timezone setting |
| "Node not found" errors | Make sure node names match exactly (they use `$('Node Name')` references) |

---

## Requirements

- **n8n** v1.0.0+ (uses Code node typeVersion 2)
- **GitHub** Personal Access Token with `repo` scope
- **Anthropic** API key with Claude access

---

*Part of [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) • Bounty #5 • $200*
