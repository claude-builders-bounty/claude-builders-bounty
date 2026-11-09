# Destructive Bash Pre-Tool-Use Hook

Blocks destructive bash commands before they execute, protecting against accidental data loss.

## Usage

Add to your Claude Code settings (`~/.claude/settings.json` or project `.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "bash destructive-bash-hook.sh \"$TOOL_INPUT_COMMAND\""
      }
    ]
  }
}
```

Or use as a standalone script:

```bash
bash destructive-bash-hook.sh "rm -rf /important/data"
# Output: BLOCKED: destructive command detected - rm -rf with recursive flag on root directory
```

## What It Blocks

| Pattern | Examples Blocked |
|---------|-----------------|
| `rm -rf /` | `rm -rf /`, `rm -rf /*`, `rm -rf /home` |
| `rm -rf ~` | `rm -rf ~/`, `rm -rf ~user` |
| `mkfs` | `mkfs.ext4 /dev/sda1`, `mkfs.xfs /dev/nvme0n1` |
| `dd` writing to disk | `dd if=/dev/zero of=/dev/sda` |
| `:(){ :|:& };:` | Fork bomb |
| `chmod -R 777 /` | `chmod -R 777 /`, `chmod -R 777 /*` |
| `> /dev/sd*` | `> /dev/sda`, `> /dev/nvme0n1` |
| `shutdown -h now` | `shutdown -h now`, `halt`, `poweroff` |
| `rm -rf .git` | `rm -rf .git`, `rm -rf .git/*` |
| `git reset --hard` with force push | `git push --force` on main/master |

## Output

When blocked, prints to stderr and exits with code 1:

```
BLOCKED: destructive command detected - reason: rm -rf on root directory path
Allowed: false
```

When safe, exits silently with code 0.

## Files

| File | Purpose |
|------|---------|
| `destructive-bash-hook.sh` | The hook script |
| `README.md` | Installation and usage guide |
| `test-hooks.sh` | Test suite with 20+ test cases |
