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

The `hooks/block_destructive_bash.py` hook protects Claude Code projects by
checking each Bash command before execution. It blocks commands that match the
bounty requirements:

- `rm -rf`
- `DROP TABLE` in direct SQL or database CLI invocations
- `git push --force` and `git push --force-with-lease`
- `TRUNCATE` in direct SQL or database CLI invocations
- `DELETE FROM` statements without a `WHERE` clause in direct SQL or database CLI invocations

Every blocked command is appended to `~/.claude/hooks/blocked.log` as JSON with
the timestamp, attempted command, project path, and matched rule. Normal Bash
commands such as `ls`, `cat README.md`, and `npm test` pass through without
output. Searches such as `grep -R 'DROP TABLE' migrations/` are treated as
normal commands instead of destructive SQL execution. Blocked commands return
Claude Code `PreToolUse` JSON with `permissionDecision: "deny"` and a clear
reason for Claude.

Install in one command from this repository:

```bash
python3 scripts/install_block_destructive_bash_hook.py
```

The installer copies the hook into `~/.claude/hooks/` and adds this Claude Code
settings entry for the Bash tool:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

Optional custom rules can be loaded with `DESTRUCTIVE_BASH_HOOK_CONFIG`:

```json
{
  "allow": [
    {
      "name": "fixture cleanup",
      "pattern": "^rm -rf \\.pytest_cache$"
    }
  ],
  "deny": [
    {
      "name": "remove build output",
      "pattern": "^rm -rf dist$"
    }
  ]
}
```

Allow rules are checked before deny rules, so teams can create narrow exceptions
without turning the blocker off.

Demo transcript:

```text
$ printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf ./dist"},"cwd":"/repo"}' | python3 hooks/block_destructive_bash.py
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "Blocked destructive Bash command before execution.\nReason: recursive forced removal\nProject: /repo\nThe attempted command was logged to ~/.claude/hooks/blocked.log."}}

$ printf '{"tool_name":"Bash","tool_input":{"command":"npm test"},"cwd":"/repo"}' | python3 hooks/block_destructive_bash.py
$ echo $?
0
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
