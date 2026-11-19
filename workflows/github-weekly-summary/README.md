# n8n + Claude API: Automated Weekly Dev Summary

An automated n8n workflow that monitors any GitHub repository and generates an executive weekly narrative summary using Claude Sonnet (`claude-sonnet-4-20250514`), delivering updates via Discord or Slack webhooks every Friday at 5:00 PM.

## Setup in 4 Steps
1. **Import Workflow**: In your n8n workspace, click **Add Workflow** → **Import from File** and select `workflows/github-weekly-summary/workflow.json`.
2. **Configure Variables**: In the **Workflow Variables** node, set:
   - `GITHUB_REPO`: `owner/repo`
   - `DISCORD_WEBHOOK_URL`: Your Discord or Slack incoming webhook URL
   - `LANGUAGE`: `EN` (or `FR`)
3. **Add API Credentials**: Set environment variable `ANTHROPIC_API_KEY` (or supply in the Claude API node headers). Optionally configure GitHub OAuth/Token for private repositories.
4. **Activate**: Toggle the workflow to **Active**. The Cron node triggers automatically every Friday at 5:00 PM.
