# 📰 Weekly Dev Summary — n8n + Claude Workflow

Automatically generates a narrative weekly development summary from your GitHub repo activity and delivers it to Slack (or Discord/email) every Friday at 5pm — powered by Claude Sonnet.

## What it does

Every Friday at 5:00 PM the workflow:

1. **Fetches** from GitHub: commits, closed issues, and merged PRs from the past 7 days
2. **Builds** a structured context object with stats and highlights
3. **Calls** `claude-sonnet-4-20250514` to write a warm, human-readable narrative summary
4. **Delivers** the summary to your Slack channel (swap one node for Discord/email — see below)

## Setup (5 steps)

**Step 1 — Import the workflow**

In n8n, go to **Workflows → Import from file** and select `workflow.json`.

**Step 2 — Add credentials**

In n8n Settings → Credentials, create two HTTP Header Auth credentials:

| Credential name | Header name | Header value |
|---|---|---|
| `GitHub Token` | `Authorization` | `Bearer ghp_YOUR_TOKEN` |
| `Anthropic API Key` | `x-api-key` | `sk-ant-YOUR_KEY` |

**Step 3 — Set environment variables**

In n8n Settings → Variables (or set via `.env` if self-hosted):

| Variable | Example | Description |
|---|---|---|
| `GITHUB_REPO_OWNER` | `vercel` | GitHub org or username |
| `GITHUB_REPO_NAME` | `next.js` | Repository name |
| `SLACK_WEBHOOK_URL` | `https://hooks.slack.com/...` | Incoming Webhook URL from Slack App |
| `SUMMARY_LANGUAGE` | `EN` or `FR` | Language for the generated summary |

**Step 4 — Test manually**

Click **Execute workflow** to run it immediately and verify the Slack message arrives.

**Step 5 — Activate**

Toggle the workflow to **Active** — it will now run automatically every Friday at 5pm.

## Sample Output

```
Weekly Dev Digest — myorg/myapp (2026-04-25)

Highlights
This was a productive shipping week. The team merged 8 pull requests, closed 12 issues,
and landed 47 commits — including two major feature releases and several performance wins.

✨ What shipped
• #284: Add dark-mode support across all dashboard pages (@alice)
• #281: Implement CSV export for analytics reports (@bob)
• #279: Fix payment form double-submit race condition (@carol)
• Closed 4 bugs reported from last week's release

⚙️ Under the hood
Commit patterns show heavy activity in the api/ and components/ui/ directories.
Several chore commits bumped dependencies and cleaned up deprecated imports.

📊 By the numbers
• Commits: 47  •  Issues closed: 12  •  PRs merged: 8

👀 Looking ahead
Keep the momentum going — the auth refactor is nearly ready for review!
```

## Swapping to Discord or Email

**Discord**: Replace the `Send to Slack` node with an HTTP Request node pointing to your Discord webhook URL. Use the same JSON body but change `text` → `content`.

**Email**: Replace the `Send to Slack` node with an `n8n-nodes-base.emailSend` node. Set `To`, `Subject`, and `Text` = `{{ $json.summaryText }}`.

## Requirements

- n8n ≥ 1.0 (cloud or self-hosted)
- GitHub personal access token (read access to target repo)
- Anthropic API key with access to `claude-sonnet-4-20250514`
- Slack Incoming Webhook URL (free)
