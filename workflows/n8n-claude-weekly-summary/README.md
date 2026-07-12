# n8n + Claude Weekly Dev Summary Workflow

Automated weekly narrative summary of GitHub repo activity, powered by n8n and Claude API.

## Setup (5 steps)

1. **Import the workflow**: In n8n, click *Workflows → Import from File* and select `weekly-dev-summary.json`
2. **Set credentials**: Add your GitHub Personal Access Token and Anthropic API key in *Settings → Credentials*
3. **Configure variables**: Open the `Configuration` node and set your repo, destination, and language
4. **Activate**: Toggle the workflow to *Active* — it runs every Friday at 5 PM
5. **Test**: Click *Execute Workflow* to run manually and verify output

## Required Credentials

- `githubApi` — GitHub Personal Access Token (classic or fine-grained with `repo` scope)
- `anthropicApi` — Anthropic API key from [console.anthropic.com](https://console.anthropic.com)

## Configurable Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `githubRepo` | Target repository (`owner/repo`) | `claude-builders-bounty/claude-builders-bounty` |
| `destinationWebhook` | Discord/Slack webhook URL | *(required)* |
| `language` | Output language (`EN` or `FR`) | `EN` |

## Output Example

> **Weekly Dev Summary — `claude-builders-bounty`**
>
> 📝 **Commits**: 12 commits this week, including refactored auth middleware and added Stripe integration.
>
> ✅ **Closed Issues**: 3 issues resolved — fixed memory leak (#42), updated docs (#43), clarified bounty rules (#44).
>
> 🔀 **Merged PRs**: 5 pull requests merged, notably the new dashboard UI and CI pipeline improvements.

## Delivery

The workflow posts to a Discord or Slack webhook. To use email instead, replace the `HTTP Request` node with an `Email` node and configure SMTP credentials.

## Screenshot

![Successful execution](screenshot.png)

## License

MIT — same as parent repo.