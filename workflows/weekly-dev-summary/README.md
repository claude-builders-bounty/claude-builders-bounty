# Automated Weekly GitHub Dev Summary (n8n + Claude Code)

> Bounty Solution for Opire / GitHub Issue #5: `WORKFLOW: n8n + Claude Code — automated weekly dev summary` ($200)

An automated n8n workflow that triggers every Friday at 5:00 PM, aggregates GitHub commits and merged pull requests across the past 7 days, calls the Claude API (`claude-sonnet-4-20250514`) to synthesize a narrative newsletter digest, and broadcasts it to Discord or Slack.

## Quickstart (5 Steps or Fewer)

1. **Import Workflow**: In your n8n dashboard, click **Add Workflow** -> **Import from File**, and select [`workflow.json`](workflow.json).
2. **Set Environment Variable**: In your n8n environment or credentials, configure `ANTHROPIC_API_KEY`.
3. **Configure Target Repo**: In the `Configuration Variables` node, set:
   - `GITHUB_OWNER` (e.g. `facebook`)
   - `GITHUB_REPO` (e.g. `react`)
   - `SUMMARY_LANGUAGE` (`EN` or `FR`)
   - `WEBHOOK_URL` (your Discord or Slack Incoming Webhook URL)
4. **Test**: Click **Test Step** or **Execute Workflow** to run a live test run.
5. **Activate**: Toggle the workflow switch to **Active** to run on schedule every Friday at 5:00 PM (`0 17 * * 5`).

## Workflow Architecture

```
[Cron: Fri 5PM] ──> [Config Vars] ──┬──> [Fetch Commits (7d)] ──┐
                                    └──> [Fetch Merged PRs]  ───┴──> [Code: Aggregate] ──> [Claude Sonnet 4 API] ──> [Webhook Delivery]
```

## Output Format
The resulting summary is formatted in clean markdown for Discord/Slack:
- 🚀 **Executive Highlight**: 2-sentence high-level impact overview.
- 📦 **Key Features & Enhancements**: Categorized merged PRs.
- 🐛 **Bug Fixes & Refactors**: Closed issues and critical bug fixes.
- 👏 **Contributor Shoutouts**: Recognition for community and team contributors.
