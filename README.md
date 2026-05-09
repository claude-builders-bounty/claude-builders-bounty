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

## Claude Code Hooks

This repo includes a `PreToolUse` Bash guard hook for bounty [#3](../../issues/3).
It blocks common destructive commands before execution, logs denied attempts to
`~/.claude/hooks/blocked.log`, and leaves normal Bash commands alone.

Install it in 2 commands:

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive_bash.py
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / '.claude' / 'settings.json'
p.parent.mkdir(parents=True, exist_ok=True)
config = json.loads(p.read_text()) if p.exists() else {}
config.setdefault('hooks', {}).setdefault('PreToolUse', []).append({
    'matcher': 'Bash',
    'hooks': [{'type': 'command', 'command': '$HOME/.claude/hooks/block_destructive_bash.py'}]
})
p.write_text(json.dumps(config, indent=2) + '\n')
PY
```

See [hooks/README.md](hooks/README.md) for behavior details and local testing.

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
