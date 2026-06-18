# Claude Code Security Hook

A `pre-tool-use` hook that blocks dangerous bash commands before execution.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp claude-hook.py ~/.claude/hooks/pre-tool-use.py
```

## What it blocks

| Pattern | Example | Risk |
|---------|---------|------|
| `rm -rf` | `rm -rf /tmp/build` | Permanent file deletion |
| `DROP TABLE` | `DROP TABLE users` | Database destruction |
| `DELETE` without WHERE | `DELETE FROM logs` | Delete all rows |
| `git push --force` | `git push --force origin main` | Overwrite remote history |
| `TRUNCATE TABLE` | `TRUNCATE TABLE sessions` | Delete all rows |
| `chmod 777` | `chmod -R 777 .` | Insecure permissions |
| `curl \| bash` | `curl -sSL x.com/install \| bash` | Remote code execution |

## How it works

1. Intercepts bash commands before execution
2. Matches against dangerous patterns
3. Blocks the command if matched
4. Logs the attempt to `~/.claude/hooks/blocked.log`
5. Explains to Claude why it was blocked

## Log format

```
[2026-06-18T15:00:00+00:00] BLOCKED: rm -rf /tmp/build
  Reason: Recursive delete detected (rm -rf). This can permanently delete files.
  Project: /home/user/my-project
```

## Testing

```bash
# This should be blocked
echo "test" | python3 claude-hook.py << 'EOF'
{"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/test"}}
EOF

# This should pass through
echo "test" | python3 claude-hook.py << 'EOF'
{"tool_name": "Bash", "tool_input": {"command": "ls -la"}}
EOF
```

## Customization

Edit `DANGEROUS_PATTERNS` in `claude-hook.py` to add your own patterns.

## License

MIT
