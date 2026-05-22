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

## Destructive Bash Guard Hook

This repository includes a Claude Code `PreToolUse` hook for bounty
[#3](../../issues/3). It blocks dangerous Bash commands before they run and
logs every blocked attempt to `~/.claude/hooks/blocked.log`.

### Install

```bash
python3 hooks/install_block_destructive_hook.py
```

### What It Blocks

- `rm -rf` style recursive force deletion
- `DROP TABLE`
- `TRUNCATE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `DELETE FROM ...` when the statement has no `WHERE` clause

### Hook Configuration

The installer copies `hooks/block_destructive_bash.py` into
`~/.claude/hooks/` and adds this Claude Code hook entry to
`~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

The hook exits normally for safe commands so it does not interfere with the
standard Claude Code permission flow.

### Test

```bash
python3 -m unittest discover -s tests
```

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
