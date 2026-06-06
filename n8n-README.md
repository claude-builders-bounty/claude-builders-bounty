# Weekly Dev Summary — n8n + Claude AI Workflow

Automatically generates a narrative weekly development summary from GitHub activity using Claude API.

## Setup (3 steps)

```bash
# 1. Import workflow into n8n
#    Open n8n → Import from File → select weekly-dev-summary.json

# 2. Set environment variables in n8n
#    ANTHROPIC_API_KEY = sk-ant-...
#    GITHUB_REPO_OWNER = your-org
#    GITHUB_REPO_NAME = your-repo
#    SLACK_CHANNEL_ID = C0123456789 (optional)

# 3. Activate the workflow
#    Toggle "Active" switch in n8n
```

## What It Does

```
Every Friday 5pm
        ↓
  GitHub API: commits (last 7 days)
  GitHub API: closed issues
  GitHub API: merged PRs
        ↓
  Aggregate raw data
        ↓
  Build Claude prompt
        ↓
  Claude API generates narrative summary
        ↓
  ↓                    ↓
Save to file      Post to Slack
```

## Workflow Nodes

| # | Node | Purpose |
|---|------|---------|
| 1 | Schedule Trigger | Cron: every Friday at 5pm |
| 2 | Set Date Range | Calculate `since`/`until` dates |
| 3 | Fetch Commits | GitHub commits API |
| 4 | Fetch Closed Issues | GitHub issues API |
| 5 | Fetch Merged PRs | GitHub pulls API |
| 6 | Aggregate Data | Merge 3 API responses into one structure |
| 7 | Build Claude Prompt | Format data into system + user prompts |
| 8 | Call Claude API | Send to Anthropic Messages API |
| 9 | Format Final Report | Wrap Claude output in report template |
| 10 | Save to File | Write to `reports/weekly-summary-{date}.md` |
| 11 | Send to Slack | Optional: post to Slack channel |

## Example Report

```markdown
# 📊 Weekly Dev Summary: myorg/myapp

**Period**: 2026-05-30 → 2026-06-06

### Weekly Summary
This week the team focused on shipping the authentication overhaul and addressing
several P0 bugs. 38 commits across 12 contributors with 5 PRs merged and 8 issues closed.

### Highlights
- JWT-based auth with refresh token rotation went live (#234)
- Fixed critical race condition in checkout flow (#289)
- Database query optimization reduced page load by 40% (#301)

### Commits (38 total)
Auth module dominated with 15 commits, followed by bug fixes (10) and
documentation updates (5). The rest were CI/CD and dependency bumps.

### Closed Issues (8 total)
Primarily auth-related bugs and two performance issues. Pattern: 3 issues
were race conditions — suggests we need better async testing coverage.

### Merged PRs (5 total)
Two feature PRs (auth, rate limiting), two bug fixes, one refactor.
Average review time: 4.2 hours. All PRs had passing CI.

### Next Week Outlook
- Monitor auth rollout for edge cases
- Address remaining rate limiting backlog
- Start planning the notifications module
```

## Customization

- **Change frequency**: Edit the cron expression in node 1
- **Different model**: Change `model` in node 8 (e.g., `claude-opus-4-20250514`)
- **Output to Discord**: Replace node 11 with Discord webhook node
- **Output to Email**: Replace node 11 with Email node

## Bounty

[claude-builders-bounty #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5) — $200
