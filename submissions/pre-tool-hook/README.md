# Pre-Tool-Use Hook — Block Destructive Bash Commands

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before they execute.

## Installation

```bash
# Create hooks directory
mkdir -p ~/.claude/hooks

# Install the hook
ln -sf $(pwd)/pre-tool-use.sh ~/.claude/hooks/pre-tool-use
```

Or copy it:
```bash
cp pre-tool-use.sh ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## What It Blocks

### 🚫 Hard Blocked (Prevented automatically)
- `rm -rf /` and variants — filesystem destruction
- `mkfs`, `dd` to devices — filesystem formatting
- Fork bombs — system crash
- `sudo rm -rf / --no-preserve-root`
- Piped shell downloads (`curl | bash`, `wget | bash`)
- `git push --force` (can destroy remote history)
- Shutdown/reboot/halt commands
- Direct device manipulation

### ⚠️ Warning (Asks for confirmation)
- `rm -rf` / `rm -f` — recursive/forced deletion
- SQL `DROP TABLE / DATABASE`, `TRUNCATE`, `ALTER...DROP`
- `git reset --hard`, `git rebase`, `git clean -f`
- `npm publish / unpublish`
- `terraform destroy`
- `kubectl delete`
- `docker system prune`
- AWS delete commands

## How It Works

Claude Code calls `pre-tool-use` hooks before executing bash commands. This hook:
1. Reads the command from stdin
2. Checks against dangerous and warning pattern lists
3. Returns `{"blocked": true/false}` with a reason

## Customization

Edit the `DANGEROUS_PATTERNS` and `WARNING_PATTERNS` arrays in the script to add or remove patterns.

## Testing

```bash
# Test blocking
echo "rm -rf /" | bash pre-tool-use.sh

# Test allowing
echo "ls -la" | bash pre-tool-use.sh
```

## Requirements
- Claude Code with hooks support
- Bash 4+
- `grep` with `-E` support
