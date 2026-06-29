# Pre-Tool-Use Security Hook for Claude Code

A robust, lightweight, and cross-platform `pre-tool-use` hook to intercept and block destructive bash commands before they are executed.

## Features

- **Safe Guardrails**: Automatically blocks dangerous commands:
  - `rm -rf` (and equivalent force-delete flag permutations)
  - `DROP TABLE` and `DROP DATABASE`
  - `git push --force` (and `-f` flag, while safely allowing `--force-with-lease`)
  - `TRUNCATE`
  - `DELETE FROM` (if it does not contain a `WHERE` clause)
- **Detailed Auditing**: Logs all blocked command attempts to `~/.claude/hooks/blocked.log` with UTC timestamp, attempted command, and directory path.
- **Rich AI Feedback**: Automatically reports the block to Claude Code via structured JSON and console stderr messages, enabling the agent to learn and self-correct.
- **Zero Dependencies**: Built entirely using the Python standard library.

## Quick Installation (1 Command)

Run the installer script to automatically copy the hook to `~/.claude/hooks/pre-tool-use` and register it in `~/.claude/settings.json`:

```bash
curl -fsSL https://raw.githubusercontent.com/aashu91/claude-builders-bounty/main/install.py | python3
```

*(Note: If you have cloned the repository locally, you can also run `python3 install.py` directly from the project root).*

## Verification & Logs

All blocked attempts are logged to `~/.claude/hooks/blocked.log` in the format:

```text
[2026-06-29T06:09:39Z] BLOCKED | project=/path/to/project | cmd=rm -rf /tmp/test | reason=Recursive force delete (rm -rf) is prohibited via Claude Code.
```

To temporarily disable the hook, simply move or rename the file:

```bash
mv ~/.claude/hooks/pre-tool-use ~/.claude/hooks/pre-tool-use.disabled
```
