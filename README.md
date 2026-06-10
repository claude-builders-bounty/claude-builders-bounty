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

## Destructive Bash Command Hook

This repository includes a Claude Code `PreToolUse` hook for bounty
[#3](../../issues/3). The hook inspects Bash commands before they run and
denies commands that can destroy local files, rewrite Git history, or wipe
database tables.

### Install

From this repository root:

```bash
python3 hooks/install.py
```

The installer copies `hooks/block-destructive-bash.py` to
`~/.claude/hooks/block-destructive-bash.py`, marks it executable, and adds a
`PreToolUse` matcher for the `Bash` tool in `~/.claude/settings.json`.

### What It Blocks

- `rm` commands that combine recursive and force flags, such as `rm -rf build`,
  `rm -fr build`, or `rm --recursive --force build`.
- `git push` with force flags, including `--force`, `-f`, and
  `--force-with-lease`, plus force-push refspecs such as `+main` and
  `git -c push.force=true push`.
- `git reset --hard`, which can discard local work without confirmation.
- Direct writes to block devices through commands such as `dd of=/dev/...`,
  `mkfs.* /dev/...`, and `wipefs /dev/...`.
- Remote script pipes such as `curl ... | bash` or `wget ... | sh`.
- SQL execution contexts containing `DROP TABLE`.
- SQL execution contexts containing `TRUNCATE`.
- SQL execution contexts containing `DELETE FROM` without a following `WHERE`
  clause.

Normal commands such as `npm test`, `git push origin main`, `rm file.log`,
`rm -r build`, `truncate -s 0 notes.txt`, `grep 'DROP TABLE' docs.md`, and
`DELETE FROM sessions WHERE id = 1` are allowed.

### Block Log

Every blocked command appends one JSON line to:

```text
~/.claude/hooks/blocked.log
```

Each entry includes:

- `timestamp`
- `command`
- `project_path`
- `reason`
- `reason_code`

When a command is denied, the hook returns the Claude Code `PreToolUse`
`hookSpecificOutput.permissionDecision` value `deny` with a clear
`permissionDecisionReason` explaining the block to Claude.

### Test

```bash
python3 -m unittest discover -s tests
```

The tests cover the destructive patterns, allowed commands, Claude Code hook
JSON output, and audit log creation.

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
