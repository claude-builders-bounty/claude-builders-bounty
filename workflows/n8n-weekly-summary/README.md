# n8n Weekly Dev Summary

Auto-generates a weekly narrative summary of GitHub repo activity using Claude API.

## Setup

1. **Import workflow**: n8n → Workflows → Import → Select `n8n-workflow.json`
2. **Set env variables**: `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `GITHUB_REPO` (owner/repo), `DISCORD_WEBHOOK_URL`
3. **Activate**: Toggle the workflow to "Active" in n8n
4. **Test**: Click "Execute Workflow" to verify

## Config

| Variable | Required | Default | Description |
|---|---|---|---|
| `GITHUB_TOKEN` | Yes | — | GitHub PAT with repo scope |
| `ANTHROPIC_API_KEY` | Yes | — | Claude API key |
| `GITHUB_REPO` | Yes | `owner/repo` | Target repository |
| `DISCORD_WEBHOOK_URL` | Yes | — | Discord webhook for output |
| `LANGUAGE` | No | `EN` | `EN` or `FR` |

## Output

Delivered to Discord every Friday at 5PM with:
- Overview paragraph (commits, issues, PRs)
- Highlights
- Technical details
- Next steps
