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

## Claude Code destructive Bash guard

This repository includes a dependency-free Python `PreToolUse` hook that blocks dangerous Claude Code Bash tool calls before they run.

### Install

From this repository:

```bash
./install.sh
```

Or in one command from a fresh checkout:

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git && cd claude-builders-bounty && ./install.sh
```

The installer copies `hooks/destructive_bash_guard.py` to `~/.claude/hooks/`, makes it executable, and adds it to `~/.claude/settings.json` as a `PreToolUse` hook for the Bash tool.

### What gets blocked

- `rm` commands that combine recursive and force flags, such as `rm -rf`, `rm -fr`, and `rm --recursive --force`
- `git push` with force flags, including `--force`, `-f`, and `--force-with-lease`
- SQL statements containing `DROP TABLE`
- SQL statements containing `TRUNCATE`
- `DELETE FROM` SQL statements that do not include a `WHERE` clause

Normal commands such as `git status`, `git push origin main`, `rm -r build`, and `DELETE FROM ... WHERE ...` are allowed to continue through Claude Code's normal permission flow.

### Logging

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each CSV row contains the UTC timestamp, project path, block reason, and attempted command.

### How it works

Claude Code sends `PreToolUse` hook input as JSON on stdin. The hook checks only Bash tool calls, tokenizes shell command separators such as `&&`, `;`, and pipes, evaluates each command segment, then returns a Claude Code deny decision when a destructive pattern is found:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command before execution: ..."
  }
}
```

When no destructive pattern is found, the hook exits with code `0` and no output.

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
