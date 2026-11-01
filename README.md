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

## Changelog generator (bounty #1)

Automatically generate a structured changelog from Git commits since the latest reachable tag. Requires Git, Bash, and Python 3.8+; no third-party Python packages.

### Setup (3 steps)

1. Copy `changelog.py` and `changelog.sh` to the root of your Git repository.
2. From that repository, run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md` before committing it.

Use `bash changelog.sh --force` to replace an existing changelog or `bash changelog.sh --output docs/CHANGELOG.md` to write to an existing directory. If no reachable tag exists, all commits are included. Unrecognized commit subjects fall under Changed.

Tests: `python3 -m unittest discover -s tests -v`.

Example: [Sample changelog](SAMPLE_CHANGELOG.md), [sample source and limitations](SAMPLE_SOURCE.md).
