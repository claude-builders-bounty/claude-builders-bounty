# Weekly Dev Summary — n8n Workflow

Automated weekly development summary using GitHub API + Claude API + Discord webhook.

## Setup (5 Steps)

### 1. Import the workflow
- Open n8n, go to **Workflows → Import from File**
- Select `n8n-weekly-summary.json`

### 2. Configure credentials
Create two **Header Auth** credentials in n8n (`⚙️ → Credentials → Add Credential → Header Auth`):

| Credential Name | Header Name | Header Value |
|---|---|---|
| `GitHub API` | `Authorization` | `Bearer ghp_your_token_here` |
| `Claude API` | `x-api-key` | `sk-ant-your_api_key_here` |

> **GitHub token** needs `repo` scope. Generate at https://github.com/settings/tokens
> **Claude API key** at https://console.anthropic.com/

### 3. Set your variables
Open the **Configuration** node and update:
- `repoOwner` — GitHub org/user (default: `claude-builders-bounty`)
- `repoName` — GitHub repo name (default: `claude-builders-bounty`)
- `webhookUrl` — Your Discord webhook URL
- `language` — `EN` (English) or `FR` (French)

### 4. Activate the workflow
Toggle the workflow to **Active**. It triggers every **Friday at 5:00 PM UTC**.

### 5. Test manually
Click **Execute Workflow** to run an immediate test. Check the Discord channel for the summary.

---

## Workflow Diagram

```
Weekly Cron (Fri 5pm)
  → Configuration (repo, webhook, language)
    → Build GitHub Query (GraphQL with date range)
      → GitHub GraphQL API (commits, issues, PRs)
        → Format Prompt (build Claude prompt)
          → Claude API (claude-sonnet-4-20250514)
            → Check Success
              ├── Yes → Send to Discord
              └── No  → Error Handler (fallback)
```

## Architecture

- **Trigger**: n8n Schedule Trigger — cron `0 17 * * 5`
- **Data Source**: GitHub GraphQL API (single query fetches commits, closed issues, merged PRs in one request)
- **AI Summary**: Anthropic Claude API (`claude-sonnet-4-20250514`) generates a 3–5 paragraph narrative
- **Delivery**: Discord webhook (supports embeds and markdown)
- **Error Handling**: IF node checks Claude API response validity; errors route to a fallback NoOp node

## Customization

- Change the cron schedule in the **Weekly Cron** node
- Swap Discord for Slack by replacing the **Send to Discord** node with a Slack Webhook node
- Adjust the prompt template in the **Format Prompt** Code node
