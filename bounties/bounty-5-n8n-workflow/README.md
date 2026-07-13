# Weekly Dev Summary — n8n Workflow

Auto-generate a weekly development summary using **GitHub + Claude (Anthropic)** and deliver it to **Slack / Email / Discord**.

---

## Quick Start

### 1. Import into n8n

| Method | Steps |
|--------|-------|
| **UI** | Workflows → Add → Import from File → select `weekly-dev-summary.json` |
| **CLI** | Copy the file into `~/.n8n/workflows/` and restart n8n |
| **Docker** | Mount the file and import via the UI |

### 2. Create Required Credentials

Create these credentials in **n8n Settings → Credentials**:

| Credential Name | Type | Fields |
|----------------|------|--------|
| `GitHub API` | GitHub API (OAuth2 or PAT) | Personal Access Token with `repo` scope |
| `Anthropic API` | Header Auth | Header Name: `x-api-key`, Header Value: your Anthropic API key |
| `Slack` | Slack API | Slack Access Token (Bot token with `chat:write`) — only needed if using Slack |
| `SMTP` | SMTP | SMTP host, port, user, pass — only needed if using Email |

### 3. Set Environment Variables

Copy `.env.example` → `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your GitHub org/repo and pick an output channel.

### 4. Activate

Enable the workflow in the n8n UI. It runs **every Monday at 9:00 AM**.

To test immediately, click **Execute Workflow**.

---

## How It Works

```
Cron (Mon 9am)
  │
  ├─ Prepare Config (calculate date range for "last week")
  │
  ├─ GitHub: Commits ─┐
  ├─ GitHub: PRs ─────┤  (parallel fetch)
  ├─ GitHub: Issues ──┘
  │
  ├─ Merge (synchronize — wait for all 3)
  │
  ├─ Build Summary (merge + format Claude prompt)
  │
  ├─ Claude API (Anthropic — natural language summary)
  │
  └─ Route ─┬─ Slack
             ├─ Email
             └─ Discord
```

**Error handling**: If any API fails the Error Trigger node catches it and sends a notification to Slack via the error webhook.

---

## Customization

### Change Frequency

Edit the **Weekly Cron Trigger** node:

| Schedule | Cron Expression |
|----------|----------------|
| Monday 9am (default) | `0 9 * * 1` |
| Daily 8am | `0 8 * * *` |
| Friday 5pm | `0 17 * * 5` |
| Every hour | `0 * * * *` |

### Change Repositories

Add more **GitHub HTTP Request** nodes for additional repos, then merge them into the prompt builder.

### Add Team Members

In the **Build Summary** Code node, add a `teamMembers` array with GitHub usernames to track individual contributions.

### Customize the Prompt

Edit the **Build Summary** Code node — look for the `prompt` template. You can adjust tone, format, or level of detail.

---

## Output Preview

The Claude-generated summary includes:

- **Highlights** — major merged PRs and completed milestones
- **Commits** — quantitative + qualitative (by contributor, area of codebase)
- **PR Activity** — opened, merged, and still-open PRs
- **Issues** — new bugs, feature requests, and resolved tickets
- **Trends** — code review velocity, response time, areas of churn
- **Action Items** — stale PRs, unreviewed issues, blockers

---

## Dependencies

- n8n ≥ 1.0 (self-hosted or n8n.cloud)
- GitHub Personal Access Token (`repo` scope)
- Anthropic API key
- Slack webhook / SMTP credentials / Discord webhook (per chosen channel)

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Workflow doesn't trigger | Check the workflow is **Active** (toggle in top-right) |
| GitHub 403 / rate limit | Ensure PAT has `repo` scope; check GitHub rate limits |
| Claude API returns 401 | Verify the `Anthropic API` Header Auth credential is correct |
| "No items" in Merge node | Check the cron expression; run workflow manually to test |
| Channel not sending | Verify `OUTPUT_CHANNEL` env var matches one of `slack`, `email`, `discord` |
