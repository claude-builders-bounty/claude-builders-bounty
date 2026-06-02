# Destructive Bash Guard

Claude Code `PreToolUse` hook for bounty #3. It intercepts Bash tool calls and denies destructive shell or SQL commands before they execute.

## Install

Run this from the repository root:

```bash
python3 hooks/destructive-bash-guard/install.py
```

The installer copies `block_destructive_bash.py` into `~/.claude/hooks/` and adds a `PreToolUse` Bash matcher to `~/.claude/settings.json` using the copied hook's absolute path. `settings.example.json` shows the shape for manual installs.

## What It Blocks

- Recursive forced `rm`, including `rm -rf`, `rm -fr`, `rm --recursive --force`, and mixed short/long flag variants.
- `DROP TABLE`.
- SQL `TRUNCATE TABLE ...` statements.
- `git push --force`, `git push -f`, and `git push --force-with-lease`.
- `DELETE FROM ...` statements that do not include a `WHERE` clause before the statement terminator.

Normal Bash commands exit silently with status `0` and no hook output.

## Blocked Attempt Log

Every blocked command is appended to:

```text
~/.claude/hooks/blocked.log
```

Each JSONL entry includes `timestamp`, `attempted_command`, `project_path`, and `reason`.

The log is created with user-only permissions on POSIX systems (`0600`). Existing POSIX log files are forced back to `0600`, and symlinked log paths are rejected where the platform exposes the needed safeguards. The hook also redacts common inline secrets such as bearer tokens, `API_KEY=...`, `password=...`, and credentials embedded in URLs before writing the command.

## Manual Checks

```bash
printf '{"tool_input":{"command":"rm -rf build"},"cwd":"/tmp/demo"}' | python3 hooks/destructive-bash-guard/block_destructive_bash.py
printf '{"tool_input":{"command":"git status"},"cwd":"/tmp/demo"}' | python3 hooks/destructive-bash-guard/block_destructive_bash.py
```

The first command prints a `permissionDecision: deny` response. The second command prints nothing and allows execution.
