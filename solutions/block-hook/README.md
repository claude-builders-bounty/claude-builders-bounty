# 🔒 Destructive Command Block Hook

A [Claude Code](https://code.claude.com) pre-tool-use hook that blocks destructive bash commands before they execute.

## What it blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /project/data` | Recursive force deletion |
| `DROP TABLE` | `DROP TABLE users;` | Destroys entire tables |
| `git push --force` | `git push --force origin main` | Overwrites remote history |
| `TRUNCATE` | `TRUNCATE TABLE orders;` | Mass irreversible deletion |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` | Accidental mass row deletion |

Every blocked attempt is logged to `blocked.log` with:
- Timestamp
- The exact command attempted
- Which pattern triggered the block
- The project directory path

## Installation (2 commands)

```bash
# 1. Create the hooks directory and copy the script
mkdir -p .claude/hooks && cp block-destructive.py .claude/hooks/

# 2. Add the hook config to your Claude Code settings
# Edit .claude/settings.local.json (project-level, not committed):
# {
#   "hooks": {
#     "hooks": [
#       {
#         "matcher": [{"type": "tool", "name": "Bash"}],
#         "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-destructive.py"
#       }
#     ]
#   }
# }
```

Or for global installation (all projects):

```bash
# Install globally
mkdir -p ~/.claude/hooks && cp block-destructive.py ~/.claude/hooks/
# Edit ~/.claude/settings.json with the config above (use ~/.claude/hooks/ path)
```

## How it works

1. Claude Code calls the hook before every `Bash` tool execution
2. The hook receives the full tool call details as JSON on **stdin**
3. It checks the command against known dangerous patterns
4. If a pattern matches, it **denies** the command and logs the attempt
5. If no pattern matches, it **allows** the command to proceed
6. Claude receives a clear explanation of why the command was blocked

## Testing

Run the included test harness to verify:

```bash
python3 -m pytest test_hook.py -v
```

Or test manually:

```bash
# Should be blocked
echo '{"hookEventName":"PreToolUse","toolCall":{"name":"Bash","input":{"command":"rm -rf /important"}}}' | python3 block-destructive.py

# Should be allowed
echo '{"hookEventName":"PreToolUse","toolCall":{"name":"Bash","input":{"command":"ls -la"}}}' | python3 block-destructive.py
```

## Customization

To add more patterns, edit `DANGEROUS_PATTERNS` in `block-destructive.py`:

```python
DANGEROUS_PATTERNS.append((
    re.compile(r'your-pattern-here'),
    "Pattern Name",
    "Explanation of why this is dangerous."
))
```

## Compatibility

- **Claude Code**: v2.0+ (with pre-tool-use hook support)
- **Python**: 3.8+
- **OS**: Linux, macOS (Windows/WSL untested)
