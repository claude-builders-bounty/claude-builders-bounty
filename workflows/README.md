# n8n Weekly GitHub Dev Summary Workflow

Automated weekly narrative summary of a GitHub repo's activity using n8n + Claude API.

## Features
- **Trigger**: Weekly cron (Friday 5pm UTC)
- **Fetches**: Commits, closed issues, merged PRs for the past week
- **Generates**: Narrative summary via Claude Sonnet 4
- **Delivers**: Discord webhook OR email (configurable)
- **Configurable**: GitHub repo, destination, language (EN/FR)

## Quick Setup (5 Steps)

1. **Import workflow**: In n8n, go to Workflows → Import → select `n8n-weekly-summary.json`
2. **Add credentials**:
   - GitHub API (Personal Access Token with `repo` scope)
   - Anthropic API (Claude API key)
   - Email SMTP (if using email delivery)
3. **Configure variables** (in workflow Settings → Workflow Variables):
   - `github_repo`: `owner/repo` (e.g., `claude-builders-bounty/claude-builders-bounty`)
   - `discord_webhook_url`: Discord webhook URL (optional)
   - `email_to`: Recipient email (optional)
   - `email_from`: Sender email (optional)
   - `language`: `EN` or `FR` (default: `EN`)
4. **Activate workflow**: Toggle "Active" in top-right
5. **Test run**: Click "Execute Workflow" to verify

## Delivery Options
- **Discord only**: Set `discord_webhook_url`, leave email fields empty
- **Email only**: Set `email_to` + `email_from`, leave Discord empty
- **Both**: Configure both

## Requirements
- n8n instance (self-hosted or cloud)
- GitHub Personal Access Token (classic, `repo` scope)
- Anthropic API key (Claude Sonnet 4 access)
- SMTP credentials (if using email)

## Testing
After import, run manually once. Check execution log for:
- ✅ GitHub API calls return data
- ✅ Claude API returns summary
- ✅ Discord/email delivery succeeds

## File Structure
```
workflows/
└── n8n-weekly-summary.json    # Importable n8n workflow
```

## License
MIT