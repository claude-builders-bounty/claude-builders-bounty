# SKILL.md — Safe Guard Hook for Claude Code

## Description
Pre-execution safety hook that blocks destructive bash commands before they run. Protects against accidental `rm -rf /`, `sudo rm`, `chmod 777`, fork bombs, and other dangerous operations.

## Trigger
Automatically active when `CLAUDE.md` includes the safe-guard configuration. 
No manual trigger needed — Claude Code checks commands against the blocklist before execution.

## Blocked Commands
| Category | Examples Blocked |
|----------|-----------------|
| File destruction | `rm -rf /`, `rm -rf /*`, `rm -rf ~` |
| Permission escalation | `sudo rm`, `sudo su` |
| Permission wide-open | `chmod 777 /`, `chmod -R 777` |
| Fork bombs | `:(){ :|:& };:` |
| Disk wipes | `dd if=... of=/dev/sd*`, `mkfs.*` |
| Git destructive | `git push --force origin main`, `git reset --hard HEAD~` |
| Docker dangerous | `docker system prune -af`, `docker rm -f $(docker ps -aq)` |

## Override
Prepend `I_KNOW_WHAT_IM_DOING` to any command to bypass the block:
```bash
I_KNOW_WHAT_IM_DOING rm -rf ./old-build/
```

## Installation
1. Save `safe-guard.sh` to your project
2. Run `bash safe-guard.sh --install`
3. Restart your shell

## Warnings (not blocked)
- `rm -rf .` (current directory)
- `npm publish`
- `git push --force` (non-main branches)
- `docker rmi`

## Files
- `safe-guard.sh` — Main guard script (install, check, test)
- This `SKILL.md` — Claude Code integration instructions
