# n8n + Claude Code — Weekly Dev Summary

An n8n workflow that generates a weekly narrative summary of GitHub repo activity.

## Setup

1. Import `weekly-dev-summary.json` into n8n
2. Set your GitHub token as `GITHUB_TOKEN` credential
3. Set your Claude API key as `CLAUDE_API_KEY` credential
4. Configure the repository URL in the HTTP Request nodes
5. Set the cron schedule (default: Friday 5pm)

## Output

A structured markdown summary covering:
- Merged PRs
- Closed Issues  
- Key Commits
- Weekly notes/observations
