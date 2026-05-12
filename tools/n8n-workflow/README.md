# Claude Weekly Dev Summary Workflow (n8n)

An automated n8n workflow that fetches your GitHub activity (commits, PRs, issues) once a week and uses Claude 3.5 Sonnet to generate a narrative executive summary, delivered straight to your Discord channel.

## Features
- **Cron Trigger**: Automatically runs every Friday at 5:00 PM.
- **Deep Analysis**: Uses Claude 3.5 Sonnet to turn raw commit messages into a readable story.
- **Multi-Source**: Aggregates data from GitHub commits, merged PRs, and closed issues.
- **Instant Delivery**: Posts the summary to a Discord webhook.

## Setup in 4 Steps

1. **Import**: Open n8n and import the `claude_weekly_summary_workflow.json` file.
2. **Configure Credentials**:
   - Add your **GitHub Personal Access Token**.
   - Add your **Anthropic API Key** (Header Auth: `x-api-key`).
3. **Set Variables**:
   - Edit the `Config` node to set your GitHub `owner`, `repo`, and `discord_webhook` URL.
4. **Activate**: Click 'Execute Workflow' to test, then toggle the 'Active' switch.

## Execution Screenshot
![n8n Execution Successful](https://github.com/thanhdatloveyou18-coder/claude-builders-bounty/raw/main/tools/n8n-workflow/screenshot.png)

*Developed for the Opire $200 Workflow Bounty.*
