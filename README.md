# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate?
Want to get paid for contributing to AI projects?
You're in the right place.

## How it works

**To post a bounty**
1. Open a GitHub issue with a clear description and acceptance criteria
2. Comment `/opire create $XXX` in the issue to set the reward
3. Share the link — contributors will find it

**To claim a bounty**
1. Browse the open issues below
2. Comment `/opire try` in the issue you want to work on
3. Submit a PR — payment is automatic on merge ✅

## Active Bounties

| # | Task | Amount | Status |
|---|------|--------|--------|
| [#1](../../issues/1) | SKILL: Generate a CHANGELOG from git history | $50 | 🟢 Open |
| [#2](../../issues/2) | TEMPLATE: CLAUDE.md for a Next.js + SQLite project | $75 | 🟢 Open |
| [#3](../../issues/3) | HOOK: Block destructive bash commands in Claude Code | $100 | 🟢 Open |
| [#4](../../issues/4) | AGENT: PR reviewer with structured Markdown output | $150 | 🟢 Open |
| [#5](../../issues/5) | WORKFLOW: n8n + Claude API — automated weekly dev summary | $200 | 🟢 Open |

## Bounty #5: weekly GitHub narrative summary

`weekly-github-summary.json` is an importable n8n workflow. It runs every
Friday at 17:00, fetches the last seven days of commits, closed issues, and
merged pull requests, asks `claude-sonnet-4-20250514` for a factual narrative,
and posts it to a configurable Discord webhook.

### Setup (5 steps)

1. Import `weekly-github-summary.json` into n8n.
2. Set `GITHUB_REPO`, `GITHUB_TOKEN`, and `ANTHROPIC_API_KEY` in n8n.
3. Set `LANGUAGE` to `EN` or `FR`, plus `DISCORD_WEBHOOK_URL`.
4. Activate the workflow; the Cron node runs at 17:00 every Friday.
5. Execute it manually once and confirm the Discord message.

`python3 workflow_smoke_test.py` validates the export locally. A live n8n
execution requires the operator's own credentials; no credentials are stored
in this repository.

## Rules

- Tasks must be related to Claude Code or AI tooling
- Every issue must have clear acceptance criteria before a bounty is activated
- Payment is handled by [Opire](https://opire.dev) (Stripe)
- Quality over speed — a solid PR beats a fast one

## Community

- 🐦 X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- 📧 Contact: claudebounty@gmail.com

---

*Started by the Claude builder community · March 2026 · MIT License*
