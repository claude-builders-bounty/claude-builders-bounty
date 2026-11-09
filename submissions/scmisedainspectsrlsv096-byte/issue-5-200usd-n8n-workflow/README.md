# Weekly GitHub Repo Narrative Summary (`n8n` + `claude-sonnet-4-20250514`)

Automated n8n workflow that runs every Friday at 17:00, fetches the last 7 days of commits, closed issues, and merged PRs from a target GitHub repository, synthesizes an executive narrative via Claude (`claude-sonnet-4-20250514`), and posts it to a Discord or Slack webhook in English (`EN`) or French (`FR`).

## Setup in 4 Steps

1. **Import Workflow:** In n8n, go to **Workflows → Import from File** and select `weekly-github-summary-workflow.json`.
2. **Set Environment Variables (or Edit the Config Node):**
   - `GITHUB_REPO`: `owner/repo` (e.g., `anthropics/claude-code`)
   - `GITHUB_TOKEN`: Personal Access Token with `repo` / `public_repo` read access
   - `ANTHROPIC_API_KEY`: Your Anthropic API key (`sk-ant-...`)
   - `DESTINATION_WEBHOOK_URL`: Your Slack or Discord incoming webhook URL
   - `SUMMARY_LANGUAGE`: `EN` (English) or `FR` (French)
3. **Test Execution:** Click **Test workflow** in the n8n canvas to run an immediate 7-day summary and deliver it to your webhook channel.
4. **Activate Schedule:** Toggle the workflow to **Active** to run automatically every Friday at 17:00 (`0 17 * * 5`).
