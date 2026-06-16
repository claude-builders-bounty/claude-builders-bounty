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

## Bounty #3: Destructive Bash Command Hook

This repository includes a Claude Code `PreToolUse` hook that inspects Bash
commands before execution and blocks destructive patterns:

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Blocked attempts exit with code `2`, print a clear reason to stderr for Claude,
and append a JSON line to `~/.claude/hooks/blocked.log` with the timestamp,
attempted command, and project path.

### Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre_tool_use_safety.py ~/.claude/hooks/pre_tool_use_safety.py && chmod +x ~/.claude/hooks/pre_tool_use_safety.py
python3 -c 'import json,pathlib;p=pathlib.Path.home()/".claude/settings.json";p.parent.mkdir(parents=True,exist_ok=True);data=json.loads(p.read_text() if p.exists() else "{}");entry={"matcher":"Bash","hooks":[{"type":"command","command":"python3 ~/.claude/hooks/pre_tool_use_safety.py"}]};items=data.setdefault("hooks",{}).setdefault("PreToolUse",[]);items.append(entry) if entry not in items else None;p.write_text(json.dumps(data,indent=2)+"\n")'
```

### Test

```bash
python3 -m unittest tests.test_pre_tool_use_safety -v
```

The hook uses only Python standard-library modules.

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
