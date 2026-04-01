# Bounty Fix Analysis

## Issue
- **URL:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5
- **Title:** [BOUNTY $200] WORKFLOW: n8n + Claude Code — automated weekly dev summary
- **Bounty:** $200
- **Labels:** bounty, workflow

## Tech Stack


## Issue Body
## 💰 Bounty: $200 — powered by [Opire](https://opire.dev)

## Description
Create a complete n8n workflow that automatically generates a weekly narrative
summary of a GitHub repo's activity, using the Claude API.

## Acceptance Criteria
- [ ] Exportable n8n workflow (importable `.json` file)
- [ ] Trigger: weekly cron (e.g., Friday at 5pm)
- [ ] Fetches from GitHub API: commits, closed issues, merged PRs for the week
- [ ] Calls Claude API (`claude-sonnet-4-20250514`) to generate a narrative summary
- [ ] Delivers the summary via: email OR Discord/Slack webhook (your choice, documented)
- [ ] Configurable variables: GitHub repo, destination channel, language (EN/FR)
- [ ] Tested on a real n8n instance (include a screenshot of successful execution)
- [ ] README with setup instructions in 5 steps or fewer

## How to Claim
1. Comment `/opire try` in this issue
2. Submit a PR with the `.json` workflow + README
3. Payment is released automatically on merge ✅

## Resources
- n8n docs: https:

## Analysis
[AI Agent should analyze the issue and implement the fix here]

## Testing Notes
- [ ] Understand the issue requirements
- [ ] Implement the fix
- [ ] Run existing tests
- [ ] Add tests if needed
- [ ] Verify fix addresses the issue
