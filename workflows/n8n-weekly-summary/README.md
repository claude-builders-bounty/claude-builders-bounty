# Automated Weekly Dev Summary (n8n + Claude Code) 📊

An automated n8n workflow that triggers every Friday at 5:00 PM, aggregates GitHub engineering activity (commits, closed issues, merged PRs) across the past 7 days, synthesizes a narrative summary using the Claude API (`claude-sonnet-4-20250514`), and broadcasts it to Discord or Slack.

## Quick Setup (4 Steps)

1. **Import Workflow**:
   In your n8n instance, click **Workflows** > **Import from File** and upload `workflow.json`.

2. **Configure Anthropic API Key**:
   In n8n, navigate to **Credentials** or set your environment variable:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```

3. **Configure Project Variables**:
   Double-click the **Config Variables** node and set:
   - `GITHUB_REPO`: `owner/repo-name` (e.g. `facebook/react`)
   - `DESTINATION_WEBHOOK`: Your Discord or Slack incoming webhook URL
   - `LANGUAGE`: `EN` or `FR` (selects English or French narrative)

4. **Activate & Test**:
   Click **Execute Workflow** to run a test execution immediately, then toggle the workflow to **Active** to run automatically every Friday at 5:00 PM.

## Architecture

```
[Cron: Every Friday 5PM]
       ↓
[Config Variables] → [Calculate 7-Day Window]
       ↓                         ↓
[Fetch GitHub Commits]    [Fetch Closed Issues & PRs]
       ↘                         ↙
       [Aggregate Activity & Prompt]
                   ↓
   [Claude Sonnet API (claude-sonnet-4-20250514)]
                   ↓
      [Deliver via Webhook (Discord/Slack)]
```

## Features

- **Multi-Source Ingestion**: Fetches commits, closed issues, and merged pull requests via GitHub's REST API.
- **Bilingual Narrative Engine**: Supports both English and French executive reports.
- **Zero Heavy Dependencies**: Pure HTTP request and JavaScript code nodes compatible with all self-hosted and cloud n8n instances.
