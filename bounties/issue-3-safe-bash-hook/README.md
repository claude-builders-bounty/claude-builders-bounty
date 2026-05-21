# Safe Bash Pre-Tool-Use Hook

Claude Code pre-tool-use hook for issue #3. It blocks destructive bash commands before execution and logs every blocked attempt.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp bounties/issue-3-safe-bash-hook/pre-tool-use-safe-bash.py ~/.claude/hooks/pre-tool-use-safe-bash.py && chmod +x ~/.claude/hooks/pre-tool-use-safe-bash.py
printf '%s\n' 'Add ~/.claude/hooks/pre-tool-use-safe-bash.py as a pre-tool-use hook in your Claude Code config.'
```

## What it blocks

- `rm -rf` / `rm -fr`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without `WHERE`

Normal commands continue untouched, including `git push`, `rm -r`, and `DELETE FROM ... WHERE ...`.

## Logging

Blocked attempts append one line to:

```text
~/.claude/hooks/blocked.log
```

Each entry includes UTC timestamp, project path, and command.

## Test

```bash
python3 bounties/issue-3-safe-bash-hook/test_safe_bash_hook.py
python3 -m py_compile bounties/issue-3-safe-bash-hook/pre-tool-use-safe-bash.py bounties/issue-3-safe-bash-hook/test_safe_bash_hook.py
```
