# Bounty Fix Task

## Issue
**Title:** [BOUNTY $200] WORKFLOW: n8n + Claude Code — automated weekly dev summary
**URL:** https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5
**Reward:** $200.00

## Description
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
- n8n docs: https://docs.n8n.io
- Claude API docs: https://docs.anthropic.com

## Instructions
1. Read the issue carefully and understand exactly what needs to be fixed.
2. Find the relevant files using grep/glob tools.
3. Implement the minimal correct fix — do not refactor unrelated code.
4. Run any existing tests to verify correctness: look for test scripts in package.json, Makefile, or similar.
5. If tests fail, fix them or update them if the behavior change is intentional.
6. Commit all changes with message: "fix: [BOUNTY $200] WORKFLOW: n8n + Claude Code — automated weekly dev summary"
7. Do NOT create the PR — the agent script handles that.
8. When done, write a one-paragraph summary of what you changed to AGENT_SUMMARY.md.

## Important
- Stay focused on the specific issue, nothing else.
- If the fix is unclear or requires significant architectural decisions, write your uncertainty to AGENT_SUMMARY.md and stop.
- Do not modify unrelated files.
