# Claude Code Pre-Tool-Use Security Hook

A lightweight, robust security hook for Claude Code that intercepts and blocks dangerous commands before execution.

## Features
- 🛡️ **Zero-False-Positive Protection**: Intercepts `rm -rf`, `git push --force`, `DROP TABLE`, `TRUNCATE`, and unconstrained `DELETE FROM` (missing `WHERE`).
- 📝 **Audit Logging**: Appends all blocked attempts to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and working directory.
- 💬 **Explaining Feedback**: Returns clear reason to Claude explaining why execution was prevented.
- ⚡ **Zero-Interference**: Non-destructive bash commands execute with zero latency impact.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use_guard.py ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## Running Tests

```bash
python3 test_hook.py
```
