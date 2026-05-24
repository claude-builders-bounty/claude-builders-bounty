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

## Destructive Command Guard Hook

This repository includes a Claude Code `PreToolUse` hook at `.claude/hooks/destructive_command_guard.py`.
It blocks high-risk Bash commands before execution, logs each blocked attempt to
`~/.claude/hooks/blocked.log`, and returns a clear denial message to Claude Code.

Blocked patterns:

- `rm` commands using both recursive and force options, including `rm -rf`, `rm -fr`,
  `rm --recursive --force`, and wrapper forms like `sudo rm -rf` or
  `env VAR=value rm -rf`.
- `DROP TABLE`.
- `TRUNCATE` and `TRUNCATE TABLE`.
- `DELETE FROM` when the statement has no `WHERE` clause.
- `git push --force`, `git push --force-with-lease`, and `git push -f`,
  including common global-option forms like `git -C repo push -f`.

Install in 2 commands:

```bash
mkdir -p ~/.claude/hooks && cp .claude/hooks/destructive_command_guard.py ~/.claude/hooks/destructive_command_guard.py && chmod +x ~/.claude/hooks/destructive_command_guard.py
python3 - <<'PY'
import json
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"
settings_path.parent.mkdir(parents=True, exist_ok=True)
settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
hooks = settings.setdefault("hooks", {})
pre_tool = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": str(Path.home() / ".claude" / "hooks" / "destructive_command_guard.py"),
        }
    ],
}
if entry not in pre_tool:
    pre_tool.append(entry)
settings_path.write_text(json.dumps(settings, indent=2) + "\n")
PY
```

Example blocked event:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/build"},"cwd":"/project"}' \
  | ~/.claude/hooks/destructive_command_guard.py
```

Example allowed event:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"npm test"},"cwd":"/project"}' \
  | ~/.claude/hooks/destructive_command_guard.py
```

Run tests:

```bash
python3 -m unittest tests/test_destructive_command_guard.py
```

---

## Community

- 🐦 X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- 📧 Contact: claudebounty@gmail.com

---

*Started by the Claude builder community · March 2026 · MIT License*
