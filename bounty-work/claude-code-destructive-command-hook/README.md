# Claude Code Destructive Command Guard

A small PreToolUse hook that blocks destructive Bash commands before Claude Code executes them.

## Blocks
- rm -rf
- DROP TABLE
- git push --force / git push -f
- TRUNCATE
- DELETE FROM without a WHERE clause

Safe commands and non-Bash tools pass through unchanged.

## Install
    mkdir -p .claude/hooks
    cp destructive-command-guard.py .claude/hooks/
    chmod +x .claude/hooks/destructive-command-guard.py

Add the hook to .claude/settings.json with a PreToolUse matcher for Bash and command:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/destructive-command-guard.py"
          }
        ]
      }
    ]
  }
}
```

Blocked attempts are logged to ~/.claude/hooks/blocked.log. Set CLAUDE_DESTRUCTIVE_GUARD_LOG to override the path.

## Test
    python -m pytest -q
