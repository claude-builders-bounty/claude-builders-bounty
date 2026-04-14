# SKILL.md — Pre-tool-use Security Hook

## Description
A Python-based pre-tool-use hook for Claude Code that intercepts and blocks destructive bash commands before execution.

## Usage
The hook is invoked automatically by Claude Code when configured. It accepts JSON input via stdin/argv and blocks dangerous commands.

## Hook Registration
Place `pre-tool-use-hook.py` at `~/.claude/hooks/` and configure in your Claude Code settings.

## Patterns Blocked
- `rm -rf /`, `rm -rf $`, `rm -rf .`
- `DROP TABLE`, `TRUNCATE TABLE`
- `git push --force`, `git push -f`
- `DELETE FROM` without WHERE clause

## Logging
Blocked commands → `~/.claude/hooks/blocked.log` with timestamp, command, and project path.
