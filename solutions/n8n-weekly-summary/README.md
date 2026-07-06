# n8n Weekly Dev Summary

An exportable n8n workflow that automatically generates a weekly narrative summary of GitHub repo activity using Claude API.

## Features

- **Weekly cron trigger** (configurable — Friday 5pm by default)
- **Fetches from GitHub API**: merged PRs, closed issues, commits for the week
- **Claude API narrative summary**: concise, technical, highlights key changes
- **Dual delivery**: Slack webhook (primary) + Email (fallback)
- **Configurable variables**: repo, destination, language (EN/FR via prompt)
- **No manual steps** — fully automated once set up

## Installation (5 Steps)

### 1. Import the Workflow
1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Upload `weekly-dev-summary.json`

### 2. Configure Credentials
Set up these credentials in n8n:
- **GitHub API**: Personal Access Token (repo scope)
- **Anthropic API**: API key
- **Slack**: Webhook URL (optional)
- **Email**: SMTP credentials (optional)

### 3. Set Environment Variables
In n8n variables section, configure:
| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | ✅ | GitHub PAT with repo scope |
| `GITHUB_REPO` | ✅ | e.g. `owner/repo-name` |
| `ANTHROPIC_API_KEY` | ✅ | Claude API key |
| `SLACK_CHANNEL` | ❌ | Defaults to `#dev-updates` |
| `EMAIL_TO` | ❌ | Email recipient |

### 4. Activate
Toggle the workflow to **Active**.

### 5. Test
Click **Execute Workflow** to run an immediate test.

## Output Example

```
# Weekly Development Summary
Generated: 2026-07-06
Repository: owner/repo-name

## Merged PRs
- [Fix: user auth cache invalidation](https://github.com/...) by @dev

## Key Changes
- Auth system: cache TTL reduced to 5min
- API rate limiting introduced for /search endpoint
- 3 bug fixes in payment processing pipeline

## Recommendations
- Monitor auth cache hit ratio after TTL change
- Consider adding integration tests for payment fixes
```

## Customization

- **Language**: Change the Claude prompt to include `"Respond in French"` for FR output
- **Delivery**: Add Discord webhook by duplicating the Slack node
- **Time range**: Adjust the cron trigger's schedule
- **Depth**: Increase `per_page` parameters in HTTP request nodes

## Tested On

- n8n v1.70+ (2026)
- Claude Sonnet 4 (claude-sonnet-4-20250514)
- GitHub API v3

## License

MIT
