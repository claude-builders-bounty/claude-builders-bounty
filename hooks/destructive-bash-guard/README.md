# Destructive Bash Guard

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

```bash
python3 hooks/destructive-bash-guard/install.py
```

Restart Claude Code or run `/hooks` to confirm the `PreToolUse` matcher for `Bash` is enabled.

## What It Blocks

- Recursive forced deletes such as `rm -rf`, `rm -fr`, `rm -R --force`, and split flags like `rm -r -f`.
- SQL table deletion commands such as `DROP TABLE`.
- SQL truncate commands such as `TRUNCATE` or `TRUNCATE TABLE`.
- Forced git pushes such as `git push --force`, `git push --force-with-lease`, and `git push -f`.
- `DELETE FROM ...` statements that do not include a `WHERE` clause before the statement terminator.

Allowed commands produce no output and exit normally, so routine Bash commands keep working.

## Files

- `destructive_bash_guard.py`: the hook invoked by Claude Code.
- `install.py`: copies the hook to `~/.claude/hooks/` and updates `~/.claude/settings.json`.
- `settings.example.json`: the hook configuration that `install.py` merges.
- `test_destructive_bash_guard.py`: unit tests for dangerous and safe command cases.

## Log Format

Every blocked command is appended to `~/.claude/hooks/blocked.log`:

```text
2026-05-11T09:30:00Z	project=/path/to/project	rule=rm_recursive_force	command=rm -rf build
```

The hook uses Claude Code's structured `PreToolUse` response format so the attempted Bash tool call is denied and Claude sees the exact reason.
