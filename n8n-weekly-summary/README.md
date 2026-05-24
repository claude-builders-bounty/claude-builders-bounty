# 📊 n8n + Claude 自动周报工作流

Automatically generates a weekly engineering summary report for any GitHub repository, powered by n8n and Anthropic Claude (claude-sonnet-4-20250514).

## ✨ Features

- **⏰ Scheduled Trigger** — Runs every Friday at 5:00 PM (Asia/Shanghai)
- **📡 GitHub API Integration** — Fetches commits, closed issues, and merged PRs from the past 7 days
- **🤖 AI-Powered Summaries** — Uses Claude Sonnet 4 to generate narrative, structured reports
- **📤 Multiple Outputs** — Slack webhook, console, file export, or email
- **📝 Structured Format** — Weekly highlights, key metrics, notable changes, contributor shoutouts, and upcoming plans

## 📋 Prerequisites

- [n8n](https://n8n.io/) v1.x or later (self-hosted or cloud)
- GitHub Personal Access Token (with `repo` scope)
- Anthropic API Key (for Claude)

## 🚀 Installation

### 1. Import the Workflow

1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Select `weekly_summary_workflow.json`
4. The workflow will appear with all nodes connected

![Import Workflow](https://docs.n8n.io/_images/workflows-import.gif)

### 2. Set Environment Variables

The workflow uses environment variables for credentials. Configure them in your n8n instance:

| Variable | Description | Required |
|---|---|---|
| `GITHUB_TOKEN` | GitHub Personal Access Token | ✅ Yes |
| `REPO_OWNER` | GitHub repository owner (e.g., `vercel`) | ✅ Yes |
| `REPO_NAME` | GitHub repository name (e.g., `next.js`) | ✅ Yes |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | ✅ Yes |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL | ❌ Optional |

#### How to set environment variables:

**Self-hosted (Docker):**
```bash
# In your docker-compose.yml or .env file
n8n env set GITHUB_TOKEN=ghp_xxxxxxxxxxxx
n8n env set ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx
n8n env set REPO_OWNER=your-org
n8n env set REPO_NAME=your-repo
n8n env set SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
```

**n8n Cloud (UI):**
1. Go to **Settings** → **Environment Variables**
2. Add each variable one by one

### 3. (Optional) Configure Slack Notifications

1. Create a Slack App with **Incoming Webhooks** enabled
2. Add a webhook to your desired Slack channel
3. Copy the webhook URL to `SLACK_WEBHOOK_URL` environment variable
4. The workflow will automatically detect the webhook and send reports to Slack

### 4. (Optional) Configure Email Output

If you prefer email delivery:
1. Add an **Email (SMTP)** credential in n8n
2. Unhide the "Email Option Placeholder" node
3. Connect it to the "Extract & Format Report" node
4. Configure the email recipient in the node settings

### 5. Activate the Workflow

1. Click **Active** toggle in the top-right corner
2. The workflow will run every Friday at 5:00 PM
3. You can also click **Execute Workflow** to test it immediately

## 🔧 How It Works

```
┌─────────────────────┐
│  Schedule Trigger    │  Every Friday 5:00 PM
│  (Cron: 0 17 * * 5) │
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│  Calculate Date      │  Computes the past 7 days
│  Range (Code Node)   │  (ISO format timestamps)
└─────────┬───────────┘
          │
    ┌─────┼─────┐
    ▼     ▼     ▼
┌────────┐┌────────┐┌────────┐
│Commits ││ Issues ││  PRs   │  Three parallel GitHub
│  API   ││  API   ││  API   │  API calls
└───┬────┘└───┬────┘└───┬────┘
    └─────┬───┘         │
          ▼              │
    ┌────────────┐       │
    │ Transform  │◄──────┘  Merge & normalize all
    │ GitHub Data│          data into a single payload
    └──────┬─────┘
           ▼
┌─────────────────────┐
│  Claude API          │  Send structured data to
│  (claude-sonnet-4)   │  Claude for report generation
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│  Extract & Format    │  Parse Claude response into
│  Report (Code Node)  │  clean Markdown report
└─────────┬───────────┘
          │
    ┌─────┴─────┐
    ▼           ▼
┌────────┐ ┌────────┐
│Console │ │ Slack  │  Dual output: console for
│(Debug) │ │(if URL)│  debugging, Slack for team
└────────┘ └────────┘
```

## 🧪 Testing the Workflow

1. Before activating, click **Execute Workflow** to run a manual test
2. Check the **Execution** tab for logs
3. Verify the output in the "Console Output (Debug)" node
4. If using Slack, confirm the message appears in your channel

## 📄 Sample Output

See [`sample_output.md`](./sample_output.md) for a full example of what the generated report looks like.

## 🔄 Customization

### Change the Repository

Update the `REPO_OWNER` and `REPO_NAME` environment variables, or modify the default values in the "Calculate Date Range" Code node.

### Change the Schedule

Edit the **Weekly Cron Trigger** node:
- Current: Every Friday at 17:00 (5:00 PM) Asia/Shanghai
- The cron expression `0 17 * * 5` means: minute 0, hour 17, day-of-month *, month *, day-of-week 5 (Friday)
- Change `hour` and `weekday` values as needed

### Customize the Report Format

Modify the prompt in the **Claude API** node's JSON body. You can:
- Change the language (e.g., switch to English, Japanese)
- Adjust the tone (formal, casual, technical)
- Add/remove report sections
- Include additional context (e.g., project milestones, release notes)

### Add More Data Sources

The workflow can easily be extended to fetch:
- GitHub Releases
- Code reviews / comments
- CI/CD status
- Deployment status
- Any REST API source

## 🔐 Security Notes

- **Never** commit your `.env` files or expose API keys
- Use n8n's built-in credential system for SMTP and sensitive values
- The GitHub token should have minimal required scopes (read-only for public repos)
- Consider rotating API keys periodically

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| Workflow won't import | Check your n8n version (needs v1.x+), try reimporting fresh |
| GitHub API returns 401 | Verify `GITHUB_TOKEN` env var is set and has correct permissions |
| Claude API returns 400 | Check `ANTHROPIC_API_KEY` env var; verify Claude model name is correct |
| No data in report | Check if the repo had any commits/PRs/issues in the past 7 days |
| Slack message not sent | Verify `SLACK_WEBHOOK_URL` is set and the webhook is active |
| Timezone issues | The workflow uses `Asia/Shanghai`; adjust in workflow settings if needed |

## 📦 File Structure

```
n8n-weekly-summary/
├── weekly_summary_workflow.json    # n8n workflow (importable)
├── README.md                       # This file
└── sample_output.md                # Example generated report
```

## 📝 License

MIT — Feel free to use, modify, and share.

---

**Made for [Bounty #5](https://github.com/your-bounty-link)** — OpenClaw Community
