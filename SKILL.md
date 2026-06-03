# Block Destructive Commands Hook

Pre-tool-use hook that intercepts bash commands before execution.

## Installation
1. Copy `block-destructive-commands.sh` to project root
2. `chmod +x block-destructive-commands.sh`
3. Configure as pre-tool hook in Claude Code

## Usage
```bash
./block-destructive-commands.sh "rm -rf /"
# {"blocked": true, "reason": "...", "command": "rm -rf /"}
```

## Blocked Patterns
- rm -rf /, rm -rf ~, rm -rf .
- mkfs.* (filesystem formatting)
- dd if=/dev/zero, dd if=/dev/null
- Direct writes to /dev/sd*
- Fork bombs
- chmod -R 777 /
- Network attack tools
- Credential exposure (/etc/shadow, SSH keys)
- SQL destructive operations
