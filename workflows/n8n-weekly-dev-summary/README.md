# n8n Weekly GitHub Dev Summary with Claude

This workflow generates a weekly narrative summary of a GitHub repository using Claude Sonnet 4 and posts it to Discord.

## Setup in 5 Steps

1. Import `workflow.json` into n8n.
2. Set environment variables: `GITHUB_REPO=owner/repo`, `GITHUB_TOKEN=...`, `ANTHROPIC_API_KEY=...`, `DESTINATION_WEBHOOK_URL=...`, `SUMMARY_LANGUAGE=EN` or `FR`.
3. Open the imported workflow and confirm the `Weekly Friday Trigger` schedule is Friday 17:00.
4. Run the workflow manually once to verify GitHub fetches, Claude response, and Discord delivery.
5. Activate the workflow.

## What It Fetches

- Commits from the last 7 days through `GET /repos/{owner}/{repo}/commits`.
- Closed issues updated during the week through `GET /repos/{owner}/{repo}/issues`.
- Closed pull requests, filtered to PRs merged during the week.

## Claude Request

The Claude node calls:

```text
POST https://api.anthropic.com/v1/messages
model: claude-sonnet-4-20250514
```

The prompt asks for a concise narrative summary focused on momentum, completed work, user-visible impact, and risks. `SUMMARY_LANGUAGE` controls whether the summary is written in English or French.

## Delivery

The final node sends the generated summary to `DESTINATION_WEBHOOK_URL` as a Discord webhook payload.

## Verification

I validated the exported workflow JSON locally with:

```bash
node workflows/n8n-weekly-dev-summary/validate-workflow.mjs
```

Dry-run output is included in `dry-run-output.md`. A real n8n execution still requires the reviewer's own `ANTHROPIC_API_KEY`, GitHub token, and Discord webhook.
