# Claude Code Security Hook

A `pre-tool-use` hook that intercepts and blocks dangerous bash commands to prevent accidental data loss.

## 🚀 Installation (2 steps)

1. Create the hooks directory:
   ```bash
   mkdir -p ~/.claude/hooks
   ```
2. Copy the script to the hooks directory:
   ```bash
   cp pre-tool-use.sh ~/.claude/hooks/pre-tool-use.sh && chmod +x ~/.claude/hooks/pre-tool-use.sh
   ```

## 🛡️ Protected Patterns
The hook blocks the following destructive patterns:
- `rm -rf`
- `DROP TABLE` / `TRUNCATE TABLE`
- `git push --force` / `git push -f`
- `DELETE FROM` (without a `WHERE` clause)

## 📝 Logging
All blocked attempts are logged to `~/.claude/hooks/blocked.log` with a timestamp, the attempted command, and the project path.

## 🧪 Verification
You can test the hook by running:
```bash
./pre-tool-use.sh "rm -rf /"
# Expected: Exit code 1 and a security warning.
```
