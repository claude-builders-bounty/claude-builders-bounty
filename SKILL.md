# Pre-tool-use Destructive Command Blocker

## Description
A Claude Code pre-tool-use hook that blocks destructive bash commands from being executed.

## Installation
Place `.claude/settings.local.json` in your project root.

## How it works
The hook intercepts the preToolUse lifecycle event and scans every bash command against a curated blocklist of destructive patterns including:
- Recursive forced deletions (rm -rf /)
- Raw disk writes (dd if=, mkfs)
- Fork bombs
- Permission resets (chmod -R 000 /)
- Device-level operations

Safe commands pass through normally.

## Compatibility
- Claude Code CLI
- Works on Linux, macOS, Windows (Git Bash/WSL)
