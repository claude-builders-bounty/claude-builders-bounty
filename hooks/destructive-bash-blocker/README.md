# Destructive Command Blocker Hook for Claude Code

A robust `pre-tool-use` security hook for Claude Code that intercepts and blocks dangerous bash commands before they run, preventing accidental data loss or destructive operations.

## Features

Blocks the following destructive patterns case-insensitively with regex word-boundary checks to prevent false positives:
- `rm -rf` (recursive force removals)
- `DROP TABLE` (SQL database drops)
- `git push --force` and `git push -f` (force-pushing git branches)
- `TRUNCATE` (SQL truncate table commands)
- `DELETE FROM` (SQL deletes missing a `WHERE` clause)

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with a timestamp, attempted command, and directory path.

---

## Installation

Install in a single command:

```bash
chmod +x install.sh && ./install.sh
```

---

## Verification

To run the automated test suite:

```bash
python3 test_hook.py
```

### Manual Verification
You can manually test command interception using `echo`:

```bash
# Verify safe command is allowed (exits 0 and prints original input)
echo '{"tool_name": "Bash", "tool_input": {"command": "ls -la"}}' | ~/.claude/hooks/pre-tool-use

# Verify destructive command is blocked (exits 2 and prints error details)
echo '{"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}' | ~/.claude/hooks/pre-tool-use
```
