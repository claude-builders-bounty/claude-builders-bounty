## Summary
This PR replaces the existing bounty board README with documentation for an n8n workflow that generates weekly GitHub repository summaries using the Claude API and delivers them via webhook. It adds a complete n8n workflow JSON file (`n8n_weekly_dev_summary.json`) containing nodes for fetching commits, issues, and PRs, summarizing with Claude Sonnet 4, and posting to Discord/Slack.

## Risks
- **Complete removal of bounty board content**: The README entirely deletes the original bounty board (active bounties, rules, community links), which may break existing contributor workflows and lose discoverability of open tasks.
- **Hardcoded credential placeholders**: The workflow JSON contains `REPLACE_WITH_GITHUB_CRED_ID` and `REPLACE_WITH_ANTHROPIC_CRED_ID` strings that will cause runtime failures if imported without manual editing; n8n typically handles this via credential selection UI rather than placeholder IDs.
- **No error handling in workflow**: There are no error branches or retry logic on any node — a single GitHub API rate limit, network timeout, or Claude API failure will silently fail the entire weekly run with no notification.
- **Unbounded data fetching**: `returnAll: true` on all three GitHub nodes with only a 7-day filter could hit API pagination limits or token limits for active repos, potentially truncating data or exceeding Claude's context window.
- **Webhook payload assumes Discord format**: The `jsonBody` uses `{ "content": ... }` which is Discord-specific; Slack expects `{ "text": ... }` or block kit format, so the "Discord/Slack compatible" claim in the README is inaccurate without conditional formatting.
- **Model ID may be stale**: `claude-sonnet-4-20250514` is hardcoded in the workflow JSON; model IDs change over time and this cannot be updated via n8n variables without editing the raw JSON.
- **Payout address in README with no context**: A Solana wallet address is added to the README without explanation of its purpose, which could confuse users or appear unprofessional.

## Suggestions
- Preserve or link to the original bounty board content rather than deleting it entirely, or move this workflow documentation to a separate file (e.g., `WORKFLOWS.md`).
- Add error handling nodes (e.g., n8n Error Trigger) and consider adding a fallback notification when the workflow fails.
- Replace `returnAll: true` with explicit pagination or item limits to prevent unbounded API calls and token overflow.
- Make the webhook payload format configurable (add a `webhookType` variable) or document clearly that users must adjust the JSON body for Slack vs Discord.
- Move the model ID into a workflow variable or environment variable so it can be updated without editing the JSON directly.
- Add input validation or default values for `githubOwner`, `githubRepo`, and `webhookUrl` to prevent silent failures from missing configuration.
- Remove or properly contextualize the Solana payout address — if it's the bounty payout for this task, note that explicitly.
- Consider adding a "Set Variables" node at the start of the workflow to centralize configuration instead of relying on `$json` fields that must be injected externally.

## Confidence
High
