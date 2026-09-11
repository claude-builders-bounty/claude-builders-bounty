# Pre-tool destructive bash block hook

## Setup (≤3 steps)
1. Copy `hooks/block-destructive-bash.sh` into your project.
2. `chmod +x hooks/block-destructive-bash.sh`
3. Wire as Claude Code pre-tool-use hook for Bash (settings excerpt):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash hooks/block-destructive-bash.sh"
          }
        ]
      }
    ]
  }
}
```

Exit code **2** blocks the tool call; **0** allows.

## What it blocks (examples)
- `rm -rf /`, `rm -rf /*`
- `dd ... of=/dev/...`, `mkfs.*`
- pipe-to-shell: `curl ... | bash`
- force-push to main/master
- DROP TABLE/DATABASE
- classic fork bomb

## Test
```bash
echo '{"command":"rm -rf /"}' | bash hooks/block-destructive-bash.sh ; echo exit:$?
echo '{"command":"ls -la"}' | bash hooks/block-destructive-bash.sh ; echo exit:$?
```
