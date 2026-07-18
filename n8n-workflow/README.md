# Weekly Dev Summary — n8n Workflow

Generates a narrative weekly summary of GitHub repo activity using Claude API and delivers it via Discord/Slack.

## Setup (5 steps)

1. **Import** — In n8n, go to **Workflows → Import from File** and select `weekly-dev-summary.json`

2. **Set GitHub token** — Create a credential "Header Auth" with key `Authorization` and value `Bearer YOUR_GITHUB_TOKEN`

3. **Set Anthropic token** — Create a credential "Header Auth" with key `x-api-key` and value `YOUR_ANTHROPIC_API_KEY`

4. **Set webhook URL** — Create env vars or set in the **Send to Discord/Slack** node:
   - `WEBHOOK_URL` — your Discord/Slack webhook URL

5. **Activate** — Toggle the workflow on. Runs every Friday at 5pm.

## Configuration

Edit the **Merge & Aggregate** node to set:

| Variable | Where | Default |
|----------|-------|---------|
| `repo` | Code node | `owner/repo` |
| `language` | Claude API prompt | `English` (or `FR`, `PT-BR`, etc.) |
| `WEBHOOK_URL` | Env or node URL | Discord/Slack webhook |

## Output Example

```
📅 Weekly Dev Summary — owner/repo
Week ending: 2026-07-18

🚀 Merged PRs (5)
• #42 Add dark mode — landed after 3 revisions
• #43 Fix login redirect loop — closes issue #38

🐛 Closed Issues (3)
• #38 Login redirect loop on expired session
• #40 Memory leak in dashboard

📊 Summary
This week was all about polish. The dark mode implementation went through
three rounds of review but landed cleanly. The login redirect bug was the
highlight fix — it had been causing 404 errors for users with expired
sessions since the last deploy.
```

## Requirements

- n8n (self-hosted or cloud)
- GitHub token (public repo access)
- Anthropic API key
- Discord or Slack incoming webhook
