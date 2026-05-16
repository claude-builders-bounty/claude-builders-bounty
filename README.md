# Weekly Dev Summary — n8n + Claude Code

**Bounty:** [#5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5) ($200)

An n8n workflow that generates a narrative weekly dev summary using Claude API.

## Nodes
| Node | Type | Purpose |
|------|------|---------|
| Weekly Cron | ScheduleTrigger | Runs Friday 5pm |
| Get Commits | GitHub | Fetch repo commits |
| Get Merged PRs | GitHub | Fetch closed/merged PRs |
| Get Closed Issues | GitHub | Fetch closed issues |
| Merge Data | Merge | Combine all sources |
| Build Prompt | Set | Format Claude prompt |
| Claude API | HTTP Request | Generate summary |
| Format Output | Set | Format markdown report |

## Setup
1. Import `weekly-dev-summary.json` into n8n
2. Add GitHub credential (PAT with `repo` scope)
3. Add Anthropic credential (API key)
4. Set workflow variables: `owner`, `repo`, `email`
5. Activate
