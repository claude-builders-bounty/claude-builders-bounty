# Destructive Bash Guard

Claude Code `pre-tool-use` hook that blocks common destructive Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
cp hooks/pre-tool-use/block-dangerous-bash.py ~/.claude/hooks/pre-tool-use/block-dangerous-bash.py
chmod +x ~/.claude/hooks/pre-tool-use/block-dangerous-bash.py
```

Add it to your Claude Code hooks config as a `pre-tool-use` hook for Bash.

## What it blocks

- `rm -rf` against broad paths such as `/`, `~`, `$HOME`, `.`, `..`
- `sudo rm -rf ...`
- disk formatting via `mkfs`
- raw disk overwrites via `dd of=/dev/...` or shell redirect to `/dev/...`
- broad recursive `chmod 777` / `chown`
- shutdown/reboot commands

## Behavior

The hook reads Claude Code hook JSON from stdin. Non-Bash tools pass through. Safe Bash commands exit `0`. Dangerous commands exit non-zero and print the reason to stderr.
