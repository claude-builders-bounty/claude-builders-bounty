# Claude Code Pre-Tool-Use Guard 🛡️

A lightweight, zero-dependency pre-tool-use hook that intercepts and blocks dangerous commands before execution in Claude Code.

## Features

- **Recursive Deletion Prevention**: Blocks `rm -rf`, `rm -fr`, `rm -r -f`, and `--recursive --force` variants.
- **Git History Protection**: Intercepts `git push --force`, `-f`, and `--force-with-lease`.
- **SQL Safeguards**: Blocks `DROP TABLE`, `TRUNCATE [TABLE]`, and unconstrained `DELETE FROM` statements missing a `WHERE` clause.
- **Selective & Accurate**: Does not block safe commands (e.g. `rm file.txt`, `git push`, `DELETE FROM table WHERE id = 1`).
- **Audit Trail**: Logs all blocked commands to `~/.claude/hooks/blocked.log` with UTC timestamp, attempted command, and working directory.

## Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks
cp guard.py ~/.claude/hooks/guard.py && chmod +x ~/.claude/hooks/guard.py
```

To configure Claude Code to run this hook before Bash executions, ensure your Claude Code settings reference `~/.claude/hooks/guard.py` as a pre-tool-use hook.

## Verification

Run the test suite (requires Python 3.10+):

```bash
python -m unittest hooks/destructive-command-guard/test_guard.py
```
