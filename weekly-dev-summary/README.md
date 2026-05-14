# Weekly Dev Summary — n8n Workflow

Generates a narrative weekly development summary for any GitHub repo using an LLM (Claude API / OpenAI-compatible).

## Setup (5 steps)

1. **Install n8n** — `npm install -g n8n` or use [n8n.cloud](https://n8n.cloud)
2. **Import workflow** — In n8n UI, go to **Workflows → Import from File**, select `weekly-dev-summary.json`
3. **Configure variables** — Edit the **⚙️ Config Variables** node:
   | Variable | Description |
   |----------|-------------|
   | `repo` | GitHub repo (`owner/repo-name`) |
   | `language` | `EN` or `FR` |
   | `webhookUrl` | Slack/Discord/Teams webhook URL |
   | `llmApiUrl` | LLM API endpoint |
   | `llmModel` | Model name (e.g. `claude-sonnet-4-20250514`) |
   | `githubToken` | GitHub PAT with `repo` scope |
4. **Add API keys** — Set your LLM API key (`Bearer` token) in the **🤖 Call LLM API** node header
5. **Activate** — Toggle the workflow to **Active** (runs every Friday at 5pm UTC)

## What it does

- ⏰ **Triggers** weekly (Friday 5pm, configurable)
- 📥 **Fetches** commits, closed issues, and merged PRs from the past 7 days
- 🤖 **Generates** a narrative summary using Claude/DeepSeek/OpenAI (3-5 paragraphs)
- 📬 **Delivers** the summary to Slack, Discord, email, or any webhook

## Requirements

- n8n (self-hosted or cloud)
- GitHub PAT with repo access
- LLM API key (OpenAI, Anthropic, or any OpenAI-compatible endpoint)

## Customization

- **Cron schedule**: Edit the **⏰ Schedule Trigger** node
- **Delivery channel**: Replace the webhook URL or add an email node
- **Language**: Set `language` to `EN` (English) or `FR` (French)
