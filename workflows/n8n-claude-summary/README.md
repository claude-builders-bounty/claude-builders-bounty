 # Weekly Dev Summary (n8n + Claude)

 Automated weekly digest of GitHub activity synthesized by Claude and delivered to Discord, Slack, or Email.

 ## Setup

 1. Import `weekly-dev-summary.json` into your n8n instance (`Settings → Import from File`).
 2. Set credentials for **GitHub API**, **Anthropic API**, and your delivery channel (Discord webhook / Slack / SMTP).
 3. Configure environment variables in n8n Settings → Environment Variables:
    - `GITHUB_REPO` – e.g. `owner/repo`
    - `GITHUB_TOKEN` – PAT with `repo` scope
    - `ANTHROPIC_API_KEY` – key with access to `claude-sonnet-4-20250514`
    - `SUMMARY_LANGUAGE` – e.g. `en`, `pt-BR`
    - `DISCORD_WEBHOOK_URL` / `SLACK_WEBHOOK_URL` / SMTP vars as needed
 4. Activate the workflow; the cron triggers every Monday at 09:00 UTC.
 5. Test manually via "Execute Workflow" to verify connectivity and output format.

 ## Notes

 - The Claude node uses `claude-sonnet-4-20250514`; update the model string if a newer version is preferred.
 - Ensure the GitHub token has read access to commits, issues, and pull requests.
 - Delivery nodes are mutually exclusive; disable unused channels to avoid errors.
