# Pre-tool-use Hook: Block Dangerous Bash Commands

A Claude Code `pre-tool-use` hook that intercepts and prevents execution of dangerous bash commands before they can cause harm.

## Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks
cp pre_tool_use.py ~/.claude/hooks/pre_tool_use.py
chmod +x ~/.claude/hooks/pre_tool_use.py
```

That's it! The hook is now active.

## What It Does

This hook protects against dangerous commands by blocking patterns that could cause harm:

| Pattern | Blocked | Safe Alternative |
|---------|---------|-------------------|
| `rm -rf` | ❌ Recursive force delete | ✅ `rm -r` or `rm file.txt` |
| `DROP TABLE` | ❌ SQL table destruction | ✅ `DROP TABLE IF EXISTS` |
| `TRUNCATE` | ❌ SQL data truncation | (No safe alternative - use caution) |
| `DELETE FROM` (no WHERE) | ❌ Delete all rows | ✅ `DELETE FROM users WHERE id = 1` |
| `git push --force` | ❌ Force overwrite remote | ✅ `git push origin main` |

## How It Works

1. **Reads** - Claude Code sends each bash command to the hook as JSON
2. **Checks** - Hook validates command against dangerous patterns
3. **Decides** - Returns `allow` (safe) or `deny` (dangerous)
4. **Logs** - Blocked attempts are recorded to `~/.claude/hooks/blocked.log`

### Blocked Command Example

If you try to run `rm -rf /tmp/data`:

```
Claude Code → Hook → "Denied: Dangerous pattern: rm_recursive_force"
Your terminal → Command NOT executed (prevented)
Log file → Entry added to ~/.claude/hooks/blocked.log
```

### Safe Command Example

If you run `rm file.txt`:

```
Claude Code → Hook → "Allowed"
Your terminal → Command executes normally ✅
Log file → No entry (command is safe)
```

## Log Format

All blocked attempts are logged to `~/.claude/hooks/blocked.log` as JSON Lines:

```json
{"timestamp": "2026-06-30T10:00:00Z", "command": "rm -rf /tmp", "project": "/home/user/my-project", "reason": "Dangerous pattern: rm_recursive_force"}
{"timestamp": "2026-06-30T10:01:00Z", "command": "DROP TABLE users", "project": "/home/user/my-project", "reason": "Dangerous pattern: drop_table"}
```

View your blocked attempts:

```bash
cat ~/.claude/hooks/blocked.log | jq .
```

## Command Examples

### Blocked ❌

```bash
rm -rf /                 # Recursive force delete root
rm -fr build             # Recursive force delete (reverse order)
DROP TABLE users         # SQL table destruction
TRUNCATE sessions        # SQL truncate
DELETE FROM users        # Delete all rows (no WHERE)
git push --force         # Force push to remote
git push -f origin main  # Force push (short form)
```

### Allowed ✅

```bash
rm file.txt              # Delete specific file
rm -r directory          # Recursive delete (without force)
git push origin main     # Normal push
git push                 # Push to default remote
DELETE FROM users WHERE id = 1  # Delete specific row
echo "Hello"             # Normal command
npm test                 # Run tests
python script.py         # Run script
```

## Configuration

The hook is automatically active after installation. No additional configuration needed.

If you want to disable it temporarily:

```bash
mv ~/.claude/hooks/pre_tool_use.py ~/.claude/hooks/pre_tool_use.py.disabled
```

Re-enable:

```bash
mv ~/.claude/hooks/pre_tool_use.py.disabled ~/.claude/hooks/pre_tool_use.py
```

## Testing

To test the hook locally:

```bash
# Test blocking rm -rf
echo '{"tool_name": "bash", "tool_input": {"command": "rm -rf /tmp"}, "project_path": "/home/test"}' | python3 pre_tool_use.py

# Output: {"permissionDecision": "deny", "reason": "Blocked dangerous command: rm_recursive_force"}

# Test allowing rm file.txt
echo '{"tool_name": "bash", "tool_input": {"command": "rm file.txt"}, "project_path": "/home/test"}' | python3 pre_tool_use.py

# Output: {"permissionDecision": "allow"}
```

## How Claude Code Hooks Work

Claude Code pre-tool-use hooks:
1. Receive tool requests as JSON on stdin
2. Analyze the command
3. Return a JSON decision to allow or deny
4. Claude Code respects the decision

This hook is safe - it only **blocks** dangerous commands, never executes or modifies anything.

## Troubleshooting

**Hook not working?**
- Verify it's in the correct location: `~/.claude/hooks/pre_tool_use.py`
- Verify it's executable: `chmod +x ~/.claude/hooks/pre_tool_use.py`
- Restart Claude Code after installation
- Check logs: `cat ~/.claude/hooks/blocked.log`

**Want to see what's blocked?**
```bash
cat ~/.claude/hooks/blocked.log | jq -r '.timestamp, .command' | paste -d " " - -
```

**Need to allow a command?**
The hook only blocks specific dangerous patterns. Most commands pass through safely. If a safe command is blocked, it's likely a false positive - please report it.

## Safety First

This hook is designed to be helpful, not annoying:
- Only blocks genuinely dangerous patterns
- Allows safe variants (e.g., `rm file.txt` is allowed)
- Logs all blocks for review
- Never interferes with normal, safe operations

Stay safe! 🔒