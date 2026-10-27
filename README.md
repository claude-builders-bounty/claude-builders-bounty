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

## Pre-Tool-Use Hook: Block Destructive Bash Commands (`hooks/`)

A Claude Code `PreToolUse` hook (`hooks/block-destructive-bash.py`) that intercepts dangerous `Bash` commands before execution, logs every blocked attempt to `~/.claude/hooks/blocked.log` (with UTC timestamp, project path, matched rule, and attempted command), and returns a clear explanation to Claude.

### Blocked Patterns
- `rm -rf`, `rm -fr`, `rm -r -f`, `rm --recursive --force`
- `DROP TABLE`, `DROP DATABASE`, `DROP SCHEMA`
- `git push --force`, `git push -f`
- `TRUNCATE TABLE` / SQL `TRUNCATE`
- `DELETE FROM <table>` without a `WHERE` clause (allows qualified `DELETE FROM ... WHERE ...`)
- Fork bombs (`:(){ :|:& };:`), `mkfs`, and raw disk writes (`dd of=/dev/...`)

### Installation (2 Commands)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git && cd claude-builders-bounty
bash hooks/install.sh
```

Or copy the hook directly into `~/.claude/hooks/` and merge `hooks/settings.example.json` into `~/.claude/settings.json`.

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
