# n8n Weekly GitHub Dev Summary with Claude

This workflow creates a weekly narrative summary of a GitHub repository's activity with Claude and posts it to a Discord webhook.

## Setup in 5 steps

1. Import `workflows/n8n-weekly-github-dev-summary.json` into n8n.
2. Set these n8n environment variables: `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `DISCORD_WEBHOOK_URL`, `GITHUB_OWNER`, `GITHUB_REPO`, and optionally `SUMMARY_LANGUAGE` (`EN` or `FR`).
3. Open the `Config` node and confirm the repository, language, and webhook values are correct.
4. Run the workflow manually once to verify it fetches commits, closed issues, merged PRs, generates a Claude summary, and posts to Discord.
5. Activate the workflow; it runs every Friday at 5:00 PM.

## What it does

- Runs weekly via an n8n Schedule Trigger.
- Fetches the last 7 days of GitHub activity:
  - commits from `/repos/{owner}/{repo}/commits`
  - closed issues from GitHub Search API
  - merged pull requests from GitHub Search API
- Calls Anthropic Messages API with `claude-sonnet-4-20250514`.
- Posts the generated summary to Discord.
- Supports configurable repository and output language through environment variables.

## Required variables

| Variable | Purpose |
|---|---|
| `GITHUB_TOKEN` | GitHub API token for the target repository |
| `ANTHROPIC_API_KEY` | Anthropic API key used by Claude |
| `DISCORD_WEBHOOK_URL` | Destination Discord webhook |
| `GITHUB_OWNER` | Repository owner, for example `anthropics` |
| `GITHUB_REPO` | Repository name, for example `claude-code` |
| `SUMMARY_LANGUAGE` | Optional: `EN` or `FR`; defaults to `EN` |

## Testing notes

The workflow is designed to be tested manually in n8n before activation. A successful test should show:

1. GitHub HTTP nodes returning JSON data.
2. The Claude node returning a `content` array with generated text.
3. The Discord node returning a successful webhook response.

Include a screenshot of the successful n8n execution when submitting the PR.

## Delivery choice

This implementation uses Discord webhook delivery because it avoids SMTP setup and is easy to test in n8n.
