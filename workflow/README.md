# Weekly GitHub Development Summary

An n8n workflow that collects the last 7 days of GitHub development activity, uses Claude to generate a concise weekly summary, and sends the result to Discord.

## What it does

The workflow collects:

- Commits from the previous 7 days
- Closed issues from the previous 7 days
- Pull requests merged during the previous 7 days

It combines the GitHub activity into a structured payload, sends it to Claude for a factual developer-facing summary, and delivers the generated summary to Discord.

Long summaries are automatically split into Discord-safe chunks and sent sequentially.

The workflow supports both manual execution and an automatic weekly schedule.

## Requirements

- n8n
- GitHub API token
- Anthropic API key
- Discord webhook URL

## Setup

1. Import `weekly-github-development-summary.json` into n8n.
2. Create an HTTP Header Auth credential named `GitHub API` and configure your GitHub API token.
3. Open the `Config` node and set `github_owner`, `github_repo`, `language` (`en` or `fr`), and your Discord webhook URL.
4. Open `Claude Weekly Summary` and replace `YOUR_ANTHROPIC_API_KEY` with your Anthropic API key.
5. Run the workflow manually to verify GitHub → Claude → Discord delivery, then activate it for weekly execution.

## Workflow behavior

The included configuration uses `n8n-io/n8n` as the example repository and `fr` as the output language.

The workflow creates a 7-day reporting period and sends Claude the commit count, closed issue count, merged pull request count, and the corresponding activity details.

Claude is instructed to use only the supplied GitHub data, avoid speculation and recommendations, and explicitly state when a category contains no activity.

The generated summary is split into chunks of approximately 1,900 characters when necessary so that long summaries can be delivered safely through Discord.

## Claude model

The workflow currently uses `claude-sonnet-4-6`.

The Claude model originally specified by the bounty is no longer the model used by this implementation, so the workflow uses a currently available Claude Sonnet model instead.

## Testing

The workflow was tested end-to-end on a real n8n instance.

Testing verified:

- GitHub activity retrieval
- Commit, issue, and merged pull request processing
- Claude summary generation
- Long-message splitting
- Sequential Discord webhook delivery

## Security

The submitted workflow contains placeholders for sensitive values.

Never commit a real Anthropic API key, Discord webhook URL, GitHub token, or other secret to the repository.