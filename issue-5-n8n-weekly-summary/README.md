# Weekly GitHub Development Summary — n8n + Claude + Discord

An importable n8n workflow for bounty #5. It runs every Friday at 17:00 UTC, reads the previous seven days of public GitHub activity, asks the Claude Messages API for a narrative engineering summary, and delivers the result to a Discord webhook.

## Setup — 5 steps

1. Import `workflow.json` into a self-hosted n8n instance.
2. Configure the repository (`GITHUB_OWNER`, `GITHUB_REPO`), language (`SUMMARY_LANGUAGE` = `EN` or `FR`), the Anthropic API credential, and the Discord webhook URL.
3. Keep the bounty-requested Claude model `claude-sonnet-4-20250514`, or explicitly select a current compatible Sonnet model if the original model is retired for your Anthropic account.
4. Run **Manual Acceptance Trigger** once and verify that all nodes finish successfully and the summary arrives at Discord.
5. Activate the workflow; **Friday 17:00** then runs it weekly at 17:00 UTC.

## Workflow

`Manual Acceptance Trigger / Friday 17:00` → `Configuration` → `Build 7 Day Window` → `GitHub Commits` → `GitHub Closed Issues` → `GitHub Closed Pulls` → `Build Claude Request` → `Claude API` → `Format Discord Delivery` → `Discord Webhook`

The GitHub requests are read-only. Closed issues are filtered so pull requests are not double-counted, and closed PRs are retained only when `merged_at` falls inside the seven-day window. Claude is instructed to use only supplied activity data and not invent details.

## Configuration

The exported workflow reads its configuration from environment variables so no secret value is committed to GitHub. Repository, language, Claude model/endpoint, and Discord destination are configurable. Self-hosted n8n installations that block environment access inside workflow expressions must explicitly allow those expressions before running this workflow.

The production Claude endpoint defaults to `https://api.anthropic.com/v1/messages`. The API credential and Discord webhook must be supplied by the operator before any live external run.

## Real n8n verification

Validation was performed on a real local **n8n 2.32.6** Docker instance (`n8nio/n8n:2.32.6`, image digest `sha256:5f7856f4fc7cd935230f7596e39fdb3d5eda0e379c5b40b699b9c0eb35ebd0bf`).

- n8n CLI import of the final workflow: **PASS** — `Successfully imported 1 workflow.`
- Final real CLI execution #3: **success**, mode `cli`, workflow `avs-opire-bounty-5`.
- Execution #3: `2026-10-08 18:32:18.713` → `2026-10-08 18:32:24.869` UTC.
- Every executed node ran exactly once and reported `success` (execution indexes 0 through 9).
- Public GitHub verification target: `pallets/flask`.
- Activity observed in the execution window: **5 commits, 0 closed issues, 10 merged pull requests**.
- Claude-shaped verification request: one message, model `claude-sonnet-4-20250514`.
- Discord-shaped verification delivery: one `content` payload.
- Final workflow SHA-256: `CF85F970F090AE57189FC0F3E6A6FE0E48F824FFC41E13E4A45FC2D8B7BAB777`.
- Evidence screenshot: `evidence/n8n-execution-success.png`.

### Verification boundary

The n8n engine and GitHub API calls were real. This machine does not have a live Anthropic credential or Discord destination configured, so the acceptance run routed only the **Claude transport** and **Discord transport** to local deterministic HTTP endpoints. Those endpoints recorded request hashes and returned deterministic responses, allowing the complete n8n graph to execute on a real n8n instance without claiming a live Anthropic call or live Discord delivery.

The exported workflow still points to the real Anthropic Messages API by default and requires operator-supplied external credentials before production use. No external credential, paid API call, or secret value is included in this submission.

## Model compatibility note

The bounty text names `claude-sonnet-4-20250514`. The export keeps that exact model as its default so the requested contract is explicit. If Anthropic has retired that model for your account, select the current compatible Sonnet model before a live run; the rest of the workflow is unchanged.
