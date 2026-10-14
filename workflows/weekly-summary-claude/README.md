# Automated Weekly GitHub Activity Summary (n8n + Claude Code)

Production-ready n8n workflow that generates a weekly narrative summary of a GitHub repository's activity using Claude API and delivers it via Discord/Slack webhook.

## Acceptance Criteria Verified
- [x] Importable `.json` workflow (`workflow.json`).
- [x] Weekly cron schedule (Friday 5:00 PM).
- [x] Real-time fetch of commits and closed issues for the past 7 days.
- [x] Narrative AI synthesis via Anthropic Claude API (`claude-3-5-sonnet`).
- [x] Webhook delivery (Discord / Slack compatible).
- [x] Fully configurable (Repo, Language FR/EN, Webhook URL).

---

## Setup Instructions (4 Steps)

1. **Import Workflow**:
   In your n8n workspace, navigate to **Workflows** → **Add Workflow** → Click `...` (top right) → **Import from File**, and select `workflow.json`.

2. **Configure Variables**:
   Open the **Configurable Variables** node and set:
   - `REPO_OWNER`: Your GitHub organization or username.
   - `REPO_NAME`: Target repository name.
   - `LANGUAGE`: `EN` or `FR`.
   - `DISCORD_WEBHOOK_URL`: Your channel webhook URL.

3. **Set API Credentials**:
   Add your `ANTHROPIC_API_KEY` in n8n credentials or environment variables.

4. **Activate**:
   Toggle the workflow to **Active**. It will automatically trigger every Friday at 17:00, or click **Test step** to test immediately.
