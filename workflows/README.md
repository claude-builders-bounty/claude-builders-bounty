# Weekly Dev Summary (n8n + Claude)

Automated weekly engineering digest for **[BOUNTY $200] WORKFLOW: n8n + Claude — automated weekly dev summary** (`claude-builders-bounty/claude-builders-bounty#5`).

## What it does

Every Monday 09:00 UTC:

1. Computes the last-7-days window
2. Pulls GitHub commits + closed PRs for `GITHUB_OWNER/GITHUB_REPO`
3. Builds a structured digest (counts, top authors, commit/PR lines)
4. Calls Claude (`ANTHROPIC_MODEL`, default Sonnet) for a manager-style Markdown summary
5. Posts to Slack and emails the same summary

## Import

1. Open n8n → **Workflows** → **Import from File**
2. Select `weekly-dev-summary.json`
3. Create credentials:
   - **GitHub Token** — Header Auth  
     - Name: `Authorization`  
     - Value: `Bearer <GITHUB_PAT>` (repo scope)
   - **Anthropic API Key** — Header Auth  
     - Name: `x-api-key`  
     - Value: `<ANTHROPIC_API_KEY>`
   - **Slack Bot** — Slack OAuth / Bot token with `chat:write`
   - **SMTP** — any outbound mail account
4. Bind those credentials on the HTTP Request / Slack / Email nodes
5. Set environment variables (n8n env or workflow vars):

| Variable | Example | Purpose |
|---|---|---|
| `GITHUB_OWNER` | `mamenesia` | repo owner |
| `GITHUB_REPO` | `claude-builders-bounty` | repo name |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | Claude model id |
| `SLACK_CHANNEL_ID` | `C0123456789` | destination channel |
| `EMAIL_FROM` | `bot@example.com` | from address |
| `EMAIL_TO` | `eng@example.com` | recipient |

6. Activate the workflow

## Manual test

- Disable the Schedule node temporarily
- Click **Test workflow** on **Compute Week Window**
- Confirm Claude returns Markdown and Slack/email fire (or check execution data if those creds are missing — both output nodes `continueOnFail`)

## Design notes

- Uses HTTP Request nodes for GitHub + Anthropic so the template works on n8n OSS without marketplace nodes
- PR filter is `merged_at` inside the week window (not just `updated`)
- Prompt forbids inventing commits/PRs — grounded on the digest only
- Slack payload truncated to ~3500 chars to stay under typical message limits

## Files

- `weekly-dev-summary.json` — importable n8n workflow
- `README.md` — this setup guide
