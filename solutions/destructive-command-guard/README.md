# Destructive Bash guard for Claude Code

A minimal Python `PreToolUse` hook that denies common destructive Bash and SQL operations before the Bash tool runs. It blocks forced recursive deletion (`rm -rf` and variants), `DROP TABLE`, `TRUNCATE`, force pushes, and `DELETE FROM` without `WHERE`. Every blocked attempt is recorded with timestamp, command, and project path in `~/.claude/hooks/blocked.log`.

## Install (2 commands)

Run these from the directory containing `hook.py`:

```bash
mkdir -p ~/.claude/hooks && cp hook.py ~/.claude/hooks/destructive_guard.py
cp settings.example.json ~/.claude/hooks/destructive_guard.settings.example.json
```

Merge the `hooks.PreToolUse` entry from `settings.example.json` into your existing `~/.claude/settings.json`; **do not overwrite other Claude Code settings or hooks**. Restart Claude Code. The hook is not installed automatically by this repository.

## Test

```bash
python3 -m unittest -v test_hook.py
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"rm -rf ./test"},"cwd":"/tmp/project"}' | python3 hook.py
```

The second command should exit with code 2, explain the denial on stderr, and append one JSON line to the log. Ordinary commands exit 0 and create no log.

## Limits

This is a lightweight pattern guard, not a full shell or SQL parser. Complex quoting, aliases, command substitution, multiline SQL, encoded payloads, and nested shell invocations may evade checks or produce false positives. Treat it as defense-in-depth, not a sandbox. It only handles Claude Code's `Bash` tool. No production configuration is modified by this package.
