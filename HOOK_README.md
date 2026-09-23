# Claude Code destructive-command hook

`hooks/pre_tool_use_guard.py` is a Claude Code `pre-tool-use` hook that blocks high-risk Bash commands before they run.

Install in 2 commands:

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre_tool_use_guard.py ~/.claude/hooks/pre_tool_use_guard.py
chmod +x ~/.claude/hooks/pre_tool_use_guard.py
```

Configure Claude Code to run `~/.claude/hooks/pre_tool_use_guard.py` as a pre-tool-use hook for Bash commands.

The hook blocks:

- `rm -rf`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with a UTC timestamp, the project path, the reason, and the attempted command. Safe commands exit with code `0` and do not write to the log.

Run tests:

```bash
python -m unittest tests/test_pre_tool_use_guard.py
```
