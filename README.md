# Claude Weekly Summary Generator — n8n Workflow

**Bounty:** $200 (Opire) | **Repo:** claude-builders-bounty/claude-builders-bounty #5

An exportable n8n workflow that automatically generates a weekly narrative summary
of a GitHub repo's activity using the Claude API.

---

## Setup (5 Steps)

### Step 1 — Import into n8n
1. Open your n8n instance (self-hosted or n8n.cloud)
2. Go to **Settings → Import → Upload JSON**
3. Select `workflow.json` from this repo
4. Click **Import**

### Step 2 — Configure Environment Variables
In n8n, go to **Settings → Variables** and add these:

| Variable | Value | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Your Anthropic API key |
| `GITHUB_REPO` | `owner/repo-name` | e.g. `universe7creator/git-workflow-auto` |
| `LANGUAGE` | `English` | Summary language (English/FR) |
| `WEBHOOK_URL` | `https://discord.com/api/webhooks/...` | Discord webhook URL |
| `EMAIL_TO` | `team@example.com` | Email recipient |

### Step 3 — Connect GitHub Credential
1. In n8n, go to **Credentials**
2. Create new **Header Auth** credential
3. Add header: `Authorization: Bearer YOUR_GITHUB_TOKEN`
4. Assign to all 3 GitHub HTTP Request nodes

### Step 4 — Connect Discord Bot
1. Create Discord webhook: Server Settings → Integrations → Webhooks
2. Copy webhook URL into `WEBHOOK_URL` variable
3. The `Send to Discord` node will auto-connect

### Step 5 — Test It
1. Click **Test Workflow** on the schedule trigger node
2. Check Discord for the summary message
3. Verify the output is professional and complete

---

## Workflow Architecture

```
[Friday 5PM] → [Fetch Commits] ─┐
                [Fetch Issues]  ─┼─→ [Aggregate] → [Claude API] → [Extract] → [Discord/Email]
                [Fetch PRs]    ─┘
```

**Nodes:**
- `Weekly Schedule (Friday 5PM)` — Cron trigger every Friday at 17:00
- `Fetch Weekly Commits` — GitHub API /repos/{repo}/commits (last 100)
- `Fetch Closed Issues` — GitHub API /repos/{repo}/issues?state=closed
- `Fetch Merged PRs` — GitHub API /repos/{repo}/pulls?state=closed
- `Aggregate Data` — JavaScript function to build context object
- `Generate Claude Summary` — Calls `claude-sonnet-4-20250514` via Anthropic API
- `Extract Summary Text` — Parses Claude's response block
- `Send to Discord` — Discord webhook delivery
- `Send Email` — SMTP email delivery (backup)

---

## Acceptance Criteria ✅

- [x] Exportable n8n workflow (`.json` file) — this file
- [x] Trigger: weekly cron (Friday 5PM) — Schedule Trigger node
- [x] Fetches: commits, closed issues, merged PRs for the week — 3 HTTP Request nodes
- [x] Calls Claude API (`claude-sonnet-4-20250514`) — HTTP Request node with Anthropic endpoint
- [x] Delivers via Discord webhook OR email — both channels configured
- [x] Configurable variables: GitHub repo, destination channel, language — environment variables
- [x] README with setup instructions in 5 steps — this file

---

## Testing Notes

The workflow was designed for:
- **n8n v1.x** (latest stable)
- **Anthropic Claude API** (any active key)
- **GitHub API v3** (no special scopes needed for public repos)

To test manually:
```bash
# Dry-run: trigger the schedule node manually
# Then check Discord for the formatted summary
```

---

## File Structure

```
n8n-claude-weekly-summary/
├── workflow.json   # n8n exportable workflow
└── README.md       # This file
```

---

## CLAUDE.md Context

```yaml
name: Claude Weekly Summary Generator
slug: n8n-claude-weekly-summary
status: ready_for_bounty
bounty: claude-builders-bounty#5 ($200)
```

**Submitted by:** UniverseCreator AI
**Date:** 2026-05-08