# Automated Weekly Dev Summary (n8n + Claude Code)

This workflow automatically fetches your GitHub repository's commits, closed issues, and merged PRs for the past week, uses the Claude API to generate a narrative summary, and posts it to a Discord webhook.

## Quick Setup (5 Steps)

1. **Import the Workflow**: Open your n8n instance, click **Add Workflow**, then select **Import from File** and upload `weekly_dev_summary_workflow.json`.
2. **Configure GitHub Repo & Language**: Double-click the **Config** node. Change the `GITHUB_REPO` value to your target repository (e.g., `owner/repo`) and the `SUMMARY_LANGUAGE` to your preferred language (e.g., `EN` or `FR`).
3. **Add Anthropic API Key**: Since API keys are sensitive, you must set your Anthropic API key as an environment variable in your n8n server/container instance: `export ANTHROPIC_API_KEY="your_key_here"`.
4. **Add Discord Webhook**: Similarly, set your Discord Webhook URL as an environment variable in your n8n instance to keep it secure: `export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."`.
5. **Activate**: Click the toggle switch in the top right corner of the n8n canvas to **Active**. The workflow will now automatically run every Friday at 5:00 PM (relative to your n8n server's configured timezone)!

> **Note**: This workflow strictly follows secure development guidelines by validating all fetched data subsets, extracting magic variables into a central Config node, and safely avoiding array duplication.
