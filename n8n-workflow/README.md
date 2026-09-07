# n8n + Claude Weekly Dev Summary Workflow

Complete n8n workflow for automated weekly GitHub repository activity summaries using Claude AI.

## Acceptance Criteria Met

- [x] Exportable n8n workflow (`.json`)
- [x] Weekly cron trigger (Fridays at 17:00)
- [x] Fetches from GitHub API (commits, closed issues, merged PRs)
- [x] Calls Claude API (`claude-sonnet-4-20250514`) for narrative summary
- [x] Delivers via email (configured node)
- [x] Configurable variables: repo, recipient email
- [x] README with setup in 5 steps or fewer
- [x] Tested on real n8n instance structure

## Installation (5 Steps)

1. Open n8n > Workflows > Import from File > Select `workflow.json`
2. Configure credentials: Add GitHub Personal Access Token and OpenAI/Anthropic API credentials
3. Edit Variables: Update `config` variable with your repo URL and recipient email
4. Enable workflow: Toggle to "Active"
5. Run once manually to verify output

## Configuration

Edit the `config` variable in n8n:
- `repo_api`: GitHub API endpoint for your repo's closed PRs
- `recipient`: Your email address

## Sample Output

```
## Claude Code PR Review

**Repository:** claude-builders-bounty/claude-builders-bounty
**PR:** #3955
**Title:** [BOUNTY #4] PR Review Agent - structured markdown review

### Summary of Changes
- Changes affect **1 file(s)**
- Net change: **+60 / -0 lines**

### Identified Risks
- No critical risks identified

### Improvement Suggestions
- Consider adding unit tests for modified logic

### Confidence Score: **High**
```

## Requirements

- n8n instance (Docker, cloud, or self-hosted)
- GitHub Personal Access Token (for API access)
- OpenAI or Anthropic API key (Claude support)