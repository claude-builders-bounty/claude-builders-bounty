# Destructive Bash Guard

This is a deterministic Claude Code `PreToolUse` hook. It blocks a narrow set
of high-risk Bash operations before they run:

- `rm -rf` and `rm -fr`
- `git push --force` and `git push --force-with-lease`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` statements that do not contain a `WHERE` clause

The hook only evaluates the `Bash` tool. Read-only commands such as `ls`,
`git status`, `git diff`, `echo`, `grep`, and `cat` are left alone even when
their displayed text contains one of the protected phrases.

## Install

From the repository root:

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
bash hooks/install.sh
```

The installer:

1. Copies the hook to `~/.claude/hooks/block-destructive-bash.py`.
2. Merges a `PreToolUse` entry into `~/.claude/settings.json` without
   overwriting unrelated settings or adding a duplicate entry.

Restart Claude Code after changing hook settings.

## Audit log

Every blocked attempt is appended as one JSON line to:

```text
~/.claude/hooks/blocked.log
```

Each record includes the UTC timestamp, attempted command, project directory,
and the reason it was blocked. Set `CLAUDE_DESTRUCTIVE_HOOK_LOG` to use a
different log path during testing.

## Behavior

When a command is blocked, the hook exits with status `2` and emits a
`PreToolUse` deny decision with a human-readable reason. Claude Code can then
rewrite the command as a narrow, reversible operation.

Malformed hook input is treated as allowed so a broken event cannot prevent
normal Claude Code operation. A failure to write the audit log does not allow
the protected command; the command remains denied.

## Test

```bash
python3 -m unittest discover -s hooks/tests -v
```

The tests cover each protected pattern, safe read-only commands, quoted
strings, chained commands, audit logging, and the emitted deny payload.
