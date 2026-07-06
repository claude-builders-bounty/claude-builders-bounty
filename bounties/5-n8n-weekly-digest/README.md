# Weekly GitHub Digest — n8n + Claude Workflow

Automated weekly summary of GitHub repo activity, powered by n8n and Claude AI.

## Setup (5 steps)

1. **Import workflow** — Open n8n, click "Import from File", select `weekly-digest-workflow.json`

2. **Set credentials** — Add these n8n credentials:
   - `Set repo`: `{ "repo": "owner/repo" }`
   - `Set language`: `{ "language": "EN" }` (or `FR`)
   - HTTP Header Auth for GitHub: `Authorization: Bearer ghp_xxx`
   - HTTP Header Auth for Anthropic: `x-api-key: sk-ant-xxx`

3. **Add Discord webhook** — In the "Send to Discord" node, paste your Discord webhook URL

4. **Add Claude messages body** — In "Call Claude API" node, add body parameter:
   ```json
   {"role": "user", "content": "Generate a weekly summary for repo ..."}
   ```
   (see node config for full prompt template)

5. **Activate** — Toggle "Active" switch. The workflow runs every Friday at 5pm.

## How it works

```
Cron (Fri 5pm) -> Fetch GitHub API (commits/issues/PRs) -> Merge data -> Call Claude -> Discord
```

## Requirements
- n8n instance (self-hosted or cloud)
- GitHub personal access token (repo scope)
- Anthropic API key
- Discord webhook URL

## Variables
| Variable | Description |
|----------|-------------|
| `repo` | GitHub repo in `owner/name` format |
| `language` | `EN` for English, `FR` for French |

## Sample output
```
## Weekly Development Digest — owner/repo
**Week ending:** 2026-07-04

This week saw 12 commits, 5 issues closed, and 3 PRs merged...

### Key Changes
- feat: add dark mode toggle (by @dev1)
- fix: resolve login timeout on mobile

### Issues Resolved
- #42: Button alignment on Safari
- #44: Broken pagination

### Contributors
Special thanks to @dev1, @dev2 for their contributions!
```
