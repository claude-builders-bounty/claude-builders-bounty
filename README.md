# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate?
Want to get paid for contributing to AI projects?
You're in the right place.

---

## How it works

**To post a bounty**
1. Open a GitHub issue with a clear description and acceptance criteria
2. Comment `/opire create $XXX` in the issue to set the reward
3. Share the link — contributors will find it

**To claim a bounty**
1. Browse the open issues below
2. Comment `/opire try` in the issue you want to work on
3. Submit a PR — payment is automatic on merge ✅

---

## Active Bounties

| # | Task | Amount | Status |
|---|------|--------|--------|
| [#1](../../issues/1) | SKILL: Generate a CHANGELOG from git history | $50 | 🟢 Open |
| [#2](../../issues/2) | TEMPLATE: CLAUDE.md for a Next.js + SQLite project | $75 | 🟢 Open |
| [#3](../../issues/3) | HOOK: Block destructive bash commands in Claude Code | $100 | 🟢 Open |
| [#4](../../issues/4) | AGENT: PR reviewer with structured Markdown output | $150 | 🟢 Open |
| [#5](../../issues/5) | WORKFLOW: n8n + Claude API — automated weekly dev summary | $200 | 🟢 Open |

---

## Rules

- Tasks must be related to Claude Code or AI tooling
- Every issue must have clear acceptance criteria before a bounty is activated
- Payment is handled by [Opire](https://opire.dev) (Stripe)
- Quality over speed — a solid PR beats a fast one

---

## Community

- 🐦 X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- 📧 Contact: claudebounty@gmail.com

---

*Started by the Claude builder community · March 2026 · MIT License*

---

## Bounty #5 — Weekly GitHub Dev Summary (n8n + Claude)

**Issue:** [#5](../../issues/5) — $200 Opire

Importable n8n workflow (`weekly-github-dev-summary.json`, 10 nodes) that every Friday 17:00 summarizes a repo's weekly activity (commits, closed issues, merged PRs) via Claude (`claude-sonnet-4-20250514`) and delivers to Slack and/or Discord webhook.

Pipeline: `Schedule (Fri 17:00) → Init Context → Fetch Commits + Closed Issues/PRs → Aggregate → Claude API → Route → Slack/Discord`

### Setup (5 steps)

1. Import `weekly-github-dev-summary.json` into n8n (Workflows → Import from File).
2. Set env on the n8n host (at least one webhook required):
   ```ini
   GITHUB_REPO=owner/repo
   GITHUB_TOKEN=ghp_...             # optional, raises rate limit 60→5000/hr
   ANTHROPIC_API_KEY=sk-ant-...     # required for narrative
   SUMMARY_LANG=EN                  # EN or FR, default EN
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...      # or
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...    # or both
   TIMEZONE=UTC                     # cron timezone, default UTC
   ```
3. Save + Activate the workflow.
4. Execute once manually to verify end-to-end.
5. Runs automatically every Friday 17:00.

### Validation without n8n

```bash
python3 dry-run.py --repo owner/repo --since 2026-09-01
python3 dry-run.py --repo owner/repo --since 2026-09-01 --claude --slack
```

`dry-run.py` is stdlib-only and mirrors the n8n nodes (GitHub → aggregate → Claude → deliver).

Meets #5 criteria: exportable `.json`, weekly cron Fri 17:00, GitHub commits/closed issues/merged PRs, Claude `claude-sonnet-4-20250514`, Slack/Discord delivery, configurable repo/channel/language.
