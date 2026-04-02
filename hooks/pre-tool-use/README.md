# Claude Code Safety Hook

Blocks dangerous bash commands before execution.

## Install

```bash
# Create hooks directory
mkdir -p ~/.claude/hooks/pre-tool-use

# Copy hook
cp hooks/pre-tool-use/safety-hook.py ~/.claude/hooks/pre-tool-use/

# Make executable
chmod +x ~/.claude/hooks/pre-tool-use/safety-hook.py
```

## What it blocks

- `rm -rf` - recursive force delete
- `DROP TABLE` - SQL table deletion
- `TRUNCATE TABLE` - SQL table clearing  
- `DELETE FROM` without WHERE - unsafe delete
- `git push --force` - history overwrite

## How it works

Hook runs before every Bash command. If dangerous pattern detected:
1. Command blocked
2. Reason shown to Claude
3. Logged to `~/.claude/hooks/blocked.log`

## Test it

```bash
# This will be blocked
rm -rf test/

# Check log
cat ~/.claude/hooks/blocked.log
```

## Customize

Edit `DANGEROUS_PATTERNS` in the script to add more patterns.

Format: `(regex_pattern, 'reason message')`
