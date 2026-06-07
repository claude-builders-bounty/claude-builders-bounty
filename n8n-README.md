# n8n + Claude AI — Weekly Dev Summary Workflow

Automated weekly engineering summary powered by n8n and Claude AI.

## Overview

This workflow runs every **Friday at 5 PM**, fetches the past week's GitHub activity (commits, merged PRs, closed issues), sends the data to Claude AI for summarization, and emails the report.

## Features

- **Cron-triggered**: Friday 5pm automatic execution
- **Multi-repo support**: Monitor any GitHub repository
- **Claude AI summary**: Contextual, insightful weekly report
- **Email delivery**: Report sent directly to your inbox
- **No-code setup**: Import JSON into n8n, configure credentials

## Installation

### Prerequisites

- [n8n](https://n8n.io/) instance (self-hosted or cloud)
- GitHub Personal Access Token (`repo` scope)
- Anthropic API key (Claude)

### Setup

1. Copy `weekly-dev-summary.json` to your n8n instance
2. Import the workflow (n8n UI → Workflows → Import)
3. Configure credentials:
   - `githubApi`: GitHub PAT (header: `Authorization: Bearer <token>`)
   - `claudeApi`: Anthropic API key (header: `x-api-key: <key>`)
4. Set the repository in the workflow parameters:
   - Default: `owner/repo` — change to your repo(s)
   - Multiple repos: comma-separated (`owner1/repo1,owner2/repo2`)
5. Configure email recipient in the Email node
6. Activate the workflow

## Output Example

```
# Weekly Dev Summary — owner/repo
> 2026-05-30 to 2026-06-06

## Highlights
- Shipped user authentication module (12 commits, 3 PRs)
- Fixed critical SSRF vulnerability in API gateway
- Improved test coverage by 15%

## Commits
- @alice: API rate limiting implementation
- @bob: Database migration scripts
- @carol: Frontend accessibility fixes

## Pull Requests
- #142: Add OAuth2.0 integration (merged)
- #138: Fix memory leak in WebSocket handler (merged)
- #135: Update dependency versions (merged)

## Action Items
- Review pending architecture proposal for caching layer
- Schedule security audit for new authentication endpoints
```

## Customization

- Change cron schedule in the Schedule Trigger node
- Add Slack/Teams notification as alternative delivery
- Filter specific branches or authors
- Add deployment status from CI/CD pipeline
