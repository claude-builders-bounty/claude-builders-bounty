# Submission-ready checklist

Public bounty: https://github.com/zhangjiayang6835-cyber/bounty-plaza/issues/484

The issue is open, has no assignee, and lists a $200 reward. Its required deliverables are the workflow JSON, a README, and a screenshot of a successful real n8n execution.

## Before submission

1. Import `github-weekly-summary.json` into a real n8n instance.
2. Set a test repository, Claude API credential, GitHub token, and Slack/Discord webhook in the instance.
3. Run the workflow once and save a screenshot showing a successful execution and delivered summary.
4. Replace any credential values in the exported JSON with credential references or placeholders.
5. Authenticate GitHub, comment `/opire try` on issue #484, then open a PR containing this directory.

## What is already included

- Weekly cron trigger.
- GitHub commits, closed issues, and merged pull requests collected for the last seven days.
- Claude `claude-sonnet-4-20250514` narrative generation.
- Slack/Discord-compatible webhook delivery.
- Configurable repository, language, and destination values.
- Setup instructions and an explicit acceptance checklist.

## Important limitation

The screenshot, bounty claim, PR, and payout cannot be completed from this workspace without a contributor's authenticated GitHub/Opire account and API credentials. Do not publish secrets in the PR.
