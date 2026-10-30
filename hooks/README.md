# Claude Code Destructive Bash Command Blocker Hook

A lightweight, zero-dependency `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous commands before execution.

## 🛡️ Blocked Command Patterns
- `rm -rf` / `rm -fr` (recursive force wipes)
- `git push --force` / `git push -f`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with timestamp, project path, and attempted command.

## 🚀 Quickstart (Installation in 2 Commands)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
python3 claude-builders-bounty/hooks/install.py
```

The installer copies the hook to `~/.claude/hooks/` and merges its Bash
`PreToolUse` registration into `~/.claude/settings.json`, preserving other
settings. Run it again safely without adding duplicate registrations.
Before this PR is merged, clone its head branch instead of the default branch.

Claude Code sends `tool_input.command` and `cwd` in its JSON stdin payload.
Blocked commands return exit code **2**, which prevents the tool call; normal
commands return 0. See the [official hook reference](https://code.claude.com/docs/en/hooks).
This pattern-based guard is not a complete shell or SQL parser and cannot
guarantee detection of obfuscated or dynamically constructed commands.

Tests: `python3 -m unittest discover -s hooks -p 'test_*.py'`.
