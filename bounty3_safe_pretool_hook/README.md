# Destructive-command PreToolUse Hook

This Claude Code `PreToolUse` hook blocks a small, explicit set of dangerous
Bash commands before they run:

- recursive forced removal (`rm -r`/`-R` with `-f`/`--force`);
- forced `git push`;
- `DROP TABLE` and `TRUNCATE`;
- `DELETE FROM` statements without a `WHERE` clause.

Blocked attempts are written as JSON Lines to `~/.claude/hooks/blocked.log`.
Malformed or unrelated hook events are allowed through so the hook does not
break other Claude Code tools.

## Install

```bash
mkdir -p ~/.claude/hooks && cp block_destructive_commands.py ~/.claude/hooks/
```

Add this command to the `PreToolUse` / `Bash` hook entry in your Claude Code
settings:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/block_destructive_commands.py"}
        ]
      }
    ]
  }
}
```

## Test

```bash
python3 tests/test_hook.py
```

## Optional live Claude Code test

The unit tests above do not invoke a model. To verify the full Claude Code
`PreToolUse` path, run the opt-in integration test against a configured
Anthropic-compatible provider. It is skipped by default because it consumes
provider quota and runs a real Claude Code session.

```bash
export CLAUDE_HOOK_E2E=1
export ANTHROPIC_API_KEY='your-provider-key'
export ANTHROPIC_BASE_URL='https://your-provider.example'
export ANTHROPIC_MODEL='your-tool-capable-model'
python3 tests/test_claude_code_integration.py
```

The test confirms that `printf safe-hook-pass` is allowed and that every
blocked category (`rm -rf`, forced `git push`, `DROP TABLE`, `TRUNCATE`, and a
`DELETE FROM` without `WHERE`) is denied and written to an isolated audit log.
The commands use nonexistent or command-only test targets, and the test does
not modify the user's Claude Code settings.

Verified on 2026-08-10 with Claude Code 2.1.210 through an OpenAI-compatible
New API relay using `DeepSeek/DeepSeek-V4-Flash`.
