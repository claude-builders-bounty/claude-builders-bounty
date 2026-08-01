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

## n8n Weekly Dev Summary Workflow

This PR includes an importable n8n workflow for bounty [#5](../../issues/5).

Import `workflows/n8n-weekly-dev-summary.json` into n8n, then configure:

- `GITHUB_REPO`
- `GITHUB_TOKEN`
- `ANTHROPIC_API_KEY`
- `SUMMARY_EMAIL_TO`
- `SUMMARY_LANGUAGE`

The workflow runs every Friday at 5pm, fetches the last seven days of commits,
closed issues, and merged pull requests, asks `claude-sonnet-4-20250514` for a
weekly development summary, then sends it by email.

Validate the workflow shape and Code node syntax:

```bash
python3 scripts/validate_n8n_workflow.py
```

Run a live GitHub API dry run without calling Claude or sending email:

```bash
python3 scripts/validate_n8n_workflow.py --live-repo n8n-io/n8n
```

Detailed setup notes live in `workflows/README.md`; sample generated output is
included at `samples/weekly-dev-summary-output.md`.

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
