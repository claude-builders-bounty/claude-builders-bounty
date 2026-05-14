# Weekly GitHub Dev Summary with Claude

This directory contains an importable n8n workflow for bounty issue #5.

The workflow runs every Friday at 5pm, collects the previous seven days of GitHub commits, closed issues, and merged pull requests, asks Claude `claude-sonnet-4-20250514` for a narrative weekly summary, and sends the result by email or webhook.

## Files

- `workflow.json` - importable n8n workflow export.
- `README.md` - setup and validation notes.

## Setup In 5 Steps

1. Import `workflow.json` into n8n.
2. Create an HTTP Header Auth credential named `GitHub Token Header` with header `Authorization: Bearer <GITHUB_TOKEN>`.
3. Create an HTTP Header Auth credential named `Anthropic API Key Header` with header `x-api-key: <ANTHROPIC_API_KEY>`.
4. Set environment variables: `GITHUB_OWNER`, `GITHUB_REPO`, `DESTINATION_MODE`, `DESTINATION_URL`, `SUMMARY_LANGUAGE`, and, for email mode, `SUMMARY_FROM_EMAIL`.
5. Configure either SMTP credentials for email mode or set `DESTINATION_MODE=webhook` with a Slack/Discord-compatible webhook URL, then run a manual test before activating the weekly schedule.

## Configuration

| Variable | Required | Example | Notes |
| --- | --- | --- | --- |
| `GITHUB_OWNER` | Yes | `octocat` | Repository owner or organization. |
| `GITHUB_REPO` | Yes | `hello-world` | Repository name only. |
| `DESTINATION_MODE` | Yes | `email` or `webhook` | Defaults to `email` if unset. |
| `DESTINATION_URL` | Yes | `team@example.com` or webhook URL | Email recipient or webhook endpoint. |
| `SUMMARY_LANGUAGE` | Yes | `EN` or `FR` | Prompt language selector. |
| `SUMMARY_FROM_EMAIL` | Email only | `bot@example.com` | Used by the SMTP node. |

## Acceptance Coverage

| Bounty criterion | Coverage |
| --- | --- |
| Exportable n8n workflow JSON | `workflow.json` included. |
| Weekly cron | Schedule node configured for Friday 5pm. |
| GitHub commits | GitHub commits endpoint included. |
| Closed issues | GitHub search query for closed issues included. |
| Merged PRs | GitHub search query for merged pull requests included. |
| Claude summarization | Anthropic Messages API call uses `claude-sonnet-4-20250514`. |
| Email or webhook delivery | Email and webhook branches included. |
| Repo, destination, language variables | Environment variables documented and used. |
| README setup <= 5 steps | Setup section has five steps. |

## Local Validation

The workflow export is valid JSON:

```bash
jq empty workflows/n8n-weekly-github-dev-summary/workflow.json
```

Run the bundled structural validator to check the main bounty criteria without
calling any paid APIs:

```bash
node workflows/n8n-weekly-github-dev-summary/validate-workflow.mjs
```

End-to-end execution still requires reviewer-provided GitHub, Anthropic, and delivery credentials in n8n.
