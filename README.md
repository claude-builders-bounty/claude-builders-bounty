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
3. Submit a PR — payment is automatic on merge

## Active Bounties

| # | Task | Amount | Status |
|---|------|--------|--------|
| [#1](../../issues/1) | SKILL: Generate a CHANGELOG from git history | $50 | 🟢 Open |
| [#2](../../issues/2) | TEMPLATE: CLAUDE.md for a Next.js + SQLite project | $75 | 🟢 Open |
| [#3](../../issues/3) | HOOK: Block destructive bash commands in Claude Code | $100 | 🟢 Open |
| [#4](../../issues/4) | AGENT: PR reviewer with structured Markdown output | $150 | 🟢 Open |
| [#5](../../issues/5) | WORKFLOW: n8n + Claude API — automated weekly dev summary | $200 | 🟢 Open |

---

## Destructive Bash Hook

A lightweight Claude Code `PreToolUse` hook that blocks destructive Bash commands before execution.

### Installation

Run:

~~~
./install.sh
~~~

Requires `jq`.

The installer registers the hook for Claude Code's Bash tool, preserves unrelated hooks, removes duplicate copies of this hook, and sets a 10-second hook timeout.

### Blocked commands

- `rm` with both recursive and force flags, including `rm -rf`, `rm -fr`, `rm -r -f`, and long-form flags
- `git push --force` / `git push -f`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` without `WHERE`

`git push --force-with-lease` and ordinary non-destructive Bash commands are allowed.

Blocked attempts are logged to:

~~~
~/.claude/hooks/blocked.log
~~~

Each log entry includes a UTC timestamp, project path, attempted command, and blocking reason.

### Testing

Run:

~~~
bash tests/test_destructive_bash_guard.sh
~~~

The test suite covers destructive variants, chained SQL statements, case-insensitive matching, safe commands, and `--force-with-lease`.

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
