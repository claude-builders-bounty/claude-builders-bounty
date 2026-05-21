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

## Bash Safety Hook (Issue #3) 🛡️

A Pre-Tool-Use hook for Claude Code to intercept and block destructive commands before they are executed.

### Features
- Intercepts and blocks hazardous operations:
  - `rm -rf` (including all variants/order of recursive and force flags, e.g. `rm -r -f`, `rm -fr`, `rm --recursive --force`)
  - `git push --force` (including `--force-with-lease` and short flag `-f` variants)
  - SQL `DROP TABLE`
  - SQL `TRUNCATE`
  - SQL `DELETE FROM` without a `WHERE` clause (evaluates multiple statements correctly)
- Automatically logs all blocked attempts to `~/.claude/hooks/blocked.log` with timestamps and full command details.
- Returns exit status `2` to halt execution safely and reports the block reason on `stderr`.

### Installation
Run the self-contained installer to copy the hook and register it in `~/.claude/settings.json`:
```bash
python3 install_hook.py
```

### Verification & Testing
To run the automated test suite confirming correct behavior across safe and destructive commands:
```bash
python3 test_hook.py
```

---

## Community

- 🐦 X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- 📧 Contact: claudebounty@gmail.com

---

*Started by the Claude builder community · March 2026 · MIT License*

