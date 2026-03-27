# Test Notes

This workflow has been validated structurally against the issue requirements:
- Exportable importable JSON workflow exists
- Weekly cron trigger exists (Friday 5pm)
- GitHub API nodes fetch commits, closed issues, and closed PRs
- Claude API call uses `claude-sonnet-4-20250514`
- Delivery supports Discord webhook or email
- Variables exist for repo, destination mode, and language

Manual n8n execution + screenshot still requires a live n8n instance and secrets.
