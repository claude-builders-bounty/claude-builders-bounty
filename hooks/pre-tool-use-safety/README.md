# pre-tool-use-safety-hook

A Claude Code **pre-tool-use** hook that blocks destructive bash commands before they execute. Zero dependencies beyond `bash`, `jq`, and `grep`.

## Blocked Patterns (12+)

| Pattern | Description |
|---------|-------------|
| `rm -rf`, `rm -fr` | Recursive force delete |
| `DROP TABLE` | SQL table deletion |
| `DROP DATABASE` | SQL database deletion |
| `TRUNCATE TABLE` | SQL table truncation |
| `git push --force`, `git push -f` | Force push (rewrites history) |
| `DELETE FROM ... ;` (no WHERE) | Unbounded SQL delete |
| `mkfs.` | Filesystem format |
| `dd if=... of=/dev/` | Direct disk write |
| `> /dev/sd` | Block device overwrite |
| `chmod -R 777 /` | Recursive root permission change |
| `chown -R ... /` | Recursive root ownership change |

## Install (2 commands)

**Step 1** — Copy the hook:

```bash
mkdir -p ~/.claude/hooks && cp hook.sh ~/.claude/hooks/pre-tool-use-safety.sh && chmod +x ~/.claude/hooks/pre-tool-use-safety.sh
```

**Step 2** — Add to `~/.claude/settings.json` (create if it doesn't exist):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/pre-tool-use-safety.sh"
          }
        ]
      }
    ]
  }
}
```

That's it. Every Bash command Claude tries to run will now be checked first.

## How It Works

1. Claude Code calls the hook with JSON on stdin before every Bash tool execution
2. The hook extracts `tool_name` and `tool_input.command` from the JSON
3. Non-Bash tools pass through immediately (exit 0, no output)
4. The command is checked against each dangerous pattern using case-insensitive grep
5. If a match is found:
   - Logs timestamp, pattern, project path, and command to `~/.claude/hooks/blocked.log`
   - Returns `{"hookSpecificOutput": {"permissionDecision": "deny", ...}}` to block execution
6. If no match, exits cleanly and the command proceeds normally

## Log Format

Blocked commands are logged to `~/.claude/hooks/blocked.log`:

```
[2026-03-31T12:00:00Z] BLOCKED | pattern="Recursive force delete (rm -rf)" | project="/home/user/myproject" | command="rm -rf /"
[2026-03-31T12:01:00Z] BLOCKED | pattern="SQL DROP TABLE" | project="/home/user/myproject" | command="psql -c 'DROP TABLE users;'"
```

## Testing

Test a blocked command:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"},"cwd":"/tmp/test"}' | bash hook.sh
# Output: {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny",...}}
```

Test a safe command:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/tmp/test"}' | bash hook.sh
# Output: (empty — command allowed)
```

Test a non-Bash tool:

```bash
echo '{"tool_name":"Read","tool_input":{"file_path":"/etc/hosts"},"cwd":"/tmp"}' | bash hook.sh
# Output: (empty — non-Bash tools pass through)
```

## Requirements

- `bash` (4.0+)
- `jq` (JSON parsing)
- `grep` with `-P` (PCRE support) — standard on most Linux distributions

## License

MIT
