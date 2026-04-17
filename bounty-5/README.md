# Bounty 5: Automated Weekly GitHub Dev Summary via n8n

This solution uses n8n to fetch GitHub activity (commits, closed issues, merged PRs) directly and passes the aggregated data to Claude 3.5 Sonnet to generate a narrative weekly summary. It then posts the exact 3-paragraph summary flawlessly to Discord/Slack via webhook.

## ⚙️ 5-Step Setup Guide

**Step 1:** Download the attached `n8n_workflow.json` file and import it into your n8n workspace (`+ New Workflow` > `...` > `Import from file`).
**Step 2:** Double-click the `Config` node (the second node).
**Step 3:** Replace `YOUR_GITHUB_TOKEN_HERE` with your GitHub Personal Access token (needs `repo` scope).
**Step 4:** Replace `YOUR_ANTHROPIC_API_KEY_HERE` with your Anthropic API Key (`sk-ant-api03...`).
**Step 5:** Replace `YOUR_DISCORD_WEBHOOK_URL_HERE` with your target Discord channel Webhook URL. Click **Execute Workflow** and watch the magic!
