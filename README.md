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

## Bounty #3: Destructive Command Hook

This repository includes a Claude Code `PreToolUse` hook that blocks destructive
Bash and SQL commands before they run.

### What It Blocks

- `rm -rf` and equivalent combined recursive/force flags such as `rm -fr`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Normal commands such as `git push origin main`, `rm file.txt`,
`python -m pytest`, and `DELETE FROM users WHERE id = 1` are allowed.

### Install

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git && cd claude-builders-bounty
./hooks/install.sh
```

The installer copies the hook to `~/.claude/hooks/block_destructive_commands.py`
and adds a `PreToolUse` entry for the Bash tool in `~/.claude/settings.json`.

### Behavior

When the hook blocks a command, it exits with code `2`, writes a clear message to
stderr for Claude Code, and appends a JSON log line to:

```text
~/.claude/hooks/blocked.log
```

Each log entry includes:

- UTC timestamp
- attempted command
- matched blocking rule
- project path

### Test

```bash
python tests/test_block_destructive_commands.py
```

The hook and tests use only the Python 3 standard library.

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
