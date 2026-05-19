# Pre-tool-use Hook: Block Destructive Commands

This hook blocks dangerous bash commands in Claude Code.

## Installation

### Option 1: Automatic (recommended)
Run these two commands:

```bash
mkdir -p ~/.claude/hooks/
cp ./hooks/pre-tool-use/pre-tool-use.sh ~/.claude/hooks/
```

### Option 2: Manual
1. Ensure you have a `~/.claude/hooks/` directory:
   ```bash
   mkdir -p ~/.claude/hooks/
   ```
2. Copy the hook script:
   ```bash
   cp ./hooks/pre-tool-use/pre-tool-use.sh ~/.claude/hooks/pre-tool-use.sh
   ```
3. Make it executable (if on Unix-like systems):
   ```bash
   chmod +x ~/.claude/hooks/pre-tool-use.sh
   ```

## How it works
The hook will block the following patterns:
- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Blocked commands are logged to `~/.claude/hooks/blocked.log`.

## Uninstall
Remove the hook script:
```bash
rm ~/.claude/hooks/pre-tool-use.sh
```