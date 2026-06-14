## 🤖 Claude Review: [BOUNTY $200] WORKFLOW: n8n + Claude API — automated weekly dev summary

### Summary
This PR adds a complete n8n workflow (`workflows/n8n-weekly-summary/`) that generates a narrative weekly summary of GitHub repo activity using the Claude API. The workflow is triggered by a weekly cron schedule, fetches commits/closed issues/merged PRs via GitHub API, calls Claude Sonnet 4, and delivers the summary to a Discord webhook. A README with 5-step setup instructions is included.

### Identified Risks
- **risk: GitHub API secondary rate limits** — The workflow makes 3 parallel API calls to GitHub. For repos with high activity (>5000 requests/hour), unauthenticated requests will hit secondary rate limits. The README should explicitly mention creating a GitHub PAT with `repo` scope and setting it in n8n credentials to get 5000 req/hr instead of 60 req/hr.
- **risk: Claude API token limits** — The workflow uses `max_tokens: 2048`. For repos with very high weekly activity (100+ commits), the input context size could approach Claude's limit. Consider truncating the input data more aggressively or adding a token-counting step.
- **risk: Discord webhook message length** — Discord webhooks have a 2000 character limit per message for regular bots. If the weekly summary is very long, the delivery will silently fail. Consider splitting long messages or using Discord's thread-based output.

### Improvement Suggestions
- **suggestion: Add error notification** — If any of the GitHub API calls fail (repo not found, rate limited, network error), the workflow proceeds with partial data and no notification to the user. Adding an "On Error" path that sends an alert would improve reliability.
- **suggestion: Make "weeks" configurable per execution** — The `weeks` parameter is currently hardcoded in the Configure Repo node. Exposing it in the workflow's "Execute Workflow" dialog would let users run ad-hoc reports for different time ranges.
- **suggestion: Support Slack webhook natively** — The current implementation targets Discord. Since many teams use Slack, adding an optional output format (detected from the webhook URL) would make it more versatile.

### Confidence Score
**High** — The workflow architecture is well-designed with parallel data fetching, proper prompt engineering, and clean output formatting. The acceptance criteria are fully met.
