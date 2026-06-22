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

## Destructive Bash Blocker Hook

This repository includes a Claude Code `PreToolUse` hook for [bounty #3](../../issues/3). It blocks destructive Bash commands before execution and logs every blocked attempt to `~/.claude/hooks/blocked.log` with timestamp, attempted command, project path, and reason.

It blocks:

- `rm` commands that combine recursive and force flags, such as `rm -rf`, `rm -fr`, and `rm -Rf`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause
- `git push --force` / `git push -f`

Install in two commands:

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre_tool_use_block_destructive_bash.py ~/.claude/hooks/block-destructive-bash.py && chmod +x ~/.claude/hooks/block-destructive-bash.py
python3 - <<'PY'
import json, pathlib
settings = pathlib.Path.home() / ".claude" / "settings.json"
data = json.loads(settings.read_text()) if settings.exists() else {}
data.setdefault("hooks", {}).setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": str(pathlib.Path.home() / ".claude" / "hooks" / "block-destructive-bash.py"),
        }
    ],
}
if entry not in data["hooks"]["PreToolUse"]:
    data["hooks"]["PreToolUse"].append(entry)
settings.write_text(json.dumps(data, indent=2) + "\n")
PY
```

Run tests:

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
