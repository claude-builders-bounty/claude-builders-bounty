# Destructive Command Guard for Claude Code

This Claude Code `PreToolUse` hook blocks destructive Bash commands before they run and writes every blocked attempt to `~/.claude/hooks/blocked.log`.

## Install

```bash
git clone https://github.com/kabbersokhi-boop/claude-builders-bounty.git
cd claude-builders-bounty && bash hooks/destructive-command-guard/install.sh
```

## What It Blocks

- `rm -rf`, including flag variants like `rm -fr` and `rm -r --force`
- `git push --force`, `git push -f`, `git push --force-with-lease`, and forced refspec pushes
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

The hook follows the Claude Code command hook protocol: it reads the `PreToolUse` JSON payload from `stdin` and returns a structured `permissionDecision: "deny"` response on `stdout` only when a Bash command should be blocked.

It intentionally focuses on the destructive patterns from the bounty instead of trying to be a full shell sandbox. The parser checks separate shell segments, nested `bash -c` calls, and SQL sent through common database clients, while leaving ordinary read-only commands alone.

## Test

```bash
python3 -m unittest tests/test_destructive_command_guard.py
```
