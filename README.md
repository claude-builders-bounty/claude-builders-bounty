# Claude Code Pre-Tool-Use Hook: Destructive Command Blocker

A security hook for Claude Code that intercepts and blocks dangerous bash commands before execution.

## 🚀 Installation (2 commands)

```bash
# 1. Download and make executable
curl -sL https://gist.githubusercontent.com/yourusername/.../pre_tool_use_hook.sh -o ~/.claude/hooks/pre_tool_use_hook.sh && chmod +x ~/.claude/hooks/pre_tool_use_hook.sh

# 2. Test it works
echo '{"command": "rm -rf /tmp"}' | ~/.claude/hooks/pre_tool_use_hook.sh
```

## 🧪 Quick Test

```bash
# Should be blocked:
echo '{"command": "rm -rf /tmp"}' | ~/.claude/hooks/pre_tool_use_hook.sh

# Should be allowed:
echo '{"command": "ls -la"}' | ~/.claude/hooks/pre_tool_use_hook.sh
```

## 🔍 Blocked Patterns

| Command Pattern | Severity | Reason |
|----------------|----------|--------|
| `rm -rf` | HIGH | Recursively deletes files without confirmation |
| `DROP TABLE/DATABASE/SCHEMA` | HIGH | Permanently deletes database objects |
| `TRUNCATE` | HIGH | Deletes all data without logging |
| `git push --force` | MEDIUM | Overwrites remote history, may lose commits |
| `DELETE FROM ...` without WHERE | HIGH | Deletes all rows from table |
| `sudo rm -rf /` | CRITICAL | Destroys entire system |
| Fork bomb `:(){ :|: &};:` | CRITICAL | Crashes system via infinite processes |
| `sudo mkfs` | HIGH | Erases all data on partition |
| `dd if=` | MEDIUM | Can overwrite disk contents |

## 📁 Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Command attempted
- Project directory
- Block reason

## ℹ️ Usage

The hook integrates with Claude Code's hook system via stdin JSON. It can also be called with command-line arguments for testing.

### Input Format (stdin)

```json
{
  "command": "rm -rf /tmp/test",
  "cwd": "/path/to/project"
}
```

### Output Format

```
ALLOW: Command allowed: No destructive patterns detected.
```

or

```
DENY: BLOCKED: Recursive delete (rm -rf) detected.
Suggestion: Use 'trash' command or move files to temp directory first
```

## ⚙️ Claude Code Integration

Add to your `~/.claude/hooks.toml`:

```toml
[[hooks]]
name = "destructive-command-blocker"
description = "Blocks destructive bash commands before execution"
matcher = "Command"  
category = "pre-tool-use"
command = ["python3", "~/.claude/hooks/pre_tool_use_hook.sh"]
```

## 🐛 Testing

Run the test suite:

```bash
# Should be blocked:
~/.claude/hooks/pre_tool_use_hook.sh '{"command": "rm -rf /test"}'

# Should be allowed:
~/.claude/hooks/pre_tool_use_hook.sh '{"command": "ls -la"}'
```

## 📄 License

MIT