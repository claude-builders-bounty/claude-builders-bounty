# n8n Weekly Dev Summary Workflow

Automated weekly narrative summary of a GitHub repo's activity using Claude API.

## 🚀 Setup (5 Steps)

1. **Import the workflow** — Open n8n → Settings → Import from File → select `weekly-dev-summary.json`

2. **Configure GitHub credentials** — In n8n, go to Credentials → Add Credential → GitHub API (Personal Access Token with `repo` scope)

3. **Configure Claude API key** — Add an HTTP Header Auth credential with:
   - Name: `x-api-key`
   - Value: Your Anthropic API key

4. **Set your variables** — Open the workflow and edit the "Config" node:
   - `GITHUB_REPO`: `owner/repo` (e.g., `facebook/react`)
   - `LANGUAGE`: `EN` or `FR`
   - `WEBHOOK_URL`: Your Discord/Slack webhook URL

5. **Activate the workflow** — Toggle the workflow to Active. It runs every Friday at 5pm UTC.

## 📋 What It Does

Every Friday at 5pm:

1. Fetches the past week's **commits**, **closed issues**, and **merged PRs** from the GitHub API
2. Sends all activity data to **Claude claude-sonnet-4-20250514** for narrative analysis
3. Generates a structured summary with:
   - Overview of the week's development
   - Key changes and their impact
   - Notable contributions
   - Trends and patterns
4. Delivers the summary to your **Discord or Slack** channel via webhook

## 🔧 Configuration Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO` | Target repository (owner/repo) | `vercel/next.js` |
| `LANGUAGE` | Summary language | `EN` or `FR` |
| `WEBHOOK_URL` | Discord/Slack webhook URL | `https://discord.com/api/webhooks/...` |

## 📸 Execution Screenshot

See `execution-screenshot.md` for successful execution evidence.

## License

MIT
