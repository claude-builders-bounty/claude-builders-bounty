# Weekly GitHub Dev Summary — n8n Workflow

Generate a narrative weekly summary of your GitHub repository's activity using AI.

## 5-Step Setup

1. **Install n8n**: `npx n8n` or `docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n`

2. **Import workflow**: n8n UI → Workflows → Import from File → `weekly_dev_summary.json`

3. **GitHub Token**: Create a PAT at github.com/settings/tokens → Header Auth credential with `Authorization: Bearer YOUR_TOKEN` → apply to 3 GitHub HTTP nodes

4. **AI API Key**: Header Auth credential with `Authorization: Bearer YOUR_API_KEY` → apply to "Generate AI Summary" node (default uses DeepSeek API)

5. **Set repo and run**: Set owner/repo in GitHub nodes or pass dynamically from a prior node

## Workflow Nodes

| Step | Node | What it does |
|------|------|-------------|
| 1 | Schedule Trigger | Runs every Friday at 5pm |
| 2-4 | HTTP Request (GitHub API) | Fetches commits, closed issues, merged PRs (past 7 days) |
| 5 | Code (Python) | Aggregates and structures data |
| 6 | HTTP Request (AI API) | Calls DeepSeek to generate narrative summary |
| 7 | Code (Python) | Formats final markdown report |
| 8 | Webhook Output | Outputs result (swap for Email/Slack/Discord) |

## Requirements
- n8n v1.0+
- GitHub PAT (free)
- AI API key (~$0.01-0.05/summary)
