# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

## Bounty #3: Destructive Command Blocker Hook

This repo includes a Claude Code `PreToolUse` hook that blocks dangerous Bash
commands before execution.

### Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_commands.py ~/.claude/hooks/block_destructive_commands.py && chmod +x ~/.claude/hooks/block_destructive_commands.py
python - <<'PY'
import json
from pathlib import Path

settings = Path.home() / ".claude" / "settings.json"
settings.parent.mkdir(parents=True, exist_ok=True)
data = json.loads(settings.read_text() if settings.exists() else "{}")
pre_tool_use = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
command = str(Path.home() / ".claude" / "hooks" / "block_destructive_commands.py")
hook = {"type": "command", "command": command}

for item in pre_tool_use:
    if item.get("matcher") == "Bash":
        hooks = item.setdefault("hooks", [])
        if hook not in hooks:
            hooks.append(hook)
        break
else:
    pre_tool_use.append({"matcher": "Bash", "hooks": [hook]})

settings.write_text(json.dumps(data, indent=2) + "\n")
PY
```

### What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` with a timestamp,
the attempted command, and the project path.

### Verify

```bash
python -m unittest discover -s tests -p "test*.py" -v
echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"rm -rf ./demo"},"cwd":"."}' | python hooks/block_destructive_commands.py
```

Normal Bash commands produce no output and are allowed to continue.

---

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
