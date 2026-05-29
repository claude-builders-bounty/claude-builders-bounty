# Destructive Command Guard

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they
run and logs every blocked attempt.

## Install

Run from the repository root:

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive-command-guard/pre_tool_use.py ~/.claude/hooks/destructive-command-guard.py && chmod +x ~/.claude/hooks/destructive-command-guard.py
python hooks/destructive-command-guard/install_settings.py
```

The installer adds this hook to `~/.claude/settings.json` under
`hooks.PreToolUse` with the `Bash` matcher.

## What It Blocks

- `rm -rf` variants, including `rm -fr`, `rm -r -f`, and `sudo rm -rf`.
- `DROP TABLE` in SQL passed to a shell command.
- `TRUNCATE` in SQL passed to a shell command.
- `git push --force`, `git push -f`, and `git push --force-with-lease`.
- `DELETE FROM ...` SQL statements that do not include a `WHERE` clause before
  the statement terminator.

Safe commands such as `npm test`, `git push`, `rm file.txt`, and
`DELETE FROM table WHERE id = 1` are allowed.

## Log File

Blocked attempts are appended to:

```text
~/.claude/hooks/blocked.log
```

Each line is JSON with:

- `timestamp`
- `attempted_command`
- `project_path`
- `rule`
- `reason`

## Manual Test

```bash
echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","cwd":"/tmp/demo","tool_input":{"command":"rm -rf build"}}' | python ~/.claude/hooks/destructive-command-guard.py
```

Expected result: JSON output with `permissionDecision` set to `deny`.

```bash
echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","cwd":"/tmp/demo","tool_input":{"command":"npm test"}}' | python ~/.claude/hooks/destructive-command-guard.py
```

Expected result: no output and exit code `0`.

## Run Tests

```bash
python -m unittest discover -s hooks/destructive-command-guard/tests -p "test_*.py"
```
