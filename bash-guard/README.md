# Destructive command hook

A Claude Code pre-tool-use check for Bash. It exits 0 when the command is ordinary. It exits 2, writes a log line, and prints the reason when the command matches a destructive rule. The command itself is never executed by this hook.

## Install

```
mkdir -p ~/.claude/hooks && cp pre_tool_use.py ~/.claude/hooks/pre_tool_use.py
```

Set the Bash PreToolUse hook command to `python3 ~/.claude/hooks/pre_tool_use.py`.

## Rules and log

Blocked: `rm -rf`, `DROP TABLE`, `TRUNCATE`, `git push --force`, and `DELETE FROM` with no WHERE clause. `DELETE FROM users WHERE id = 3` is allowed.

Each blocked attempt appends one line to `~/.claude/hooks/blocked.log`: UTC timestamp, project path, rule name, and the command. Set `HOOK_LOG` to send that line somewhere else during a test.

## Check

```
python3 test_hook.py
```

The test runs eight fixed payloads. Three safe commands must exit 0 and stay out of the log. Five destructive commands must exit 2 and appear in the log. A failing case exits 1.
