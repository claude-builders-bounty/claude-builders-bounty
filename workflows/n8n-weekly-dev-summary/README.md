# n8n Weekly GitHub Dev Summary with Claude

This directory contains an importable n8n workflow that posts a weekly narrative development summary for a GitHub repository to Discord, generated with `claude-sonnet-4-20250514`.

## What it does

Every Friday at 5pm, the workflow:

1. Reads configurable variables for the GitHub repository, API keys, destination webhook, and language.
2. Fetches the last 7 days of GitHub activity:
   - commits
   - closed issues
   - merged pull requests
3. Sends the activity JSON to Claude using the Anthropic Messages API.
4. Formats the generated summary for Discord.
5. Posts it to the configured Discord webhook.

## Files

- `weekly-dev-summary.json` — importable n8n workflow export
- `README.md` — setup and testing notes

## Setup in 5 steps

1. Import `weekly-dev-summary.json` into n8n.
2. Set these environment variables on the n8n host:
   - `GITHUB_REPO`, for example `owner/repo`
   - `GITHUB_TOKEN`, optional for public repos but recommended for rate limits
   - `ANTHROPIC_API_KEY`
   - `DISCORD_WEBHOOK_URL`
   - `SUMMARY_LANGUAGE`, either `EN` or `FR`
3. Open the workflow and verify the `Config` node resolves the variables correctly.
4. Click `Execute workflow` once manually to test the full path.
5. Activate the workflow so the Friday 5pm schedule runs automatically.

## Configuration

| Variable | Required | Example | Purpose |
|---|---:|---|---|
| `GITHUB_REPO` | Yes | `n8n-io/n8n` | Repository to summarize in `owner/repo` format |
| `GITHUB_TOKEN` | No | `ghp_...` | Raises GitHub rate limits and enables private repo access |
| `ANTHROPIC_API_KEY` | Yes | `sk-ant-...` | Calls Claude Messages API |
| `DISCORD_WEBHOOK_URL` | Yes | `https://discord.com/api/webhooks/...` | Destination channel |
| `SUMMARY_LANGUAGE` | No | `EN` or `FR` | Output language; defaults to English |

## n8n node overview

1. `Weekly Friday 5pm Trigger` — weekly schedule trigger.
2. `Config` — central place for all user-editable variables.
3. `Fetch GitHub Activity` — calls GitHub REST API with `fetch` from an n8n Code node.
4. `Generate Summary with Claude` — HTTP Request node calling `https://api.anthropic.com/v1/messages` with model `claude-sonnet-4-20250514`.
5. `Format Discord Message` — extracts Claude text and prepares a Discord payload.
6. `Send to Discord` — posts to the Discord webhook.

## Claude prompt behavior

The prompt asks Claude to produce:

- executive summary
- what shipped
- bugs and maintenance
- contributors
- risks or follow-ups

It also tells Claude not to invent releases, metrics, or roadmap items that are not present in the GitHub activity JSON.

## Testing notes

Validation performed for this PR:

- Confirmed `weekly-dev-summary.json` is valid JSON.
- Confirmed the workflow contains an importable n8n node graph with a weekly schedule trigger.
- Confirmed it includes GitHub activity collection for commits, closed issues, and merged PRs.
- Confirmed it calls the Anthropic Messages API with `claude-sonnet-4-20250514`.
- Confirmed it supports configurable repository, destination channel, and output language.

Manual n8n smoke test checklist:

1. Import the JSON file.
2. Set `GITHUB_REPO=n8n-io/n8n` or another active public repo.
3. Set `SUMMARY_LANGUAGE=EN`, then run once and confirm a Discord message is posted.
4. Change `SUMMARY_LANGUAGE=FR`, run again, and confirm the generated summary is in French.
5. Capture the successful execution screen from n8n if the maintainer requires visual proof.

## Why Discord instead of email

Discord webhooks require no SMTP account setup and are easy to test in a new n8n instance. This keeps the workflow portable and makes the destination channel configurable with a single URL.
