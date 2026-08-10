# Claude Code Destructive Command Guard

This is a robust, pure Python standard-library `pre-tool-use` hook for Claude Code that prevents destructive `Bash` commands from executing. 

It intercepts the JSON payload from Claude Code and intelligently blocks commands like `rm -rf`, `DROP TABLE`, `TRUNCATE`, `git push --force`, and `DELETE FROM` (without a `WHERE` clause).

## Installation (2 Commands)

Run the following commands in the directory where you downloaded `destructive_guard.py`:

```bash
mkdir -p ~/.claude/hooks
cp destructive_guard.py ~/.claude/hooks/pre_tool_use.py && chmod +x ~/.claude/hooks/pre_tool_use.py
```

## Features

- **No Dependencies**: Uses only Python 3 standard library (`sys`, `json`, `re`, `os`, `datetime`).
- **Edge-Case Resistant**: Parses quotes and flags correctly to avoid false positives (e.g., `echo "rm -rf"` is allowed) while catching sneaky destructive attempts (e.g., `rm -f -r /`).
- **Audit Logging**: Logs every blocked attempt automatically to `~/.claude/hooks/blocked.log` with a UTC timestamp, current working directory, and the exact blocked command.
- **Claude Feedback**: Returns a properly formatted JSON `deny` response to Claude, giving the AI context on why its command failed so it can correct its behavior.
