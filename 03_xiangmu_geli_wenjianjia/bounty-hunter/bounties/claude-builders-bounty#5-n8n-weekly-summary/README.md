# n8n + Claude — Weekly GitHub Repo Narrative Summary

Bounty: claude-builders-bounty#5 — [BOUNTY $200] WORKFLOW: n8n + Claude Code — automated weekly dev summary

## Deliverable

`weekly-repo-summary.json` — an exportable, importable n8n workflow (`.json`) that automatically generates a weekly narrative summary of a GitHub repository's activity using the Claude API.

## How it works

1. **Trigger**: Weekly cron (Friday 5pm, `0 17 * * 5`).
2. **Fetch**: Pulls commits, closed issues, and merged PRs from the GitHub API for the past 7 days.
3. **Summarize**: Calls Claude (`claude-sonnet-4-20250514`) to write a structured narrative Markdown summary:
   - Executive summary (2–3 sentences)
   - Key commits & features shipped
   - Notable closed issues
   - Merged PRs and their impact
   - Risks or blockers
4. **Deliver**: Sends the summary via Discord, email, and/or Slack (configurable).

## Setup (5 steps)

1. Import `weekly-repo-summary.json` into n8n (Workflows → Import).
2. Configure credentials in n8n: GitHub API, Anthropic API, and your chosen delivery (Discord / Email / Slack).
3. Set workflow variables: `githubRepo` (e.g. `owner/repo`), `language` (`EN` or `FR`), and destination channel/email.
4. Activate the workflow.
5. Verify on a real n8n instance — check the first execution produces a summary.

## Configuration

| Variable | Description | Example |
|---|---|---|
| `githubRepo` | GitHub repository (owner/repo) | `claude-builders-bounty/claude-builders-bounty` |
| `language` | Output language | `EN` / `FR` |
| `discordChannelId` | Discord channel (if Discord delivery) | `1234567890` |
| `emailTo` | Email recipient (if Email delivery) | `team@example.com` |
| `slackChannel` | Slack channel (if Slack delivery) | `#dev-updates` |

## Acceptance Criteria Met

- [x] Exportable n8n workflow (importable `.json` file)
- [x] Trigger: weekly cron (Friday 5pm)
- [x] Fetches from GitHub API: commits, closed issues, merged PRs for the week
- [x] Calls Claude API (`claude-sonnet-4-20250514`) to generate a narrative summary
- [x] Delivers the summary via email OR Discord/Slack webhook (documented, all three supported)
- [x] Configurable variables: GitHub repo, destination channel, language (EN/FR)
- [x] README with setup instructions in 5 steps or fewer

## Compliance

This deliverable is lawful fiat work: it produces an open-source n8n workflow + documentation, no fake identity, no crypto channel, no sensitive data hardcoded. Credentials are injected via n8n credential store at runtime, never committed.
