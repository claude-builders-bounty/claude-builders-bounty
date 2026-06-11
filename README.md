# n8n Weekly GitHub Summary Workflow

An automated n8n workflow that generates a professional narrative summary of a GitHub repository's weekly activity using Claude AI.

## 🚀 Installation (5 steps)

1. **Import Workflow**: Import the `workflow.json` file into your n8n instance.
2. **Configure GitHub**: Add your GitHub API Token in the `Fetch Commits` and `Fetch PRs` nodes.
3. **Configure Claude**: Add your Anthropic API Key in the `Claude AI Summary` node.
4. **Set Destination**: Update the `Config` node with your target Slack/Discord webhook URL.
5. **Activate**: Turn on the workflow to enable the weekly Friday 5 PM trigger.

## 🛠 How it Works

1. **Trigger**: A weekly cron job triggers the process every Friday at 5 PM.
2. **Configuration**: The `Config` node manages variables like repository name and language.
3. **Data Collection**:
    - Fetches all commits from the last 7 days.
    - Fetches recently closed/merged Pull Requests.
4. **AI Analysis**: Claude AI analyzes the raw technical data and translates it into a narrative summary focusing on "technical wins" and "a-ha moments".
5. **Delivery**: The final summary is posted to your chosen messaging platform via webhook.

## 📊 Configuration Variables
| Variable | Description | Example |
|---|---|---|
| `repo` | GitHub owner/repo | `vercel/next.js` |
| `webhook_url` | Destination webhook | `https://hooks.slack.com/services/...` |
| `language` | Output language | `EN` or `FR` |
