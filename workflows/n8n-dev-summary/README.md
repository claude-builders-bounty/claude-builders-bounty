# n8n + Claude Code: Weekly Dev Summary

An automated n8n workflow that triggers every Friday at 5 PM. It fetches the week's commits, closed issues, and merged PRs from a GitHub repository, sends the raw data to the Claude API (using `claude-3-5-sonnet`), and emails a professionally formatted narrative summary to the engineering team.

## Setup Instructions

1. **Import the Workflow**: Open your n8n instance. Go to Workflows -> Add Workflow. Click the top-right menu and select "Import from File". Select `weekly_github_summary.json`.
2. **Configure GitHub Credentials**: Open the "Get Closed Issues & PRs" and "Get Commits" nodes and attach your GitHub OAuth2 or Personal Access Token credentials.
3. **Configure Anthropic Credentials**: Open the "Claude API" node and provide your Anthropic API Key.
4. **Set Variables**: Open the "Set Config Variables" node and update:
   - `repoOwner`: e.g., "facebook"
   - `repoName`: e.g., "react"
   - `destinationEmail`: The email address to receive the summary.
   - `language`: Set the output language (e.g., "English", "French").
5. **Configure Email Credentials**: Open the "Send Email" node and add your SMTP credentials (or replace this node with a Slack/Discord webhook node if preferred).
6. **Activate**: Toggle the workflow to "Active". It will now run automatically every Friday at 5 PM!
