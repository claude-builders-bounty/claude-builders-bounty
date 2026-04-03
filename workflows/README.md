# n8n + Claude API — Weekly Dev Summary

> Automated workflow that collects weekly git activity and generates a narrative dev summary using Claude API.

## Setup (5 steps)

```bash
# 1. Import the workflow into n8n
n8n import:workflow --input=workflows/weekly-dev-summary.json

# 2. Set required environment variables
export GITHUB_REPO="owner/repo"
export ANTHROPIC_API_KEY="sk-ant-..."
export SUMMARY_LANGUAGE="EN"  # or "FR" for French

# 3. Configure GitHub API credentials in n8n
#    Go to Settings > Credentials > Add > GitHub API

# 4. Choose your delivery channel (set one):
export DISCORD_WEBHOOK_ID="your_id"
export DISCORD_WEBHOOK_TOKEN="your_token"
# OR
export SLACK_WEBHOOK="services/T000/B000/xxx"

# 5. Activate the workflow in n8n and test with "Execute Workflow"
```

## What It Does

Every **Friday at 5pm**, the workflow:

1. **Fetches** commits, merged PRs, and closed issues from the past 7 days
2. **Aggregates** data: commits by author, PR titles, closed issues, top contributors
3. **Sends to Claude API** (`claude-sonnet-4-20250514`) for a structured narrative summary
4. **Delivers** via Discord webhook and/or Slack webhook

## Configurable Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_REPO` | ✅ | GitHub repo in `owner/repo` format |
| `ANTHROPIC_API_KEY` | ✅ | Claude API key |
| `SUMMARY_LANGUAGE` | ❌ | `EN` (default) or `FR` for French output |
| `DISCORD_WEBHOOK_ID` | ❌ | Discord webhook ID |
| `DISCORD_WEBHOOK_TOKEN` | ❌ | Discord webhook token |
| `SLACK_WEBHOOK` | ❌ | Slack webhook path |

## Output Format

```markdown
# Weekly Dev Summary - 2026-04-03

## Stats
- Total commits: 47
- Merged PRs: 12
- Closed issues: 8
- Active contributors: 5

## Top Contributors
1. Alice — 18 commits
2. Bob — 14 commits

## Merged Pull Requests
- #142: Add user authentication
- #139: Fix payment gateway timeout

## Closed Issues
- #135: Login fails on mobile
- #130: Dashboard loading slow

## Key Changes
- Authentication: New JWT-based auth system
- Performance: Redis caching for API endpoints

## Focus for Next Week
- Complete migration to TypeScript
- Load testing for new auth system
```

## Requirements

- **n8n** (self-hosted or cloud)
- **GitHub API** credentials (for commit/PR/issue data)
- **Anthropic API key** (for Claude)
- **Discord or Slack webhook** (for delivery)

## License

MIT
