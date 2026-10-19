# Destructive-command PreToolUse Hook

This repository contains a small, dependency-free Claude Code `PreToolUse`
hook for Bash. It blocks the destructive command patterns requested by the
bounty, records blocked attempts, and leaves normal commands in the standard
permission flow.

## Install

From the repository root:

```bash
mkdir -p ~/.claude/hooks
cp .claude/hooks/block-destructive.py ~/.claude/hooks/
```

The committed `.claude/settings.json` is the shareable project configuration.
It runs the hook for Bash tool calls with:

```text
python3 ${CLAUDE_PROJECT_DIR}/.claude/hooks/block-destructive.py
```

The hook reads the PreToolUse JSON object from stdin and returns Claude Code's
`hookSpecificOutput.permissionDecision` format. A denial is shown to Claude
with the reason; a safe command produces no output, so normal permissions
continue to apply.

Blocked patterns are:

- `rm -rf`
- `DROP TABLE`
- `TRUNCATE` or `TRUNCATE TABLE`
- `DELETE FROM` unless the same statement contains `WHERE`

Each blocked attempt is appended to `~/.claude/hooks/blocked.log` with an ISO
UTC timestamp, attempted command, project path, and blocking reason. Commands
are kept to one log line and truncated to bounded lengths.

## Verify

Run:

```bash
python3 -m unittest discover -s tests -v
```

The tests cover every required blocked pattern, safe commands, and a scoped
`DELETE FROM ... WHERE ...` statement.

## Design notes

The hook is intentionally narrow: it matches Bash only, does not approve any
command, and does not modify command input. Invalid JSON is denied rather
than silently authorized. This is a pattern guard, not a shell parser; users
should retain Claude Code permission review and normal host-level safeguards.
