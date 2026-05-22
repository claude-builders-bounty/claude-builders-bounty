# n8n Weekly GitHub Summary Workflow

An n8n workflow that runs every Friday at 5 PM, fetches the past week's GitHub activity (commits, closed issues, merged PRs), sends it to Claude (`claude-sonnet-4-20250514`) for a narrative summary, and posts the result to Discord.

## Setup (5 steps)

### 1. Import the workflow

Open your n8n instance → **Workflows** → **Import from File** → select `workflow.json`.

### 2. Create the GitHub credential

Go to **Credentials** → **Add Credential** → **Header Auth**.

| Field | Value |
|-------|-------|
| **Name** | `GitHub Token` (must match exactly) |
| **Header Name** | `Authorization` |
| **Header Value** | `Bearer ghp_YOUR_GITHUB_TOKEN` |

Generate a token at [github.com/settings/tokens](https://github.com/settings/tokens) with `repo` (read) scope.

### 3. Create the Anthropic credential

Go to **Credentials** → **Add Credential** → **Header Auth**.

| Field | Value |
|-------|-------|
| **Name** | `Anthropic API Key` (must match exactly) |
| **Header Name** | `x-api-key` |
| **Header Value** | `sk-ant-YOUR_ANTHROPIC_KEY` |

Get a key at [console.anthropic.com](https://console.anthropic.com/).

### 4. Configure variables

Open the **Set Variables** node in the workflow and edit:

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_REPO` | `BerriAI/litellm` | Owner/repo to summarize |
| `DISCORD_WEBHOOK` | *(empty)* | Your Discord webhook URL ([how to create one](https://support.discord.com/hc/en-us/articles/228383668)) |
| `LANGUAGE` | `EN` | Summary language: `EN` or `FR` |
| `DAYS_BACK` | `7` | Number of days of history to fetch |

### 5. Activate

Toggle the workflow **Active**. It will run every Friday at 5 PM. To test immediately, click **Execute Workflow**.

---

## Workflow Overview

```
┌──────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────────────┐
│ Cron Trigger │───▶│ Set Variables│───▶│ GitHub: Commits  │───▶│ GitHub: Closed Issues│
│ Fri 5pm     │    │              │    │                  │    │                      │
└──────────────┘    └──────────────┘    └─────────────────┘    └──────────┬───────────┘
                                                                          │
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐    ┌────────▼──────────┐
│ Discord Post │◀───│ Claude API Call   │◀───│ Build Prompt │◀───│ GitHub: Merged PRs│
│              │    │ claude-sonnet-4-20250514│              │    │                   │
└──────────────┘    └──────────────────┘    └──────────────┘    └───────────────────┘
```

**Nodes used** (all built-in, no community nodes):
- `n8n-nodes-base.scheduleTrigger` — weekly cron
- `n8n-nodes-base.set` — configurable variables
- `n8n-nodes-base.httpRequest` — GitHub API (×3), Claude API, Discord webhook
- `n8n-nodes-base.code` — data aggregation and prompt building

## Notes

- **Discord message limit**: The summary is truncated to 2000 characters to fit Discord's message limit.
- **GitHub rate limits**: Unauthenticated requests are limited to 60/hour. The GitHub Token credential avoids this (5000/hour).
- **Language**: Set `LANGUAGE` to `FR` for a French summary. The Claude prompt adapts automatically.
- **No community nodes**: This workflow uses only built-in n8n nodes and works on any n8n instance (self-hosted or cloud).
