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

## Generate a changelog

1. Copy `changelog.sh` into a Git working tree with its history and tags. The script uses Bash, Git and Python 3.8 or later.
2. In that working tree, run `bash changelog.sh --stdout` to preview the Markdown.
3. Run `bash changelog.sh` to write `CHANGELOG.md` at the repository root.

The script reads non-merge commits since the nearest reachable tag. With no tag, it reads the whole history. Commit types and leading verbs determine the section. Other subjects go under Changed. Review the wording before publishing.

The generator replaces only the region between its two HTML comments. If a changelog already exists, paste the preview's marked block where the Unreleased section belongs. Keep published releases outside that block. See the [sample from Click](examples/click-changelog.md), generated at [6e1f6d3](https://github.com/pallets/click/commit/6e1f6d3052b6459fa3e43392d728376c423a7d4c) after tag `8.1.6`.

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
