# GitHub Weekly Summary — n8n Workflow

## What It Does
Every Friday at 5pm, this n8n workflow:
1. Fetches commits, closed issues, and merged PRs from any GitHub repo
2. Sends them to Claude API (`claude-sonnet-4-20250514`)
3. Generates a narrative weekly summary
4. Emails the summary to you

## Setup (5 steps)

### 1. Import the workflow
- In n8n, go to **Workflows → Import from File**
- Select `github-weekly-summary.workflow.json`

### 2. Configure credentials
Create these n8n credentials:
- **GitHub**: Personal Access Token with `repo` scope
- **Claude**: Anthropic API key
- **Email**: SMTP credentials for sending

### 3. Set config variables
In the **Config** node, set:
- `repo`: your GitHub repo (e.g. `owner/repo`)
- `toEmail`: where to send the summary
- `language`: `EN` or `FR`

### 4. Activate the workflow
Toggle the workflow to **Active** in n8n.

### 5. Run once to test
Click **Execute Workflow** to test before the weekly cron fires.

## Files
- `github-weekly-summary.workflow.json` — n8n importable workflow
- Screenshot: (attach successful execution screenshot here)
