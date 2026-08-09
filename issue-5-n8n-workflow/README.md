# Weekly GitHub Dev Summary — n8n + Claude

Author: RawNuke

Copyright (c) 2026 RawNuke. All rights reserved.

An n8n workflow that generates a weekly narrative summary of GitHub repository
activity. It fetches commits, closed issues, and merged pull requests.
It calls the Claude API for the narrative summary. It delivers the summary
via Discord webhook or email.

## Setup (5 steps)

### 1. Import the workflow

Open n8n. Select **Import from File**. Choose the file
`n8n-workflow-weekly-dev-summary.json`.

### 2. Set environment variables

Add these environment variables to your n8n instance:

- `GITHUB_TOKEN` — a GitHub personal access token with repo read access
- `CLAUDE_API_KEY` — your Claude API key from the Anthropic Console
- `DISCORD_WEBHOOK_URL` — your Discord webhook URL (if you use Discord)
- `SMTP_FROM` — the sender email address (if you use email)

### 3. Configure workflow variables

Open the **Set Variables** node. Change these values:

- `GITHUB_OWNER` — the GitHub organisation or user name
- `GITHUB_REPO` — the repository name
- `LANGUAGE` — `EN` for English or `FR` for French
- `DESTINATION_TYPE` — `discord` or `email`
- `EMAIL_TO` — the recipient email address (only when you use email)

### 4. Set up SMTP credentials (email only)

Click the **Send Email** node. Add SMTP credentials with your mail server
details. Skip this step if you use Discord.

### 5. Activate the workflow

Set the workflow to **Active**. The workflow runs every Friday at 5pm UTC.
Run it once manually with **Execute Workflow** to test.

## Files

- `n8n-workflow-weekly-dev-summary.json` — the importable n8n workflow
- `README.md` — this file
