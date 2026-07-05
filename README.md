 # n8n + Claude — Automated Weekly Dev Summary
 
 A complete n8n workflow that automatically generates a narrative summary of any GitHub repo's weekly activity using the Claude API.
 
 ## Features
 
 - **Weekly cron trigger** — runs every Friday at 5 PM (configurable)
 - **GitHub API integration** — fetches commits, closed issues, and merged PRs
 - **Claude narrative generation** — uses `claude-sonnet-4-20250514` to write engaging summaries
 - **Dual delivery** — sends to Discord webhook AND/OR email
 - **Configurable** — repo, language (EN/FR), destination channel
 
 ## Setup (5 steps)
 
 1. **Import workflow** — Open n8n, go to Workflows → Import from File, select `n8n-workflow.json`
 2. **Configure credentials** — Add your GitHub PAT (Personal Access Token) and Anthropic API key as environment variables
 3. **Set environment variables** — Configure `GITHUB_REPO`, `DISCORD_WEBHOOK_URL`, `EMAIL_TO`, `EMAIL_FROM`, `ANTHROPIC_API_KEY`
 4. **Activate** — Toggle the workflow to "Active" in n8n
 5. **Test** — Click "Execute Workflow" to run a manual test
 
 ## Configuration Variables
 
 | Variable | Default | Description |
 |----------|---------|-------------|
 | `GITHUB_REPO` | `octocat/Hello-World` | Target repository (owner/repo) |
 | `ANTHROPIC_API_KEY` | *(required)* | Claude API key from console.anthropic.com |
 | `LANGUAGE` | `EN` | Output language (EN or FR) |
 | `DISCORD_WEBHOOK_URL` | *(optional)* | Discord webhook URL for delivery |
 | `EMAIL_TO` | *(optional)* | Recipient email address |
 | `EMAIL_FROM` | `n8n@devsummaries.com` | Sender email address |
 | `CRON_EXPRESSION` | `0 17 * * 5` | Weekly schedule (Friday 5 PM) |
 
 ## Workflow Diagram
 
 ```
 Weekly Schedule → Set Date Range → ┬─ Fetch Commits
                                    ├─ Fetch Closed Issues
                                    └─ Fetch Merged PRs
                                           ↓
                                    Combine Data
                                           ↓
                                 Build Claude Prompt
                                           ↓
                                   Claude API Call
                                           ↓
                                  Extract Summary
                                         /    \
                                   Discord   Email
 ```
 
 ## Requirements
 
 - n8n v1.0+ (self-hosted or cloud)
 - GitHub Personal Access Token (with `repo` scope)
 - Anthropic API key
 - (Optional) Discord webhook URL
 - (Optional) SMTP credentials for email delivery
 
 ## Example Output
 
 ```markdown
 # Weekly Dev Summary: octocat/Hello-World
 
 ## Overview
 A productive week with 15 commits, 3 issues closed, and 2 PRs merged.
 
 ## Highlights
 - Major refactor of the authentication module
 - New contributor @janedev joined the project
 
 ## Issues Resolved
 - #42: Fixed login timeout on slow connections
 - #43: Added pagination to user list
 
 ## New Features
 - #89: Refactored database layer for improved performance
 - #90: Added unit tests for API endpoints
 
 ## Community
 - 2 new contributors this week
 - Average PR review time: 4 hours
 ```
 
 ## License
 
 MIT
