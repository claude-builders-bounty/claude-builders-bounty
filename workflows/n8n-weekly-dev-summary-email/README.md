# Weekly GitHub Dev Summary - Claude + Email

Importable n8n workflow for bounty #5. It runs every Friday at 5 PM, fetches the last seven days of commits, closed issues, and merged PRs from GitHub, asks `claude-sonnet-4-20250514` for a narrative summary, and sends the result by email through Resend.

## Setup

1. Import `weekly-dev-summary-email.workflow.json` into n8n.
2. Set environment variables: `GITHUB_REPO=owner/repo`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `RESEND_API_KEY`, `DESTINATION_EMAIL`, optional `EMAIL_FROM`, `SUMMARY_LANGUAGE=EN` or `FR`, and `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` if your self-hosted n8n blocks Code node env access.
3. Open the workflow and run `Manual Test Trigger` once to verify GitHub, Claude, and email delivery.
4. Activate the workflow so `Friday 5 PM Weekly Trigger` runs weekly.

## Configuration

| Variable | Required | Description |
| --- | --- | --- |
| `GITHUB_REPO` | Yes | Repository to summarize, in `owner/repo` format. |
| `GITHUB_TOKEN` | Yes | GitHub token used only in GitHub HTTP request headers. It is not returned in workflow item JSON. |
| `ANTHROPIC_API_KEY` | Yes | Claude API key for `claude-sonnet-4-20250514`. |
| `RESEND_API_KEY` | Yes | Resend API key for email delivery. |
| `DESTINATION_EMAIL` | Yes | Email recipient for the weekly summary. |
| `EMAIL_FROM` | No | Sender, defaulting to `Weekly Dev Summary <onboarding@resend.dev>`. |
| `SUMMARY_LANGUAGE` | No | `EN` by default; set `FR` for French summaries. |
| `N8N_BLOCK_ENV_ACCESS_IN_NODE` | Sometimes | Set to `false` on self-hosted n8n if Code nodes cannot read `$env`. |

Resend test-mode accounts can send only to the account owner's verified email. For arbitrary recipients, verify a sending domain in Resend and set `EMAIL_FROM` to that domain.

## Test Evidence

Successful isolated n8n execution is shown in `successful-execution.jpg`.
