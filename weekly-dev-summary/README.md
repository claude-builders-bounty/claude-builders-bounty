# Automated Weekly GitHub Dev Summary (n8n + Claude API)

An importable, production-ready **n8n workflow** ([`weekly-dev-summary.json`](./weekly-dev-summary.json)) that runs on a weekly cron schedule, fetches the last 7 days of GitHub repository activity (commits, closed issues, and merged PRs with automatic pagination and zero-item resiliency), generates an executive + technical narrative summary using **Claude Sonnet 4** (`claude-sonnet-4-20250514`), and delivers it to **Slack, Discord, or Email**.

![n8n Weekly Dev Summary Execution Screenshot](./execution-screenshot.png)

---

## Quick Setup (5 Steps)

1. **Import the Workflow into n8n**
   Open your n8n instance, click **Workflows → Add Workflow → Import from File**, and select [`weekly-dev-summary.json`](./weekly-dev-summary.json).

2. **Configure API & Delivery Credentials**
   Set your GitHub and Anthropic API keys in your n8n environment variables:
   ```bash
   export GITHUB_TOKEN="ghp_your_github_token"
   export ANTHROPIC_API_KEY="sk-ant-your_anthropic_key"
   # Optional — required only if using Slack Bot API (chat.postMessage) or SMTP Email delivery:
   export SLACK_BOT_TOKEN="xoxb-your-slack-bot-token"
   export SMTP_FROM_EMAIL="dev-digest@yourdomain.com"
   ```
   *(If using `DELIVERY_METHOD=email`, also attach your SMTP credential to the **`Deliver via Email`** node in n8n and set `SMTP_FROM_EMAIL`.)*

3. **Set Repository, Destination Channel, and Language (`EN` / `FR`)**
   Open the **`Workflow Configuration`** node (or use environment variables) to set:
   - `GITHUB_REPO`: Target repository in `owner/repo` format (e.g., `anthropics/claude-code`)
   - `DESTINATION_CHANNEL`: Routes the summary to your target destination:
     - **Slack**: Channel name or ID (e.g., `#dev-updates` or `C0123456789`) passed as `channel` in the webhook / `chat.postMessage` payload
     - **Discord**: Thread ID (auto-appended as `?thread_id=...` when numeric) or channel label displayed in the rich `embeds` header/footer (full narrative delivered via multi-embed chunking up to 4,096 chars per embed — never truncated at 1,990 chars)
     - **Email**: Recipient email address(es) passed to `toEmail` (e.g., `engineering@yourdomain.com`)
   - `LANGUAGE`: `EN` (English) or `FR` (Français)
   - `DELIVERY_METHOD`: `webhook` (Slack/Discord incoming webhook), `slack_api` (`https://slack.com/api/chat.postMessage`), or `email` (SMTP)
   - `WEBHOOK_URL`: Your Slack or Discord Incoming Webhook URL (when using webhook delivery)

4. **Test the Workflow**
   Click **Test workflow** (or **Execute Workflow**) in the n8n editor to verify that commits, closed issues, and merged PRs are fetched, summarized by `claude-sonnet-4-20250514`, and delivered to `DESTINATION_CHANNEL`.

5. **Activate the Weekly Schedule**
   Toggle the workflow switch to **Active**. The **`Weekly Schedule Trigger`** fires automatically every **Friday at 5:00 PM (`0 17 * * 5`)**.

---

## Workflow Architecture & Production Safeguards

| Node | Type | Key Production Features |
|------|------|-------------------------|
| **1. Weekly Schedule Trigger** | `n8n-nodes-base.scheduleTrigger` | Fires weekly on cron `0 17 * * 5` (Fridays at 17:00). |
| **2. Workflow Configuration** | `n8n-nodes-base.set` | Centralizes `GITHUB_REPO`, `DESTINATION_CHANNEL`, `LANGUAGE` (`EN`/`FR`), `DELIVERY_METHOD`, `WEBHOOK_URL`, and 7-day timestamps (`SINCE_ISO`, `UNTIL_ISO`). |
| **3. Fetch Weekly Commits** | `n8n-nodes-base.httpRequest` | `GET /repos/{owner}/{repo}/commits` with `alwaysOutputData: true`, `executeOnce: true`, and automatic pagination (`per_page=100`, up to 10 pages). |
| **4. Fetch Closed Issues** | `n8n-nodes-base.httpRequest` | `GET /repos/{owner}/{repo}/issues?state=closed` with `alwaysOutputData: true`, `executeOnce: true`, and automatic pagination. |
| **5. Fetch Closed PRs** | `n8n-nodes-base.httpRequest` | `GET /repos/{owner}/{repo}/pulls?state=closed` with `alwaysOutputData: true`, `executeOnce: true`, and automatic pagination. |
| **6. Aggregate Activity & Build Prompt** | `n8n-nodes-base.code` | Deduplicates multi-page results, filters out PRs from `/issues`, retains only issues closed and PRs merged in the 7-day window, and builds the `EN`/`FR` prompt. |
| **7. Claude Narrative Summary** | `n8n-nodes-base.httpRequest` | Calls `POST https://api.anthropic.com/v1/messages` with `claude-sonnet-4-20250514` (`max_tokens: 2048`, `temperature: 0.3`). |
| **8. Format Delivery Payload** | `n8n-nodes-base.code` | Routes `DESTINATION_CHANNEL` for Slack (`channel`), Discord (`?thread_id=` + non-truncated 4,096-char `embeds`), and Email (`toEmail`). |
| **9. Route Delivery Channel** | `n8n-nodes-base.switch` | Routes between `Deliver via Email` (`DELIVERY_METHOD=email`) and `Deliver to Slack or Discord Webhook`. |
| **10. Deliver to Slack / Discord / Email** | `httpRequest` / `emailSend` | Sends the weekly digest via Slack/Discord webhook (or `chat.postMessage` with `SLACK_BOT_TOKEN`) or SMTP (`SMTP_FROM_EMAIL`). |
