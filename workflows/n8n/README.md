# Automated Weekly Dev Summary: n8n + Claude Sonnet

An end-to-end importable **n8n workflow** that automatically aggregates weekly engineering achievements (commits, merged pull requests, closed issues) from GitHub, synthesizes a narrative summary using **Claude Sonnet 4**, and broadcasts the report via **Discord / Slack webhook or Email**.

---

## 🌟 Workflow Specifications
- **Trigger:** Automated weekly cron trigger (Default: Friday at 5:00 PM).
- **GitHub Aggregator:** Queries GitHub REST API for commits since `now - 7 days`, closed issues, and merged PRs.
- **Claude API Engine:** Calls `claude-sonnet-4-20250514` to transform commit logs and pull request diffs into an executive engineering digest.
- **Delivery Channels:** Webhook dispatcher for Discord / Slack / Mattermost and SMTP Email.
- **Configurable Variables:**
  - `GITHUB_REPO`: `owner/repo_name`
  - `SUMMARY_LANGUAGE`: `EN` or `FR`
  - `TARGET_CHANNEL`: `DISCORD` or `SLACK` or `EMAIL`

---

## ⚡ 5-Step Setup Instructions

1. **Open n8n:** Access your n8n dashboard (Cloud or Self-Hosted instance).
2. **Import Workflow:** Click **Workflows** -> **Import from File** -> select `weekly_dev_summary_workflow.json`.
3. **Set Variables:** In the `Workflow Configuration` node, enter your GitHub repository name (`owner/repo`), desired language (`EN`/`FR`), and webhook URL.
4. **Add API Credentials:** Configure your **GitHub Personal Access Token** and **Anthropic API Key** in the credentials manager.
5. **Activate Workflow:** Toggle the **Active** switch in the top-right corner to start scheduled execution.
