# Destructive command PreToolUse guard

This directory implements bounty #3: a Claude Code `PreToolUse` hook that stops
destructive Bash commands before they execute and records every block.

## Install

From this repository checkout, installation is one command:

```bash
python3 .claude/hooks/install-quarry-guard.py
```

The installer copies `quarry-guard.py` to `~/.claude/hooks/` and adds one
`PreToolUse` entry to `~/.claude/settings.json` without replacing existing hooks.

To install the hook file manually instead:

```bash
mkdir -p ~/.claude/hooks && cp .claude/hooks/quarry-guard.py ~/.claude/hooks/quarry-guard.py && chmod +x ~/.claude/hooks/quarry-guard.py
```

Then register `python3 ~/.claude/hooks/quarry-guard.py` under a Bash
`PreToolUse` matcher in `~/.claude/settings.json`.

## Required protections

The guard denies:

- `rm -rf`, `rm -fr`, split `rm -r -f`, and long-form recursive+force flags
- `git push --force` and `git push -f` while leaving `--force-with-lease` alone
- SQL `DROP TABLE`
- SQL `TRUNCATE`
- SQL `DELETE FROM` without a later `WHERE` clause

It recognizes common SQL clients before applying SQL rules, so ordinary commands
that merely mention SQL words are not blocked. Shell wrappers such as `sudo`
and `env`, command chains, and `sh -c`/ `bash -c` payloads are inspected.

## Block response and log

A denied command returns the Claude Code hook decision:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked ..."
  }
}
```

Every denied attempt appends one JSON line to
`~/.claude/hooks/blocked.log` containing:

- UTC timestamp
- attempted command
- project path from the hook payload
- block reason

Unmatched Bash commands and non-Bash tools exit normally without output.
