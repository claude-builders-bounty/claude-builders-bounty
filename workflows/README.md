# n8n + Claude — Weekly Dev Summary

> Automated weekly narrative summary of GitHub repo activity using Claude API, delivered via Slack.

## Features

- 📅 **Weekly Schedule**: Runs every Friday at 5:00 PM (cron: `0 17 * * 5`)
- 🐙 **GitHub API**: Fetches commits, closed issues, and merged PRs from the past 7 days
- 🤖 **Claude Sonnet 4**: Generates an engaging narrative summary using `claude-sonnet-4-20250514`
- 📨 **Slack Delivery**: Posts the summary to your team's Slack channel via webhook
- 🌐 **Multi-language**: Configurable language support — English (EN) or French (FR)
- ⚙️ **Fully Configurable**: Repo, language, and destination controlled via environment variables

## Workflow Structure

```
Schedule Trigger (Fri 5pm)
    ├── Fetch Commits (past 7 days)
    ├── Fetch Closed Issues (past 7 days)
    └── Fetch Merged PRs (past 7 days)
            ↓
      Merge All Data
            ↓
      Prepare Prompt (language-aware)
            ↓
      Claude API (Sonnet 4)
            ↓
      Deliver to Slack (webhook)
            ↓
      Format Output
```

## Setup Instructions (5 Steps)

### 1. Import the Workflow

1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Select `n8n-weekly-dev-summary.json`

### 2. Configure GitHub Credentials

1. Go to **Settings** → **Credentials** → **Add Credential**
2. Choose **GitHub API**
3. Generate a Personal Access Token at https://github.com/settings/tokens
   - Required scopes: `repo`, `read:user`
4. Enter your token and save

### 3. Configure Claude API (HTTP Header Auth)

1. Go to **Settings** → **Credentials** → **Add Credential**
2. Choose **Header Auth**
3. Set **Name** to `x-api-key` and **Value** to your Anthropic API key
   - Get your key at https://console.anthropic.com
4. Save as "Claude API"

### 4. Set Environment Variables

In your n8n instance, set these environment variables:

```bash
# Required
GITHUB_REPO_OWNER=your-org-or-username
GITHUB_REPO_NAME=your-repo-name
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../xxxxx

# Optional (defaults shown)
SUMMARY_LANGUAGE=EN
```

**To get a Slack webhook URL:**
1. Go to https://api.slack.com/apps → Create New App → From Scratch
2. Enable **Incoming Webhooks**
3. Create a webhook for your target channel
4. Copy the webhook URL

### 5. Activate the Workflow

1. Open the workflow in the n8n editor
2. Review each node's configuration (especially credentials)
3. Toggle **Active** (top-right corner)
4. The workflow will run every Friday at 5:00 PM automatically

## Testing

To test manually:
1. Open the workflow in n8n editor
2. Click **Execute Workflow** (▶️ button)
3. Inspect each node's output to verify data flows correctly
4. Check your Slack channel for the delivered summary

> 💡 **Tip**: Use n8n's **pinData** feature to test with sample data without hitting the APIs repeatedly.

## Output Example

```markdown
# Weekly Development Summary

**Repository:** my-org/my-project
**Period:** 2026-04-22 to 2026-04-29

## 🎯 Key Achievements
- Shipped the new onboarding flow (PR #142)
- Resolved 3 critical bugs reported in production

## 📊 Activity Overview
| Metric | Count |
|--------|-------|
| Commits | 47 |
| Issues Closed | 12 |
| PRs Merged | 8 |

## 🔥 Trends & Patterns
- Frontend team velocity increased 20% week-over-week
- Most activity focused on the v2.1 release branch

## ⚠️ Blockers & Concerns
- CI pipeline instability on macOS runners — tracked in #156

## 👏 Team Highlights
- 🏆 @alice — 15 commits, shipped the auth refactor
- 🚀 @bob — 5 PR reviews, unblocked the dashboard team
```

## Customization

| Setting | Where to Change |
|---------|-----------------|
| **Schedule** | Edit the **Schedule Trigger** node's cron expression |
| **Language** | Set `SUMMARY_LANGUAGE` env var to `EN` or `FR` |
| **Tone** | Modify the system prompt in the **Prepare Prompt** node |
| **Delivery** | Replace `SLACK_WEBHOOK_URL` with an Email node or Discord webhook URL |
| **Repo** | Change `GITHUB_REPO_OWNER` / `GITHUB_REPO_NAME` env vars |

### Switching from Slack to Discord

Replace the **Deliver to Slack** node with another HTTP Request node:
- **Method**: POST
- **URL**: Your Discord webhook URL
- **Body**: `{ "content": "{{ $json.content[0].text }}" }`

## Cost Estimation

- **GitHub API**: Free (within rate limits — 5,000 requests/hour)
- **Claude API**: ~$0.02–0.05 per summary (dependent on repo activity volume)
- **Monthly**: ~$0.10–0.25 for weekly runs

## Troubleshooting

| Issue | Solution |
|-------|----------|
| GitHub 403 errors | Check token scopes (`repo`, `read:user`) and expiry |
| Claude API errors | Verify API key and model availability |
| Slack delivery fails | Ensure webhook URL is active and channel exists |
| Workflow not triggering | Confirm workflow is **Active** and n8n is running |
| Empty summary | Repo may have no activity in past 7 days — normal |

## Acceptance Criteria

- [x] Exportable n8n workflow (`.json` file)
- [x] Trigger: weekly cron (Friday at 5pm — `0 17 * * 5`)
- [x] Fetches commits, closed issues, merged PRs from the past 7 days
- [x] Calls Claude API (`claude-sonnet-4-20250514`) for narrative summary
- [x] Delivers via Slack webhook (documented, swappable to Discord/Email)
- [x] Configurable: repo, destination, language (EN/FR)
- [x] README with 5-step setup

## License

MIT — see repository LICENSE file.
