# Claude Weekly Dev Summary — n8n Workflow ($200 Bounty #5)

Importable n8n workflow that posts a weekly narrative summary of any GitHub repo.

## Setup (5 steps)

1. **Import** `workflow.json` in n8n (Workflows → Import from File).
2. **Credentials** — create two credentials in n8n:
   - `githubApi` (GitHub Personal Access Token, `repo` scope)
   - `anthropicApi` (Anthropic API key, set base to `https://api.anthropic.com`)
3. **Configure** the `Set Config` node: `githubRepo` (e.g. `owner/repo`), `language` (`EN` or `FR`), `webhookUrl` (Discord/Slack webhook — or leave empty to use Email node instead).
4. **Schedule** is pre-set to **Friday 5pm** cron `0 17 * * 5` — adjust in the Schedule Trigger if needed.
5. **Activate** the workflow and run once manually to verify. Screenshot the execution for the PR.

## What it does

- Fetches commits, closed issues, and merged PRs for the last 7 days via GitHub API
- Aggregates the three feeds
- Calls `claude-sonnet-4-20250514` to generate a concise narrative summary (progress, highlights, next steps)
- Delivers via Discord/Slack webhook (replace with Email node if you prefer email)

## Variables

- `githubRepo` — `owner/repo`
- `language` — `EN` | `FR`
- `webhookUrl` — Discord or Slack incoming webhook URL

## Test

Run on `myn8n-automation.org` (n8n 1.77.1) or local n8n. Capture a successful execution screenshot showing the Claude summary delivered to the webhook.

## Claim

Comment `/opire try` on issue #5, then open a PR with `workflow.json` + this README. Payout is automatic on merge.
