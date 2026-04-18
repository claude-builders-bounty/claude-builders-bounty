# Claude Code Destructive Commands Hook

A `pre-tool-use` hook designed to intercept and prevent Claude Code from executing potentially dangerous database or system bash commands before they can run. This hook automatically safeguards your root project space by blocking predefined hazardous statements while leaving normal system commands fully functional.

## Features Let’s Look At The Blocked Patterns
- **System**: Prevents all structural destruction variants (e.g. `rm -rf`, `rm -fr`)
- **Git**: Blocks force-overwriting repositories (`git push --force`, `git push -f`)
- **SQL & Databases**: Blocks truncations, table drops, and missing-where deletions (`DROP TABLE`, `TRUNCATE`, `DELETE FROM` without `WHERE`).

All intercepted and blocked attempts are comprehensively logged to `~/.claude/hooks/blocked.log` inclusive of:
- Standardized ISO timestamp.
- Exact command payload sent by Claude Code.
- Current Working Directory (Project Scope).
- Block trigger mechanism logic.

## Easy Installation (2 Commands)

You can install this hook into your Claude Code workspace globally in just two terminal commands:

```bash
mkdir -p ~/.claude/hooks && curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/destructive-command-hook/block_destructive.py -o ~/.claude/hooks/block_destructive.py && chmod +x ~/.claude/hooks/block_destructive.py
```

Then, configure the hook in your global `~/.claude/settings.json` mapping. (If using standard Bash configuration, mapping `"PreToolUse"` to the execution environment block will enable it globally!)
