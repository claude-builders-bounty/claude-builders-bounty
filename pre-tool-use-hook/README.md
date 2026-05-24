# Claude Code Pre-Tool-Use Hook: Block Destructive Commands

**Bounty #3** — A `pre-tool-use` hook for [Claude Code](https://docs.anthropic.com/en/docs/claude-code/) that intercepts dangerous bash commands before they execute.

## Features

Blocks commands that could cause **data loss** or **system damage**:

| Command | Risk |
|---|---|
| `rm -rf /` | Deletes the entire filesystem |
| `sudo rm -rf /` | Deletes the entire filesystem (elevated) |
| `rm -rf /etc`, `/boot`, `/lib`, etc. | Deletes critical system directories |
| `dd if=/dev/zero` | Overwrites disks (data destruction) |
| `dd of=/dev/sda`, `/dev/nvme0` | Direct block device writes |
| `:(){ :\|:& };:` | Fork bomb (system crash via process exhaustion) |
| `> /dev/sda`, `> /dev/nvme0` | Direct block device writes |
| `chmod -R 000 /` | Removes all permissions (system unbootable) |
| `mv /* /dev/null` | Moves root files to void |
| `shutdown now`, `reboot`, `poweroff`, `init 0/6` | System shutdown / restart |
| `mkfs` on block devices | Formats / erases filesystems |
| `format C:\` | Windows drive erase |
| `curl ... \| bash` | Dangerous remote script execution |
| `chown -R ... /` | Changes ownership of entire filesystem |

### Whitelisted (allowed safe variants)

- `rm -rf ./...` (relative paths, safe)
- `rm -rf /tmp/...` (temporary directory, safe)
- `rm -rf /var/tmp/...` (temporary directory, safe)
- `dd if=/dev/zero of=file.bin` (writing to a file, not a device)
- `dd if=/dev/urandom of=file.bin` (writing to a file, not a device)
- `mkfs ... file.img` (creating filesystem in a regular file)

## Installation

```bash
# Create the hooks directory (if it doesn't exist)
mkdir -p ~/.claude/hooks/

# Copy the hook script
cp block_destructive_commands.py ~/.claude/hooks/pre-tool-use

# Make it executable (Linux/macOS)
chmod +x ~/.claude/hooks/pre-tool-use
```

## Verification

Test that the hook is installed correctly:

```bash
ls -la ~/.claude/hooks/pre-tool-use
```

Expected output:

```
-rwxr-xr-x  ...  pre-tool-use
```

## Testing

### 1. Quick manual test (run the script directly)

```bash
# Test blocked command
echo '{"tool_use_id":"test","tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | python3 ~/.claude/hooks/pre-tool-use

# Expected output:
# {"is_allowed": false, "suggestion": "Blocked: 'rm -rf /' ...", "confidence": 1.0}
```

```bash
# Test allowed command
echo '{"tool_use_id":"test","tool_name":"Bash","tool_input":{"command":"rm -rf ./node_modules"}}' | python3 ~/.claude/hooks/pre-tool-use

# Expected output:
# {"is_allowed": true}
```

```bash
# Test whitelisted /tmp command
echo '{"tool_use_id":"test","tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/*"}}' | python3 ~/.claude/hooks/pre-tool-use

# Expected output:
# {"is_allowed": true}
```

### 2. Test all blocked patterns at once

Clone the repo and run the included test harness:

```bash
python3 test_block_destructive_commands.py
```

Or run individual cases:

```bash
# Fork bomb
echo '{"tool_use_id":"t1","tool_name":"Bash","tool_input":{"command":":(){ :|:& };:"}}' | python3 ~/.claude/hooks/pre-tool-use

# dd of=/dev/sda
echo '{"tool_use_id":"t2","tool_name":"Bash","tool_input":{"command":"dd if=/dev/zero of=/dev/sda bs=4M"}}' | python3 ~/.claude/hooks/pre-tool-use

# sudo rm -rf /
echo '{"tool_use_id":"t3","tool_name":"Bash","tool_input":{"command":"sudo rm -rf /"}}' | python3 ~/.claude/hooks/pre-tool-use
```

### 3. Test with Claude Code (in-session)

Inside a Claude Code session, try:

```
> Run: rm -rf /
```

The hook should intercept and display the block message before the command executes.

## How It Works

Claude Code supports hooks at specific lifecycle points. The `pre-tool-use` hook runs **before** any tool invocation. It receives the tool call as JSON on stdin and must return a JSON decision on stdout:

- `{"is_allowed": true}` — command proceeds
- `{"is_allowed": false, "suggestion": "...", "confidence": 1.0}` — command blocked

This script:

1. Reads the JSON input from stdin
2. Extracts the command from `Bash` or `BashCode` tool invocations
3. Checks against a whitelist (safe patterns like `rm -rf ./` and `rm -rf /tmp/*`)
4. Checks against danger patterns (regex-based)
5. Outputs the decision as JSON to stdout

On any error (malformed JSON, unexpected exception), the hook **fails open** — allowing the command and logging the error to stderr.

## Caveats

- This hook uses **regex pattern matching**, which is heuristic. It may have false positives (blocking a safe command) or false negatives (missing a dangerous variant).
- The hook **fails open** on errors — if the script crashes, commands are allowed through.
- For maximum safety, combine with OS-level protections like `chmod 000 /usr` or a restrictive Docker container.

## Files

| File | Description |
|---|---|
| `block_destructive_commands.py` | Main hook script (copy to `~/.claude/hooks/pre-tool-use`) |
| `README.md` | This file |

## License

MIT — Use freely, modify as needed.
