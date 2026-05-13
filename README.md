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

## Bounty #3: Claude Code destructive command guard

This repository now includes a Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

### What it blocks

- `rm -rf`
- `git push --force` and `git push -f`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

When a command is blocked, the hook exits with code `2`, prints a clear explanation, and appends an audit entry to `~/.claude/hooks/blocked.log`.

### Install in 2 commands

From this repository:

```bash
mkdir -p ~/.claude/hooks && cp claude_destructive_command_hook.py ~/.claude/hooks/destructive-command-guard.py
python3 - <<'PYSETTINGS'
import json
from pathlib import Path
settings = Path.home() / '.claude' / 'settings.json'
settings.parent.mkdir(parents=True, exist_ok=True)
data = json.loads(settings.read_text()) if settings.exists() else {}
hooks = data.setdefault('hooks', {})
pre = hooks.setdefault('PreToolUse', [])
entry = {
    'matcher': 'Bash',
    'hooks': [{'type': 'command', 'command': 'python3 ~/.claude/hooks/destructive-command-guard.py'}],
}
if entry not in pre:
    pre.append(entry)
settings.write_text(json.dumps(data, indent=2) + '\n')
PYSETTINGS
```

### Manual configuration

Add this to `~/.claude/settings.json` or a project `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/destructive-command-guard.py"
          }
        ]
      }
    ]
  }
}
```

### Run tests

```bash
python3 -m unittest tests/test_hook.py -v
```

Expected result:

```text
Ran 7 tests
OK
```

### Behavior notes

- Normal Bash commands pass through silently with exit code `0`.
- Non-Bash tools are ignored.
- `DELETE FROM ... WHERE ...` is allowed.
- SQL matching is intentionally conservative and string-based; it is a safety guard, not a SQL parser.
