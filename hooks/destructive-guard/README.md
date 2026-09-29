# Destructive-command hook

A dependency-free Python 3 PreToolUse hook for the destructive patterns requested in bounty issue #3. No commands under inspection are executed.

## Install

From the repository root, run:

```sh
cd hooks/destructive-guard
python3 install.py
```

The installer writes `~/.claude/hooks/destructive_guard.py` and merges a Bash-matched hook into `~/.claude/settings.json`. Unrelated settings and hooks are retained. Running the same installer again does not duplicate the hook. Different existing content at the destination is refused. Restart Claude Code or inspect `/hooks` to load the updated configuration.

Blocked calls return a documented `PreToolUse` JSON deny decision and exit 2. Safe calls exit 0 without an allow decision, preserving Claude's normal permission checks. Each denied call appends a JSON record with UTC timestamp, original command, project path, and reason to `~/.claude/hooks/blocked.log`. Logging failure still denies the operation.

## Check

```sh
python3 -m unittest -v test_guard.py
```

Checks run hook and installer subprocesses against a temporary HOME; no real shell deletion, database query, git push, or modification to the user's Claude settings occurs.

## Scope

Recognizes recursive forced `rm` (combined, separate and long flags), common forced `git push` forms, DROP TABLE, TRUNCATE, and DELETE FROM without WHERE for the listed SQL clients or direct SQL text. Handles ordinary command chaining, simple shell wrappers, eval, and simple command substitutions. SQL checks ignore literals and comments and examine statements separately.

This is a pattern guard, not a Bash/SQL parser or security sandbox. It does not resolve aliases, shell variables, generated or encoded code, arbitrary interpreters, external scripts, all nested substitutions, heredocs or SQL dialect grammar. Database client commands may conservatively block nonexecuting arguments containing these patterns. A WHERE clause is required syntactically; its presence does not guarantee a safe deletion. Keep independent permissions, backups, and database access controls.

Log records can contain secrets from attempted commands. The log is created with mode 0600; rotation and deletion are managed by its owner.

Reference: https://code.claude.com/docs/en/hooks

Live Claude Code execution remains unverified; the automated checks exercise the documented JSON protocol through subprocesses.
