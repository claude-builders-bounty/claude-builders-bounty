# n8n + Claude API — Automated Weekly Dev Summary

## Setup (5 steps)

### 1. Import the workflow

1. Open n8n (cloud or self-hosted)
2. Click "Import from File"
3. Select `weekly-dev-summary.json`

### 2. Configure credentials

- **GitHub:** Add Header Auth credential with `Authorization: Bearer ghp_xxxx`
- **Anthropic:** Add Header Auth credential with `x-api-key: sk-ant-xxxx`
- **Discord:** Add Header Auth credential or use webhook URL directly

### 3. Set environment variables

In n8n → Settings → Environment Variables:
- `ANTHROPIC_API_KEY`: Your Claude API key
- `GITHUB_TOKEN`: Your GitHub token

### 4. Configure the schedule

Open the "Schedule Trigger" node → set cron to Friday at 5pm (`0 17 * * 5`)

### 5. Activate

Toggle "Active" on the workflow canvas.

## Configurable Variables

| Variable         | Where to set               | Default   |
|-----------------|----------------------------|-----------|
| GitHub repo      | Set node input `repo`      | `owner/repo` |
| Language         | Set node input `language`  | `EN`      |
| Discord webhook  | Set node input `webhook_url` | —      |

## What It Does

1. Every Friday at 5pm, the workflow triggers
2. Fetches: commits (since last Friday), closed issues, merged PRs
3. Aggregates activity into structured data
4. Calls Claude API to generate a narrative summary
5. Delivers summary to Discord channel (or email via SMTP)

## Requirements

- n8n instance (Cloud or self-hosted)
- GitHub token with `repo` scope
- Anthropic API key
- Discord webhook URL (or email SMTP credentials)