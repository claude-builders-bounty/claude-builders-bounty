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

## Destructive-command hook

This repository includes a dependency-free Python `PreToolUse` hook for issue
[#3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3).
It denies `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and
`DELETE FROM` statements that do not contain a `WHERE` clause. Every denial is
written as one JSON line to `~/.claude/hooks/blocked.log` with its UTC
timestamp, command, project path, and reason.

From the repository root, install the files into a target project with two
commands:

```bash
mkdir -p /path/to/project/.claude/hooks
cp -R .claude/. /path/to/project/.claude/
```

The checked-in `.claude/settings.json` registers the hook for Bash tools. On a
machine where the Python executable is named `python3`, change `python` in the
command to `python3`. The hook prints Claude Code's structured
`permissionDecision: "deny"` response and stays silent for safe commands, so
normal permission handling is preserved. The response format follows the
[Claude Code hooks reference](https://code.claude.com/docs/en/hooks).

Run the standard-library tests with:

```bash
python -m unittest discover -s tests -v
```
