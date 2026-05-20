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

## Bounty #3: Destructive Bash Guard Hook

This repository includes a Claude Code `PreToolUse` hook that blocks dangerous
Bash commands before they run.

### Install

From this repository:

```bash
./install.sh
```

The installer copies the hook to `~/.claude/hooks/destructive-bash-guard.py` and
adds it to `~/.claude/settings.json` for the `Bash` tool.

### What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM ...` statements without a `WHERE` clause

Safe commands continue normally. For example, `npm test`, normal `git push`,
`rm -r build`, and scoped SQL deletes with `WHERE` are allowed.

### Blocked Command Output

When a destructive command is detected, the hook denies the tool call and
returns a clear reason to Claude Code:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command: rm -rf. Reason: recursive forced removal is blocked. Rewrite the command to be scoped, reversible, or ask the user for explicit confirmation."
  }
}
```

### Logging

Blocked attempts are appended to:

```text
~/.claude/hooks/blocked.log
```

Each log entry includes:

- UTC timestamp
- project path
- blocked pattern
- attempted command

### Test

```bash
python3 -m unittest discover -s tests
```
