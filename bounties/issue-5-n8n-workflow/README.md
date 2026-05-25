# Weekly Dev Summary — n8n + Claude

Generates a narrative weekly summary of a GitHub repository's activity using the Claude API, delivered to Discord (or Slack).

## How It Works

```
Schedule (Fri 5pm) → Config → 3x GitHub API calls → Merge → Build prompt → Claude API → Discord webhook
```

The workflow fetches commits, closed issues, and merged PRs from the past 7 days, sends them to `claude-sonnet-4-20250514` for a narrative summary in English or French, then posts the result to Discord.

---

## Setup (5 Steps)

### 1. Import the workflow
- In n8n, go to **Workflows → Add Workflow → Import from File**
- Select `weekly-dev-summary.json`

### 2. Configure the **Config** node
Open the `Config` code node and edit the top section:

```javascript
const config = {
  repo:           'owner/repo',         // your GitHub repo
  language:       'EN',                 // 'EN' or 'FR'
  claudeApiKey:   'sk-ant-...',         // your Anthropic API key
  discordWebhook: '',                   // Discord webhook URL
  slackWebhook:   '',                   // OR Slack webhook URL
};
```

Set at least one of `discordWebhook` or `slackWebhook`.

### 3. Create a GitHub credential
1. [Generate a GitHub personal access token](https://github.com/settings/tokens) with `repo` scope
2. In n8n, go to **Credentials → Add Credential → Header Auth**
3. Set **Header Name** → `Authorization`, **Header Value** → `token ghp_your_token`
4. Name it `GitHub Token`

### 4. (Optional) Set the schedule
The workflow runs **Friday at 5pm** by default (`0 17 * * 5`).  
Edit the `Schedule Trigger` node to change the cron expression or switch to a different interval.

### 5. Activate
Toggle the workflow **Active** and wait for the next scheduled run — or click **Execute Workflow** to test immediately.

---

## Customization

| What | Where |
|------|-------|
| GitHub repo | `Config` node → `config.repo` |
| Language (EN/FR) | `Config` node → `config.language` |
| Schedule | `Schedule Trigger` node |
| Claude model | `Call Claude` code node → `model` field |
| Delivery channel | Discord or Slack — set the webhook URL in `Config` |

---

## Sample Output

> **Weekly Dev Summary — owner/repo**  
> May 17 – May 24, 2026
>
> _A quiet week with 12 commits, 3 issues closed, and 2 PRs merged. The team focused on bug fixes and dependency upgrades. Alice refactored the auth middleware, Bob landed the new rate limiter, and Carol closed the longest-standing UI bug..._
>
> ### Stats
> - Commits: 12
> - Issues closed: 3
> - PRs merged: 2
> - Unique contributors: 4
