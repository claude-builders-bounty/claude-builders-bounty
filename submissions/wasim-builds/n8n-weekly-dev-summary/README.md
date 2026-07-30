# n8n + Claude Code — Weekly Dev Summary

Exportable n8n workflow that automatically generates a weekly development summary from GitHub activity using Claude Sonnet.

## What it does

- Triggers every Friday at 17:00 UTC
- Fetches commits, closed issues, and merged PRs from the last 7 days
- Sends them to Claude Sonnet 4 with a summarization prompt
- Delivers a clean markdown summary to Slack and/or email

## Setup

### 1. Import the workflow

1. Open n8n
2. Go to **Workflows** → **Import from File**
3. Select `workflow.json`
4. The workflow will appear as **Weekly Dev Summary - Claude + GitHub**

### 2. Configure GitHub credentials

1. In n8n, go to **Settings** → **Credentials**
2. Add a **GitHub API** credential with a token that has `repo` scope
3. In the workflow, edit each GitHub node and select your credential

### 3. Configure Claude API

1. Add a **Anthropic API** credential in n8n with your Claude API key
2. In the **Claude Summary** node, select the credential
3. Verify the model is set to `claude-3-5-sonnet-20240620`

### 4. Configure delivery channels

**Slack:**
- Add a Slack credential in n8n
- Select the target channel in the **Deliver to Slack** node

**Email:**
- Add an email credential (SMTP) in n8n
- Update the recipient in the **Deliver via Email** node

### 5. Activate the workflow

1. Click **Save** in the workflow editor
2. Toggle **Active** to on
3. Test by clicking **Execute Workflow** manually
4. Verify delivery in Slack/email

## File structure

```
submissions/wasim-builds/n8n-weekly-dev-summary/
├── workflow.json   # Importable n8n workflow
└── README.md       # Setup instructions
```

## Customization

- Change the cron schedule in the **Weekly Trigger** node
- Modify the Claude prompt in the **Claude Summary** node
- Add/remove delivery channels as needed

## License

MIT
