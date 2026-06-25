# Weekly Dev Summary n8n Workflow

An automated n8n workflow that triggers weekly (Fridays at 5:00 PM), collects your repository's commits, closed issues, and merged pull requests, passes the data to Claude (via the Anthropic API), and posts the generated Markdown summary to a Discord webhook.

## Features

- **Weekly Dev Cron**: Triggers automatically on schedule.
- **Unified GitHub Fetch**: Simultaneously pulls commits, closed issues, and merged pull requests from the past 7 days.
- **Claude Narrative Generator**: Prompts Claude to write a structured weekly summary in the selected language.
- **Discord Delivery**: Formatted directly with markdown blockquotes and headers.
- **Flexible Configuration**: Single `Configuration` node to control repo names, language translations (EN/FR), and API keys.

---

## Setup Instructions (5 Steps)

1. **Import the Workflow**
   Open your n8n workspace, click **Add Workflow** (top right) -> **Import from File**, and select the `weekly_dev_summary.json` file.

2. **Set Configuration Variables**
   Double-click the `Configuration` node and enter your settings:
   - `owner` / `repo`: The repository target.
   - `language`: `EN` or `FR`.
   - `discord_webhook_url`: Your target Discord channel webhook URL.
   - `claude_api_key`: Your Anthropic API Key.

3. **Authenticate GitHub**
   Double-click the three GitHub nodes (`Get Commits`, `Get Closed Issues`, and `Get Closed PRs`) and configure/link your GitHub OAuth2 credentials in n8n.

4. **Test the Workflow**
   Click **Execute Workflow** at the bottom of the n8n canvas to run a test execution. A structured Markdown summary should appear in your Discord channel.

5. **Activate the Cron**
   Toggle the workflow switch from **Inactive** to **Active** (top right) to enable automatic execution every Friday at 5:00 PM.
