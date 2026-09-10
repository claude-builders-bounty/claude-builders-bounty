# Pre-Tool-Use Hook: Block Destructive Bash Commands 🛡️

A `pre-tool-use` hook for **Claude Code** that intercepts and blocks dangerous, destructive bash commands before execution.

---

## Features

- **Blocks Destructive Patterns**:
  - `rm -rf` (recursive force deletion)
  - `DROP TABLE` (database drop table statements)
  - `git push --force` (git force pushes, including `-f` and `--force-with-lease`)
  - `TRUNCATE` (database truncate statements)
  - `DELETE FROM` without a `WHERE` clause (unfiltered deletion)
- **Automatic Logging**: Every blocked command is logged to `~/.claude/hooks/blocked.log` with an ISO timestamp, project path, and attempted command.
- **Claude Error Feedback**: Returns a clear JSON response to Claude explaining why the command was blocked and exits with a non-zero status.
- **Zero Interruption**: Allows all safe, standard bash commands to execute without delay.

---

## Installation

Install the hook in **2 commands**:

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre_tool_use.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre_tool_use.py
```

---

## How It Works

When Claude Code attempts to run a bash tool command, `pre_tool_use.py` intercepts the payload over `stdin` (or CLI arguments).

If a dangerous pattern is detected:
1. Logs the blocked attempt to `~/.claude/hooks/blocked.log`:
   ```text
   [2026-09-10T13:20:00.000000+00:00] Project: /path/to/project | Command: rm -rf / | Reason: rm -rf (recursive force remove)
   ```
2. Outputs a JSON error explaining why it was blocked:
   ```json
   {
     "status": "blocked",
     "error": "Command blocked by pre-tool-use hook: rm -rf (recursive force remove)",
     "reason": "rm -rf (recursive force remove)",
     "command": "rm -rf /",
     "project_path": "/path/to/project",
     "message": "Execution of command 'rm -rf /' was blocked because it matched dangerous pattern: rm -rf (recursive force remove)."
   }
   ```
3. Exits with status `1`.

If no dangerous pattern is detected, it exits with status `0` and allows execution to proceed.

---

## Testing & Verification

Run the included test suite to verify unit and end-to-end functionality:

```bash
python3 -m unittest discover -s tests
```
