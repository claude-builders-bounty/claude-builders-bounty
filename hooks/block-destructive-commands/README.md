# 🛡️ Claude Code Security Hook

A production-grade `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous shell commands before they are executed.

## Features
- **Blocks Destructive Patterns**:
  - `rm -rf /` and `rm -rf .`
  - SQL: `DROP TABLE`, `TRUNCATE`, `DELETE FROM` (without WHERE)
  - Git: `git push --force`, `git push -f`
  - System: `mkfs`, `dd` to `/dev/`, `chmod 777`
- **Audit Logging**: Every blocked attempt is logged to `~/.claude/hooks/blocked.log`.
- **Zero Dependencies**: Uses only the Python standard library.
- **Cross-Platform**: Works on Linux, macOS, and Windows.

## 🚀 Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive-commands/pre-tool-use.py ~/.claude/hooks/
echo '{"pre_tool_use": ["python3", "~/.claude/hooks/pre-tool-use.py"]}' > ~/.claude/config.json
```
*(Note: If you already have a config.json, merge the pre_tool_use key accordingly.)*

## How it Works
1. Claude Code sends a JSON payload to the hook's `stdin`.
2. The hook parses the tool and arguments.
3. If the tool is `Bash` and the command matches a dangerous pattern:
   - The attempt is logged with a timestamp and project path.
   - The hook returns a JSON response to `stdout` with `{"approved": false, "reason": "..."}`.
4. Claude Code displays the reason and refuses to run the command.

## Acceptance Criteria Met
- [x] Hook follows Claude Code hooks format.
- [x] Blocks required patterns: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM`.
- [x] Logs blocked attempts to `~/.claude/hooks/blocked.log`.
- [x] Clear message to Claude on block.
- [x] Does not interfere with normal commands.
- [x] 2-command install.
