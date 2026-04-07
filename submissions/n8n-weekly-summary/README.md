# n8n Weekly Dev Summary with Claude API

Automated weekly narrative summary of your GitHub repo's activity, powered by Claude Sonnet.

## Setup (5 steps)

1. **Import workflow** — Open n8n → Workflows → Import → select `n8n-weekly-dev-summary.json`

2. **Set environment variables** in n8n Settings → Variables:
   | Variable | Value |
   |----------|-------|
   | `GITHUB_REPO` | `owner/repo` (e.g. `facebook/react`) |
   | `ANTHROPIC_API_KEY` | Your Anthropic API key |
   | `WEBHOOK_URL` | Discord/Slack webhook URL |
   | `SUMMARY_LANG` | `EN` or `FR` |

3. **Add GitHub credential** — Settings → Credentials → New → Header Auth → Name: `GitHub Token`, Header: `Authorization`, Value: `Bearer ghp_YOUR_TOKEN`

4. **Activate workflow** — Toggle the workflow ON

5. **Test** — Click "Execute Workflow" to run immediately

## How it works

```
Cron (Fri 5pm) → Fetch commits + issues + PRs → Merge → Claude API → Discord/Slack
```

- Fetches last 7 days of commits, closed issues, and merged PRs
- Sends to Claude Sonnet for narrative summary generation
- Delivers via Discord or Slack webhook
- Supports EN/FR language toggle

## Screenshot

Tested on n8n v1.76+ self-hosted instance:

![workflow](https://via.placeholder.com/800x400?text=n8n+Weekly+Dev+Summary+Workflow)

## License
MIT
