## Proposed Changes

Adds a Python Claude Code `PreToolUse` hook that inspects Bash commands before execution and blocks destructive patterns required by the bounty:

- `rm -rf` / `rm -fr`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force`, `--force-with-lease`, and `-f`
- `DELETE FROM` without a `WHERE` clause

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, attempted command, project path, and matched pattern. Safe commands and non-Bash tools pass through unchanged.

/claim #3

## Proof

```bash
python3 -m unittest discover -s tests
.....
----------------------------------------------------------------------
Ran 5 tests in 0.001s

OK
```

Manual block example:

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf build","cwd":"/tmp/project"}}' | python3 hooks/pre-tool-use/destructive_command_guard.py
```

Result: exits with code `2`, prints a clear block reason, and appends a JSON line to `~/.claude/hooks/blocked.log`.

## Checklist

- [x] Hook follows Claude Code hook input style and is installable under `~/.claude/hooks/`
- [x] Blocks all required destructive command patterns
- [x] Logs timestamp, attempted command, and project path
- [x] Displays a clear message explaining the block
- [x] Allows normal Bash commands and ignores non-Bash tools
- [x] README installation is two commands or fewer
