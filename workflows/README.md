# 📊 GitHub Weekly Narrative Dev Summary with n8n & Claude

An automated n8n workflow that pulls weekly commits, closed issues, and pull requests from any GitHub repository, sends the telemetry to **Claude API (`claude-sonnet-4-20250514`)**, and publishes an engaging narrative summary to Discord or Slack.

## 🚀 Setup Instructions in 5 Steps

1. **Import Workflow:** Open your n8n dashboard, click **Workflows -> Import from File**, and select `n8n-claude-weekly-dev-summary.json`.
2. **Set Configuration:** Double-click the **Set Variables** node and configure your target `repo_owner`, `repo_name`, `destination_webhook`, and preferred `language` (EN/FR).
3. **Configure Claude API:** Set your `ANTHROPIC_API_KEY` in n8n Environment Variables or in the **Claude API** node header parameters.
4. **Connect GitHub Credentials:** Authenticate the **GitHub** node with your GitHub OAuth2 or Personal Access Token.
5. **Activate Schedule:** Toggle the workflow to **Active** to trigger automatically every Friday at 5:00 PM (or test manually with "Test workflow").

---
*Created for [claude-builders-bounty #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5) — Powered by Opire.*
