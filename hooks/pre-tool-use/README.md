# Pre-Tool-Use Hook — Danger Blocker

Blocks dangerous bash commands (rm -rf /, git push --force, DROP TABLE, etc.) in Claude Code.

**Install (2 commands):**
```bash
mkdir -p ~/.claude/hooks/
cp hooks/pre-tool-use/pre-tool-use.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use.py
```

## Blocked Patterns
- `rm -rf /` and recursive force deletes
- `git push --force`, `git reset --hard`
- `DROP TABLE`, `TRUNCATE`, `DELETE`/`UPDATE` without WHERE
- `shutdown`, `reboot`, `dd`, `mkfs`
- `sudo rm -rf`, package managers uninstall

## Testing
```bash
# Should block
echo '{"tool":{"name":"Bash","input":{"command":"rm -rf /"}}}' | python3 hooks/pre-tool-use/pre-tool-use.py
# Should allow
echo '{"tool":{"name":"Bash","input":{"command":"ls -la"}}}' | python3 hooks/pre-tool-use/pre-tool-use.py
```
