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

## Included Builder Skills

### Generate a changelog from git history

This repository includes a small Claude Code skill and bash utility for generating structured release notes from commit history:

```bash
scripts/generate-changelog.sh
```

By default it writes `CHANGELOG.md` from the latest git tag to `HEAD`. If the repository has no tags, it uses all history. You can also choose the starting point or output path:

```bash
scripts/generate-changelog.sh --since v1.2.0 --output RELEASE_NOTES.md
```

The generated changelog groups conventional commits into `Added`, `Fixed`, `Changed`, `Removed`, and other changes. GitHub remotes are detected automatically so commit hashes and tag comparisons are linked in Markdown output.

The Claude Code skill lives at [`skills/generate-changelog/SKILL.md`](skills/generate-changelog/SKILL.md).

---

*Started by the Claude builder community · March 2026 · MIT License*
