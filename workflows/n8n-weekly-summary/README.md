# n8n + Claude Weekly Dev Summary

An n8n workflow that generates a weekly narrative summary of GitHub activity using Claude API.

## Features

- **Weekly cron:** Every Friday at 5 PM
- **Fetches:** Commits, closed issues, merged PRs (past 7 days)
- **Claude API:** Generates narrative summary
- **Delivery:** Discord webhook (configurable)
- **Language:** English or French

## Setup (5 Steps)

### 1. Import Workflow
In n8n: **Workflows → Add → Import from JSON** → select `n8n-weekly-summary.json`

### 2. GitHub Credentials
Create a **Header Auth** credential in n8n:
- Name: `GitHub API`
- Header: `Authorization` → Value: `Bearer <your-github-token>`

### 3. Anthropic Credentials
Create a **Header Auth** credential in n8n:
- Name: `Anthropic API`
- Header: `x-api-key` → Value: `<your-anthropic-key>`
- Add second header: `anthropic-version` = `2023-06-01`

### 4. Configure Variables
Edit the **Configuration** (Code) node:
```javascript
repoUrl: 'https://api.github.com/repos/owner/repo'
language: 'EN'        // or 'FR'
webhookUrl: 'your-discord-webhook-url'
```

### 5. Activate
Toggle workflow to **Active**.

## Testing
Click **Execute Workflow** to test immediately. Check Discord for output.
