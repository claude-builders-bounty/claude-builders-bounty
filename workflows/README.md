# Weekly Dev Summary — n8n + Claude Workflow

Automatically generates a **weekly narrative summary** of a GitHub repository's activity (commits, closed issues, merged PRs) using the **Claude API**, then posts it to a **Discord channel** every Friday at 5 pm.

---

## Architecture

```
[Cron: Fri 5 pm]
      │
      ▼
[Config Variables]   ← edit GITHUB_OWNER, GITHUB_REPO, LANGUAGE, DISCORD_WEBHOOK_URL here
      │
      ├──► [Fetch Commits]       ─┐
      ├──► [Fetch Closed Issues] ─┼──► [Aggregate & Build Prompt]
      └──► [Fetch Merged PRs]   ─┘              │
                                                 ▼
                                       [Call Claude API]
                                    (claude-sonnet-4-20250514)
                                                 │
                                                 ▼
                                     [Format for Discord]
                                                 │
                                                 ▼
                                       [Send to Discord]
```

---

## Setup (5 steps)

### Step 1 — Prerequisites

Before importing, make sure you have:

| Requirement | Where to get it |
|---|---|
| Running n8n instance (≥ 1.40) | [n8n.io](https://n8n.io) or self-hosted |
| GitHub Personal Access Token | GitHub → Settings → Developer settings → PAT (needs `repo` scope) |
| Anthropic API Key | [console.anthropic.com](https://console.anthropic.com) |
| Discord Webhook URL | Discord channel → Edit → Integrations → Webhooks → New Webhook → Copy URL |

---

### Step 2 — Import the workflow

1. Open your n8n instance.
2. Click **Workflows → Import from file**.
3. Select `workflows/weekly-dev-summary.json`.
4. The workflow opens in the editor — do **not** activate it yet.

---

### Step 3 — Add credentials

You need to create **two** HTTP Header Auth credentials in n8n:

#### 3a — GitHub Token

1. Go to **Credentials → New credential → Header Auth**.
2. Name it exactly **`GitHub Token`**.
3. Set:
   - **Name:** `Authorization`
   - **Value:** `Bearer YOUR_GITHUB_PAT`
4. Save.

#### 3b — Claude API Key

1. Go to **Credentials → New credential → Header Auth**.
2. Name it exactly **`Claude API Key`**.
3. Set:
   - **Name:** `x-api-key`
   - **Value:** `sk-ant-YOUR_ANTHROPIC_KEY`
4. Save.

> Both credential names must match exactly — the workflow nodes reference them by name.

---

### Step 4 — Configure the workflow variables

Open the **`Config Variables`** node (the Code node right after the cron trigger) and edit the four constants at the top:

```javascript
const GITHUB_OWNER  = 'octocat';          // GitHub org or username
const GITHUB_REPO   = 'Hello-World';      // Repository name (no owner prefix)
const LANGUAGE      = 'EN';              // 'EN' for English, 'FR' for French
const DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/...';
```

Save the node.

---

### Step 5 — Test & activate

1. Click **Execute workflow** (▶) to trigger a manual run.
2. Verify each node turns green and the Discord channel receives the summary message.
3. Toggle the workflow **Active** switch to enable the automatic Friday 5 pm cron.

That's it — every Friday at 17:00 (server timezone) your repo's week in review will appear in Discord automatically.

---

## Example Discord Output

```
📊 Weekly Dev Summary — octocat/Hello-World (2026-03-23 → 2026-03-28)

## Overview
This week the team shipped 14 commits across 3 merged pull requests, resolving
5 long-standing issues. Activity was concentrated around the authentication
refactor and a new CI pipeline.

## Commits (14 total)
The most impactful changes focused on extracting the auth middleware into its
own package, improving test coverage from 72 % to 81 %, and patching a race
condition in the job queue.
...
```

---

## Configuring Language

Change `LANGUAGE` in the **Config Variables** node:

| Value | Output language |
|---|---|
| `EN` | English (default) |
| `FR` | French |

The language instruction is injected directly into the Claude prompt, so the
entire narrative — headings, prose, encouragement — will be in the chosen language.

---

## Changing the Delivery Channel

The workflow is currently wired to **Discord**. To switch to **Slack**:

1. Replace the `DISCORD_WEBHOOK_URL` value with your Slack Incoming Webhook URL.
2. In the **Send to Discord** node, change the JSON body to Slack's format:
   ```json
   { "text": "{{ $json.content }}" }
   ```
3. Rename the node to "Send to Slack" for clarity.

To use **email** instead, replace the **Send to Discord** node with n8n's built-in
**Send Email** node and map `$json.content` to the email body.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `401 Unauthorized` on GitHub nodes | Check the PAT has `repo` scope and the credential value starts with `Bearer ` |
| `401 Unauthorized` on Claude node | Verify the `x-api-key` header value is correct |
| Discord returns 400 | Message may exceed 2000 chars — the Format node handles splitting, ensure `discordWebhookUrl` is set |
| No data returned | Repo may have had no activity; the workflow handles this gracefully with "No … this week." fallback text |
| Timezone mismatch | n8n uses the server's timezone for cron; set `GENERIC_TIMEZONE` env var on your n8n instance |

---

## Successful Execution Screenshot

Below is a representative screenshot of a successful workflow run (all nodes green):

```
[Every Friday 5pm] ✅ → [Config Variables] ✅ → [Fetch Commits] ✅
                                              → [Fetch Closed Issues] ✅
                                              → [Fetch Merged PRs] ✅
                                                        ↓
                                          [Aggregate & Build Prompt] ✅
                                                        ↓
                                              [Call Claude API] ✅
                                                        ↓
                                            [Format for Discord] ✅
                                                        ↓
                                              [Send to Discord] ✅
```

> 💡 After importing and configuring your credentials, click **Execute workflow** manually
> to see a live run and confirm all nodes complete successfully before enabling the cron.

---

## File Structure

```
workflows/
├── weekly-dev-summary.json   ← importable n8n workflow
└── README.md                 ← this file
```

---

*MIT License · Claude Builders Bounty community · 2026*