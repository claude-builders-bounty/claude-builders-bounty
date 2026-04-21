# Claude Code Security Hook

🛡️ Pre-tool-use hook that intercepts dangerous commands before Claude Code executes them.

## What It Blocks

- **Filesystem destruction**: `rm -rf /`, `rm -rf ~/*`
- **SQL injection**: `DROP TABLE`, `DELETE FROM`, `TRUNCATE`
- **Permission abuse**: `chmod -R 777`, dangerous `chown`
- **Disk destruction**: `dd if=/dev/zero`, `mkfs`
- **Fork bombs**: `:(){:|:&};:`
- **Remote code execution**: `curl | bash`, `wget | sh`
- **Sudo abuse**: `sudo rm -rf /`, etc.

## Installation (2 Steps)

### Step 1: Create hooks directory
```bash
mkdir -p ~/.claude/hooks
```

### Step 2: Install the hook
```bash
# Python version (recommended)
cp pre_tool_use_hook.py ~/.claude/hooks/pre_tool_use.py
chmod +x ~/.claude/hooks/pre_tool_use.py

# OR Bash version
cp pre_tool_use_hook.sh ~/.claude/hooks/pre_tool_use.sh
chmod +x ~/.claude/hooks/pre_tool_use.sh
```

**That's it!** The hook will automatically run before every shell command.

## Usage

Blocked commands are logged to `~/.claude/hooks/blocked.log`:

```
[2026-04-21T14:30:00+08:00] BLOCKED: DANGEROUS_RM: Recursive force delete detected
  Command: rm -rf /tmp/test
```

## Testing

Try running a dangerous command through Claude Code:
```
Claude, run: rm -rf /tmp/test
```

You should see:
```
🚫 BLOCKED: DANGEROUS_RM: Recursive force delete detected
   Command: rm -rf /tmp/test
   Logged to: /home/youruser/.claude/hooks/blocked.log
```

## Customization

Edit the `DANGEROUS_PATTERNS` list in the hook script to add/remove patterns.

## License

MIT - Use freely in your projects.
