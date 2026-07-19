# n8n Weekly Dev Summary Workflow (Claude 3.5 Sonnet)

A complete, importable n8n workflow that automatically compiles a narrative summary of a GitHub repository's weekly activity (commits, closed issues, and merged PRs) and delivers it to Discord using Anthropic's Claude 3.5 Sonnet.

## Setup Instructions (4 Steps)

1. **Import the Workflow**: Open your n8n instance, click `Workflows > Add Workflow > Import from File`, and select `n8n_weekly_dev_summary.json`.
2. **Configure Variables**: Double click the **"Set Config Variables"** node and update the 4 string values: `github_owner`, `github_repo`, `discord_webhook`, and `language` (e.g. "English" or "French").
3. **Add Credentials**: In the two `Fetch` nodes (Commits, Issues/PRs), add your `GitHub API` Header Auth if your repo is private. In the `Anthropic Claude API` node, add your `x-api-key` in the Header Auth.
4. **Activate**: Toggle the workflow to **Active** in the top right. It is scheduled to run every Friday at 17:00 (5:00 PM) automatically.

*(Note: Tested screenshot is attached in the Pull Request body).*