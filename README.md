# 🔄 n8n + Claude API Weekly Dev Summary

An automated n8n workflow that generates a weekly narrative summary of a GitHub repository's activity using the Claude API.

## ✨ Features

- **Weekly Cron Trigger**: Runs automatically every Friday at 5 PM.
- **GitHub API Integration**: Fetches commits, closed issues, and merged PRs from the past 7 days.
- **Claude API Synthesis**: Uses `claude-sonnet-4-20250514` to generate a readable narrative summary.
- **Discord/Slack Delivery**: Posts the summary directly to your configured webhook.
- **Multi-Language Support**: Configure output in English (EN) or French (FR).

## 🚀 Setup Instructions (5 Steps)

1. **Import Workflow**: In your n8n instance, go to **Workflows > Import from File** and select `workflow.json`.
2. **Configure Environment Variables**: Add the following variables to your n8n environment or `.env` file:
   - `GITHUB_REPO`: The target repository (e.g., `owner/repo`)
   - `GITHUB_TOKEN`: Your GitHub Personal Access Token
   - `ANTHROPIC_API_KEY`: Your Claude API key
   - `DISCORD_WEBHOOK_URL`: Your Discord or Slack webhook URL
   - `LANGUAGE`: `EN` or `FR`
3. **Activate Workflow**: Toggle the "Active" switch in the top right corner of the workflow editor.
4. **Test Manually**: Click "Execute Workflow" to verify the API connections and webhook delivery.
5. **Monitor**: Check your Discord/Slack channel every Friday at 5 PM for the automated summary.

## 📦 Deliverables

- `workflow.json`: Exportable n8n workflow ready for import.
- `README.md`: Setup instructions and documentation.

## 💰 Bounty Claim

This PR fulfills all acceptance criteria for Issue #5 ($200 bounty).

/opire try
